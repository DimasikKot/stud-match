import json
import os
import ssl
import threading
import time
from contextlib import asynccontextmanager

import torch
from kafka import KafkaConsumer, KafkaProducer
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel, Field
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TextIteratorStreamer,
    TextStreamer,
)

MODEL_NAME = os.getenv("LLM_MODEL", "Qwen/Qwen3-4B")
HF_TOKEN = os.getenv("HF_TOKEN") or None
MAX_NEW_TOKENS = int(os.getenv("LLM_MAX_NEW_TOKENS", "2048"))
THINK_END_TOKEN_ID = 151668  # </think>

# Очередь задач через Kafka: бэк кладёт задачу в llm.tasks, воркер отвечает в llm.results
KAFKA_HOST = os.getenv("KAFKA_HOST", "sm-kafka")
KAFKA_PORT = int(os.getenv("KAFKA_PORT", "9092"))
KAFKA_SECURITY_PROTOCOL = os.getenv("KAFKA_SECURITY_PROTOCOL", "").strip().upper()
KAFKA_SASL_MECHANISM = os.getenv("KAFKA_SASL_MECHANISM", "PLAIN")
LLM_KF_USERNAME = os.getenv("LLM_KF_USERNAME", "")
LLM_KF_PASSWORD = os.getenv("LLM_KF_PASSWORD", "")
KAFKA_SSL_CA_FILE = os.getenv("KAFKA_SSL_CA_FILE", "")
KAFKA_SSL_CHECK_HOSTNAME = (
    os.getenv("KAFKA_SSL_CHECK_HOSTNAME", "false").lower() == "true"
)
TASKS_TOPIC = "llm.tasks"
RESULTS_TOPIC = "llm.results"
CONSUMER_GROUP = os.getenv("KAFKA_CONSUMER_GROUP", "sm-llm-worker")
# TLS-порты: 9093 — SSL-листенер, 9193 — внешний SASL_SSL (внутренний 19094 — SASL_PLAINTEXT)
KAFKA_TLS_PORTS = (9093, 9193)
KAFKA_SASL_PROTOCOLS = ("SASL_SSL", "SASL_PLAINTEXT")
KAFKA_SSL_PROTOCOLS = ("SSL", "SASL_SSL")


def _security_protocol() -> str:
    if KAFKA_SECURITY_PROTOCOL:
        return KAFKA_SECURITY_PROTOCOL
    if LLM_KF_USERNAME or LLM_KF_PASSWORD:
        return "SASL_SSL" if KAFKA_PORT in KAFKA_TLS_PORTS else "SASL_PLAINTEXT"
    return "SSL" if KAFKA_PORT in (9093, 9193) else "PLAINTEXT"


def _ssl_context() -> ssl.SSLContext:
    if KAFKA_SSL_CA_FILE:
        context = ssl.create_default_context(cafile=KAFKA_SSL_CA_FILE)
        context.verify_mode = ssl.CERT_REQUIRED
        context.check_hostname = KAFKA_SSL_CHECK_HOSTNAME
        return context

    # Самоподписанный сертификат без CA — поведение как раньше (только для локальной разработки)
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context


def _kafka_kwargs(**extra) -> dict:
    protocol = _security_protocol()
    kwargs = {
        "bootstrap_servers": f"{KAFKA_HOST}:{KAFKA_PORT}",
        "api_version_auto_timeout_ms": 5000,
        "security_protocol": protocol,
    }
    if protocol in KAFKA_SSL_PROTOCOLS:
        kwargs["ssl_context"] = _ssl_context()
    if protocol in KAFKA_SASL_PROTOCOLS:
        if not LLM_KF_USERNAME or not LLM_KF_PASSWORD:
            raise ValueError("LLM_KF_USERNAME/LLM_KF_PASSWORD обязательны для SASL")
        kwargs.update(
            sasl_mechanism=KAFKA_SASL_MECHANISM.upper(),
            sasl_plain_username=LLM_KF_USERNAME,
            sasl_plain_password=LLM_KF_PASSWORD,
        )
    kwargs.update(extra)
    return kwargs


