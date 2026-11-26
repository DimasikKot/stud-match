import json
import ssl
import urllib.request
from datetime import datetime

from app.config import settings

from kafka import KafkaProducer

FIRST_LINE_LIMIT = 1024 * 1024
MODEL_VERSION = "0.1.0 2026-11-27: extracted"


class TaskResponse:
    def __init__(
        self, rustfs_object_id: int, status: str, feature_set: dict, model_version: str
    ):
        self.rustfs_object_id = rustfs_object_id
        self.status = status
        self.feature_set = feature_set
        self.model_version = model_version


def _ssl_context(url: str) -> ssl.SSLContext | None:
    if not url.startswith("https://"):
        return None
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context


def _result(rustfs_object_id: int, status: str, feature_set: dict) -> dict:
    return TaskResponse(
        rustfs_object_id=rustfs_object_id,
        status=status,
        feature_set=feature_set,
        model_version=MODEL_VERSION,
    ).__dict__


def task(producer: KafkaProducer, task: dict) -> bool:
    rustfs_object_id = task["rustfs_object_id"]
    extension = task["extension"]

    try:
        url = f"{settings.BACKEND_URL}/internal/rustfs-objects/{rustfs_object_id}"
        with urllib.request.urlopen(
            url, timeout=60, context=_ssl_context(url)
        ) as response:
            body = json.loads(response.read())
        if not body.get("success"):
            raise RuntimeError(f"backend ответил success=false: {body}")

        first_line = read_first_line(rustfs_object_id)
        payload = _result(
            rustfs_object_id,
            "failed",
            {
                "extension": extension,
                "extracted_at": datetime.now().isoformat(),
                "first_line": first_line[:50],
            },
        )
    except Exception as exc:
        print(f"[features] object {rustfs_object_id} failed: {exc}", flush=True)
        payload = _result(
            rustfs_object_id,
            "failed",
            {
                "extension": extension,
                "extracted_at": datetime.now().isoformat(),
                "error": str(exc) or type(exc).__name__,
            },
        )

    try:
        producer.send(settings.KAFKA_RESULTS_TOPIC, payload).get(timeout=10)
        print(f" + {rustfs_object_id}", flush=True)
        return True
    except Exception as exc:
        print(
            f"[features] object {rustfs_object_id}: "
            f"не удалось отправить результат: {exc}",
            flush=True,
        )
        return False


def read_first_line(rustfs_object_id: int) -> str:
    """Скачивает начало файла через backend и возвращает первую строку."""
    url = f"{settings.BACKEND_URL}/internal/rustfs-objects/{rustfs_object_id}/content"
    with urllib.request.urlopen(
        url, timeout=120, context=_ssl_context(url)
    ) as response:
        buffer = bytearray()
        while len(buffer) < FIRST_LINE_LIMIT:
            chunk = response.read1(64 * 1024)
            if not chunk:
                break
            buffer += chunk
            newline = buffer.find(b"\n")
            if newline != -1:
                return buffer[:newline].decode("utf-8", errors="replace")
    return bytes(buffer).decode("utf-8", errors="replace")
