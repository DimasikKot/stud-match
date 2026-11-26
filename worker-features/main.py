import json
import ssl
import threading
import time
from contextlib import asynccontextmanager

from app.config import settings
from app.task import task
from fastapi import FastAPI

from kafka import KafkaConsumer, KafkaProducer


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
        "api_version_auto_timeout_ms": 60000,
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


state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    state["queue_thread"] = threading.Thread(
        target=kafka_loop, daemon=True, name="features-kafka"
    )
    state["queue_thread"].start()
    yield
    state.clear()


app = FastAPI(title="sm-features-worker", lifespan=lifespan)


@app.get("/health")
def health():
    queue_thread = state.get("queue_thread")
    return {
        "status": "ok",
        "consumer": bool(queue_thread and queue_thread.is_alive()),
    }


def kafka_loop():
    producer = KafkaProducer(
        value_serializer=lambda value: json.dumps(value).encode(),
        **_kafka_kwargs(),
    )
    print(
        f"[features] kafka {settings.KAFKA_TASKS_TOPIC} -> {settings.KAFKA_RESULTS_TOPIC} @ {settings.KAFKA_HOST}:{settings.KAFKA_PORT}",
        flush=True,
    )
    while True:
        consumer = None
        try:
            consumer = KafkaConsumer(
                settings.KAFKA_TASKS_TOPIC,
                group_id=settings.KAFKA_CONSUMER_GROUP,
                auto_offset_reset="earliest",
                max_poll_interval_ms=3600000,
                enable_auto_commit=False,
                value_deserializer=lambda raw: json.loads(raw.decode()),
                **_kafka_kwargs(),
            )
            for message in consumer:
                success = task(producer, message.value)
                if success:
                    consumer.commit()
        except Exception as exc:
            print(f"[features] kafka error: {exc}", flush=True)
            time.sleep(5)
        finally:
            if consumer is not None:
                consumer.close()