llm: dict = {}
gpu_lock = threading.Lock()


def load_model():
    # 4-bit NF4 (~2.5 GB VRAM); GTX 1650 Ti (Turing) has no bf16, so compute in fp16
    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )
    llm["tokenizer"] = AutoTokenizer.from_pretrained(MODEL_NAME, token=HF_TOKEN)
    llm["model"] = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        token=HF_TOKEN,
        dtype=torch.float16,
        device_map="cuda:0",
        quantization_config=quantization_config,
    )
    print(f"VRAM allocated: {torch.cuda.memory_allocated() / 1024**3:.2f} GB")


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_model()
    llm["queue_thread"] = threading.Thread(
        target=kafka_loop, daemon=True, name="llm-kafka"
    )
    llm["queue_thread"].start()
    yield
    llm.clear()
    torch.cuda.empty_cache()


app = FastAPI(title="sm-llm-worker", lifespan=lifespan)


class Message(BaseModel):
    role: str
    content: str


class GenerateRequest(BaseModel):
    prompt: str | None = None
    messages: list[Message] | None = None
    max_new_tokens: int = Field(default=MAX_NEW_TOKENS, ge=1, le=32768)
    enable_thinking: bool = True


class GenerateResponse(BaseModel):
    thinking: str
    content: str


def build_inputs(request: GenerateRequest):
    tokenizer, model = llm["tokenizer"], llm["model"]
    messages = [m.model_dump() for m in request.messages or []]
    if request.prompt:
        messages.append({"role": "user", "content": request.prompt})
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=request.enable_thinking,
    )
    return tokenizer([text], return_tensors="pt").to(model.device)


def log_request(request: GenerateRequest):
    last = request.prompt or (request.messages[-1].content if request.messages else "")
    print(f"\n[llm] >>> {last}\n[llm] <<< ", end="", flush=True)


@app.get("/health")
def health():
    queue_thread = llm.get("queue_thread")
    return {
        "status": "ok",
        "model": MODEL_NAME,
        "loaded": "model" in llm,
        "consumer": bool(queue_thread and queue_thread.is_alive()),
    }


@app.post("/generate", response_model=GenerateResponse)
def generate(request: GenerateRequest):
    tokenizer, model = llm["tokenizer"], llm["model"]
    model_inputs = build_inputs(request)

    log_streamer = TextStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)

    with gpu_lock, torch.inference_mode():
        log_request(request)
        generated_ids = model.generate(
            **model_inputs,
            max_new_tokens=request.max_new_tokens,
            streamer=log_streamer,
        )
    output_ids = generated_ids[0][len(model_inputs.input_ids[0]) :].tolist()

    try:
        index = len(output_ids) - output_ids[::-1].index(THINK_END_TOKEN_ID)
    except ValueError:
        index = 0

    thinking = tokenizer.decode(output_ids[:index], skip_special_tokens=True)
    content = tokenizer.decode(output_ids[index:], skip_special_tokens=True)
    return GenerateResponse(thinking=thinking.strip("\n"), content=content.strip("\n"))


@app.post("/generate/stream", response_class=StreamingResponse)
def generate_stream(request: GenerateRequest):
    """Plain-text stream of the answer (thinking is wrapped in <think>...</think>)."""
    tokenizer, model = llm["tokenizer"], llm["model"]
    model_inputs = build_inputs(request)
    streamer = TextIteratorStreamer(
        tokenizer, skip_prompt=True, skip_special_tokens=True
    )

    def run():
        with gpu_lock, torch.inference_mode():
            log_request(request)
            model.generate(
                **model_inputs,
                max_new_tokens=request.max_new_tokens,
                streamer=streamer,
            )

    def stream_and_log():
        for chunk in streamer:
            print(chunk, end="", flush=True)
            yield chunk
        print(flush=True)

    threading.Thread(target=run, daemon=True).start()
    return StreamingResponse(stream_and_log(), media_type="text/plain; charset=utf-8")


