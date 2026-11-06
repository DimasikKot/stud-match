import json
import os
import threading
import time
from contextlib import asynccontextmanager

import httpx
import redis
import torch
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

# Очередь задач: бэк кладёт id в Redis, воркер забирает запрос и файлы с бэка
BACKEND_URL = os.getenv("BACKEND_URL", "http://sm-backend:8060/api/v1")
REDIS_HOST = os.getenv("REDIS_HOST", "sm-redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6350"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD") or None
QUEUE_KEY = "llm:queue"
TASK_TTL_SECONDS = 24 * 60 * 60


def _service_token() -> str:
    try:
        tokens = json.loads(os.getenv("TRAIN_JWT_ACCESS_TOKENS") or "[]")
    except json.JSONDecodeError:
        return ""
    return tokens[0] if tokens else ""


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
        target=queue_loop, daemon=True, name="llm-queue"
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
        "queue": bool(queue_thread and queue_thread.is_alive()),
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


class RedisStreamer(TextStreamer):
    """Пишет куски ответа в Redis Stream (для стриминга на фронт) и в логи."""

    def __init__(self, tokenizer, client: redis.Redis, key: str):
        super().__init__(tokenizer, skip_prompt=True, skip_special_tokens=True)
        self.client, self.key, self.parts = client, key, []

    def on_finalized_text(self, text: str, stream_end: bool = False):
        if text:
            self.parts.append(text)
            self.client.xadd(self.key, {"chunk": text})
        super().on_finalized_text(text, stream_end)


def process_task(client: redis.Redis, http: httpx.Client, task_id: str):
    stream_key = f"llm:task:{task_id}:stream"
    try:
        response = http.get(f"/llms/tasks/{task_id}/context")
        response.raise_for_status()
        context = response.json()
        request = GenerateRequest(
            prompt=context["prompt"],
            enable_thinking=context["enable_thinking"],
            max_new_tokens=context["max_new_tokens"],
        )
        streamer = RedisStreamer(llm["tokenizer"], client, stream_key)
        with gpu_lock, torch.inference_mode():
            print(f"\n[llm] task {task_id}", flush=True)
            log_request(request)
            llm["model"].generate(
                **build_inputs(request),
                max_new_tokens=request.max_new_tokens,
                streamer=streamer,
            )
        payload = {"result": "".join(streamer.parts)}
        event = {"event": "done"}
    except Exception as exc:
        detail = (
            exc.response.text if isinstance(exc, httpx.HTTPStatusError) else str(exc)
        )
        print(f"\n[llm] task {task_id} failed: {detail}", flush=True)
        payload = {"error": detail or type(exc).__name__}
        event = {"event": "error", "detail": payload["error"]}

    try:
        http.post(f"/llms/tasks/{task_id}/result", json=payload).raise_for_status()
    except httpx.HTTPError as exc:
        print(
            f"[llm] task {task_id}: не удалось сохранить результат: {exc}", flush=True
        )
    client.xadd(stream_key, event)
    client.expire(stream_key, TASK_TTL_SECONDS)


def queue_loop():
    use_tls = REDIS_PORT == 6150
    client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        decode_responses=True,
        ssl=use_tls,
        ssl_cert_reqs="none" if use_tls else "required",
        health_check_interval=30,
    )
    http = httpx.Client(
        base_url=BACKEND_URL,
        headers={"Authorization": f"Bearer {_service_token()}"},
        timeout=30.0,
    )
    print(
        f"[llm] queue {QUEUE_KEY} @ {REDIS_HOST}:{REDIS_PORT}, backend {BACKEND_URL}",
        flush=True,
    )
    while True:
        try:
            item = client.brpop([QUEUE_KEY], timeout=5)
            if item:
                process_task(client, http, item[1])
        except redis.RedisError as exc:
            print(f"[llm] redis error: {exc}", flush=True)
            time.sleep(5)
        except Exception as exc:
            print(f"[llm] queue error: {exc}", flush=True)


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
