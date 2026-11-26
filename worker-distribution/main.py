import json
import ssl
import threading
import time
from contextlib import asynccontextmanager

import torch
from app.config import settings
from fastapi import FastAPI
from pydantic import BaseModel, Field
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TextStreamer,
)

from kafka import KafkaConsumer, KafkaProducer

MODEL_NAME: str = "Qwen/Qwen3-4B"
LLM_MAX_NEW_TOKENS: int = 2048


def _security_protocol() -> str:
    if settings.KAFKA_SECURITY_PROTOCOL:
        return settings.KAFKA_SECURITY_PROTOCOL
    if settings.KAFKA_USERNAME or settings.KAFKA_PASSWORD:
        return "SASL_SSL" if settings.KAFKA_PORT in (8092,) else "SASL_PLAINTEXT"
    return "SSL" if settings.KAFKA_PORT in (8092,) else "PLAINTEXT"


def _ssl_context() -> ssl.SSLContext:
    if settings.KAFKA_SSL_CA_FILE:
        context = ssl.create_default_context(cafile=settings.KAFKA_SSL_CA_FILE)
        context.verify_mode = ssl.CERT_REQUIRED
        context.check_hostname = settings.KAFKA_SSL_CHECK_HOSTNAME
        return context

    # Самоподписанный сертификат без CA - поведение как раньше (только для локальной разработки)
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context


def _kafka_kwargs(**extra) -> dict:
    protocol = _security_protocol()
    kwargs = {
        "bootstrap_servers": f"{settings.KAFKA_HOST}:{settings.KAFKA_PORT}",
        "api_version_auto_timeout_ms": 5000,
        "security_protocol": protocol,
    }
    if protocol in ("SSL", "SASL_SSL"):
        kwargs["ssl_context"] = _ssl_context()
    if protocol in ("SASL_SSL", "SASL_PLAINTEXT"):
        if not settings.KAFKA_USERNAME or not settings.KAFKA_PASSWORD:
            raise ValueError("KAFKA_USERNAME/KAFKA_PASSWORD обязательны для SASL")
        kwargs.update(
            sasl_mechanism=settings.KAFKA_SASL_MECHANISM.upper(),
            sasl_plain_username=settings.KAFKA_USERNAME,
            sasl_plain_password=settings.KAFKA_PASSWORD,
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
    llm["tokenizer"] = AutoTokenizer.from_pretrained(
        MODEL_NAME, token=settings.HF_TOKEN
    )
    llm["model"] = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        token=settings.HF_TOKEN,
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
    max_new_tokens: int = Field(default=LLM_MAX_NEW_TOKENS, ge=1, le=32768)
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


class CollectStreamer(TextStreamer):
    """Собирает куски ответа для итогового результата."""

    def __init__(self, tokenizer):
        super().__init__(tokenizer, skip_prompt=True, skip_special_tokens=True)
        self.parts: list[str] = []

    def on_finalized_text(self, text: str, stream_end: bool = False):
        if text:
            self.parts.append(text)
        super().on_finalized_text(text, stream_end)


def process_task(producer: KafkaProducer, task: dict) -> bool:
    task_id = task["task_id"]
    try:
        producer.send(
            settings.KAFKA_RESULTS_TOPIC, {"task_id": task_id, "status": "running"}
        ).get(timeout=10)

        request = GenerateRequest(
            prompt=task["prompt"],
            enable_thinking=task.get("enable_thinking", True),
            max_new_tokens=task.get("max_new_tokens") or LLM_MAX_NEW_TOKENS,
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
        producer.send(settings.KAFKA_RESULTS_TOPIC, payload).get(timeout=10)
        return True
    except Exception as exc:
        print(
            f"[llm] task {task_id}: не удалось отправить результат: {exc}", flush=True
        )
        return False


def kafka_loop():
    producer = KafkaProducer(
        value_serializer=lambda value: json.dumps(value).encode(),
        **_kafka_kwargs(),
    )
    print(
        f"[llm] kafka {settings.KAFKA_TASKS_TOPIC} -> {settings.KAFKA_RESULTS_TOPIC} @ {settings.KAFKA_HOST}:{settings.KAFKA_PORT}",
        flush=True,
    )
    while True:
        consumer = None
        try:
            consumer = KafkaConsumer(
                settings.KAFKA_TASKS_TOPIC,
                group_id=settings.KAFKA_CONSUMER_GROUP,
                auto_offset_reset="earliest",
                max_poll_interval_ms=900_000,
                enable_auto_commit=False,
                value_deserializer=lambda raw: json.loads(raw.decode()),
                **_kafka_kwargs(),
            )
            for message in consumer:
                value = message.value
                if not isinstance(value, dict) or "task_id" not in value:
                    print(f"[llm] skip malformed task: {value!r}", flush=True)
                    consumer.commit()
                    continue
                if not process_task(producer, value):
                    raise RuntimeError(
                        f"[llm] task {value.get('task_id')}: "
                        f"результат не отправлен, оффсет не коммитим"
                    )
                consumer.commit()
        except Exception as exc:
            print(f"[llm] kafka error: {exc}", flush=True)
            time.sleep(5)
        finally:
            if consumer is not None:
                consumer.close()
