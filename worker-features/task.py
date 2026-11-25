import ssl
import urllib.request

from config import settings

from kafka import KafkaProducer

FIRST_LINE_LIMIT = 1024 * 1024
MODEL_VERSION = "0.0.1 2026-11-25: first line and failed status"


class TaskResponse:
    def __init__(
        self, rustfs_object_id: int, status: str, feature_set: dict, model_version: str
    ):
        self.rustfs_object_id = rustfs_object_id
        self.status = status
        self.feature_set = feature_set
        self.model_version = model_version


def task(producer: KafkaProducer, task: dict):
    rustfs_object_id = task["rustfs_object_id"]
    extension = task["extension"]
    try:
        first_line = read_first_line(rustfs_object_id)
        payload = TaskResponse(
            rustfs_object_id=rustfs_object_id,
            status="failed",
            feature_set={"extension": extension, "first_line": first_line},
            model_version=MODEL_VERSION,
        ).__dict__
    except Exception as exc:
        print(f"[features] object {rustfs_object_id} failed: {exc}", flush=True)
        payload = TaskResponse(
            rustfs_object_id=rustfs_object_id,
            status="failed",
            feature_set={
                "extension": extension,
                "error": str(exc) or type(exc).__name__,
            },
            model_version=MODEL_VERSION,
        ).__dict__

    try:
        producer.send(settings.KAFKA_RESULTS_TOPIC, payload).get(timeout=10)
    except Exception as exc:
        print(
            f"[features] object {rustfs_object_id}: "
            f"не удалось отправить результат: {exc}",
            flush=True,
        )


def read_first_line(rustfs_object_id: int) -> str:
    """Скачивает начало файла через backend и возвращает первую строку."""
    url = (
        f"{settings.BACKEND_URL}" f"/internal/rustfs-objects/{rustfs_object_id}/content"
    )
    if url.startswith("https://"):
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    else:
        context = None
    with urllib.request.urlopen(url, timeout=120, context=context) as response:
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