class CollectStreamer(TextStreamer):
    """Собирает куски ответа для итогового результата."""

    def __init__(self, tokenizer):
        super().__init__(tokenizer, skip_prompt=True, skip_special_tokens=True)
        self.parts: list[str] = []

    def on_finalized_text(self, text: str, stream_end: bool = False):
        if text:
            self.parts.append(text)
        super().on_finalized_text(text, stream_end)


def process_task(producer: KafkaProducer, task: dict):
    task_id = task["task_id"]
    try:
        producer.send(RESULTS_TOPIC, {"task_id": task_id, "status": "running"}).get(
            timeout=10
        )

        request = GenerateRequest(
            prompt=task["prompt"],
            enable_thinking=task.get("enable_thinking", True),
            max_new_tokens=task.get("max_new_tokens") or MAX_NEW_TOKENS,
        )
        streamer = CollectStreamer(llm["tokenizer"])
        with gpu_lock, torch.inference_mode():
            print(f"\n[llm] task {task_id}", flush=True)
            log_request(request)
            llm["model"].generate(
                **build_inputs(request),
                max_new_tokens=request.max_new_tokens,
                streamer=streamer,
            )
        payload = {"task_id": task_id, "result": "".join(streamer.parts)}
    except Exception as exc:
        print(f"\n[llm] task {task_id} failed: {exc}", flush=True)
        payload = {"task_id": task_id, "error": str(exc) or type(exc).__name__}

    try:
        producer.send(RESULTS_TOPIC, payload).get(timeout=10)
    except Exception as exc:
        print(
            f"[llm] task {task_id}: не удалось отправить результат: {exc}", flush=True
        )


def kafka_loop():
    producer = KafkaProducer(
        value_serializer=lambda value: json.dumps(value).encode(),
        **_kafka_kwargs(),
    )
    print(
        f"[llm] kafka {TASKS_TOPIC} -> {RESULTS_TOPIC} @ {KAFKA_HOST}:{KAFKA_PORT}",
        flush=True,
    )
    while True:
        consumer = None
        try:
            consumer = KafkaConsumer(
                TASKS_TOPIC,
                group_id=CONSUMER_GROUP,
                auto_offset_reset="earliest",
                enable_auto_commit=False,
                value_deserializer=lambda raw: json.loads(raw.decode()),
                **_kafka_kwargs(),
            )
            for message in consumer:
                process_task(producer, message.value)
                consumer.commit()
        except Exception as exc:
            print(f"[llm] kafka error: {exc}", flush=True)
            time.sleep(5)
        finally:
            if consumer is not None:
                consumer.close()


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def playground():
    return PLAYGROUND_HTML


PLAYGROUND_HTML = """<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>sm-llm-worker</title>
<style>
  body { font-family: system-ui, sans-serif; max-width: 860px; margin: 2rem auto; padding: 0 1rem; }
  textarea { width: 100%; height: 6rem; font: inherit; }
  pre { white-space: pre-wrap; background: #f4f4f4; padding: 1rem; border-radius: 6px; min-height: 4rem; }
  .row { display: flex; gap: 1rem; align-items: center; margin: .5rem 0; }
</style>
</head>
<body>
<h2>sm-llm-worker &mdash; потоковая генерация</h2>
<textarea id="prompt">Расскажи коротко, что такое большие языковые модели.</textarea>
<div class="row">
  <label><input type="checkbox" id="thinking" checked> thinking</label>
  <label>max_new_tokens <input type="number" id="max" value="1024" min="1" style="width:6rem"></label>
  <button id="send">Отправить</button>
  <a href="/docs">Swagger</a>
</div>
<pre id="out"></pre>
<script>
document.getElementById("send").onclick = async () => {
  const out = document.getElementById("out");
  out.textContent = "";
  const res = await fetch("/generate/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      prompt: document.getElementById("prompt").value,
      enable_thinking: document.getElementById("thinking").checked,
      max_new_tokens: Number(document.getElementById("max").value),
    }),
  });
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    out.textContent += decoder.decode(value, { stream: true });
  }
};
</script>
</body>
</html>
"""
