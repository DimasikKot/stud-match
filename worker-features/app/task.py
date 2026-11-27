import json
import ssl
import urllib.request
from datetime import datetime

from app.config import settings
from app.extract import SkippedFile, extract_text, limit_chunks, split_chunks
from app.llm import MODEL_VERSION, extract_chunk_skills, merge_skills

from kafka import KafkaProducer


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
    print(
        f"[features] Processing object {rustfs_object_id} with extension {extension}, model version: {MODEL_VERSION}",
        flush=True,
    )
    meta = {"extension": extension, "extracted_at": datetime.now().isoformat()}

    try:
        url = f"{settings.BACKEND_URL}/internal/rustfs-objects/{rustfs_object_id}"
        with urllib.request.urlopen(
            url, timeout=60, context=_ssl_context(url)
        ) as response:
            body = json.loads(response.read())
        if not body.get("success"):
            raise RuntimeError(f"backend ответил success=false: {body}")

        try:
            text = extract_text(extension, read_content(rustfs_object_id))
        except SkippedFile as skipped:
            # Пропущенный файл считается обработанным, чтобы его не гоняли повторно
            payload = _result(
                rustfs_object_id,
                "extracted",
                {**meta, "skills": {}, "skipped": str(skipped)},
            )
        else:
            skills, chunks_total, chunks_failed = analyze_text(rustfs_object_id, text)
            payload = _result(
                rustfs_object_id,
                "extracted",
                {
                    **meta,
                    "skills": skills,
                    "chunks": chunks_total,
                    "chunks_failed": chunks_failed,
                },
            )
    except Exception as exc:
        print(f"[features] object {rustfs_object_id} failed: {exc}", flush=True)
        payload = _result(
            rustfs_object_id,
            "failed",
            {**meta, "error": str(exc) or type(exc).__name__},
        )

    try:
        producer.send(settings.KAFKA_RESULTS_TOPIC, payload).get(timeout=10)
        print(f" + {rustfs_object_id} {payload['status']}", flush=True)
        return True
    except Exception as exc:
        print(
            f"[features] object {rustfs_object_id}: "
            f"не удалось отправить результат: {exc}",
            flush=True,
        )
        return False


def analyze_text(rustfs_object_id: int, text: str) -> tuple[dict, int, int]:
    """Режет текст на чанки, прогоняет каждый через модель и объединяет навыки.

    Возвращает навыки, число обработанных чанков и число чанков с невалидным ответом.
    Если невалидны все чанки, бросает RuntimeError, и файл получит статус failed."""
    chunks = limit_chunks(
        split_chunks(text, settings.CHUNK_CHARS, settings.CHUNK_OVERLAP_CHARS),
        settings.MAX_CHUNKS_PER_FILE,
    )
    per_chunk: list[dict] = []
    failed = 0
    for index, chunk in enumerate(chunks, start=1):
        try:
            per_chunk.append(extract_chunk_skills(chunk))
        except ValueError as exc:
            failed += 1
            print(
                f"[features] object {rustfs_object_id} chunk {index}/{len(chunks)}: "
                f"невалидный ответ модели: {exc}",
                f"raw: {chunk}",
                flush=True,
            )
    if chunks and failed == len(chunks):
        raise RuntimeError("модель не вернула валидный JSON ни для одного чанка")
    return merge_skills(per_chunk), len(chunks), failed


def read_content(rustfs_object_id: int) -> bytes:
    """Скачивает файл целиком через backend, с ограничением по размеру."""
    url = f"{settings.BACKEND_URL}/internal/rustfs-objects/{rustfs_object_id}/content"
    buffer = bytearray()
    with urllib.request.urlopen(
        url, timeout=120, context=_ssl_context(url)
    ) as response:
        while chunk := response.read(64 * 1024):
            buffer += chunk
            if len(buffer) > settings.MAX_FILE_BYTES:
                raise RuntimeError("размер файла превышает допустимый предел")
    return bytes(buffer)
