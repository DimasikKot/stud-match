import time
from urllib.parse import quote

from app.core.database import SessionLocal
from app.core.db import FileStatus, RustfsObjectDB
from app.services import file
from app.services import kafka as kafka_service
from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool
from starlette.responses import StreamingResponse


def _content_disposition(disposition: str, filename: str) -> str:
    """Content-Disposition с поддержкой не-ASCII имён (RFC 5987)."""
    return f"{disposition}; filename*=UTF-8''{quote(filename)}"


async def stream_rustfs_object(
    rustfs_object: RustfsObjectDB,
    filename: str,
    disposition: str,
    media_type: str,
) -> StreamingResponse:
    """Отдаёт объект из RustFS/S3 потоком."""
    s3_response = await run_in_threadpool(file.get_rustfs_object_file, rustfs_object)
    body = s3_response["Body"]

    def iterator():
        try:
            while chunk := body.read(64 * 1024):
                yield chunk
        finally:
            body.close()

    headers = {
        "Content-Disposition": _content_disposition(disposition, filename),
    }
    content_length = s3_response.get("ContentLength")
    if content_length is not None:
        headers["Content-Length"] = str(content_length)

    return StreamingResponse(
        iterator(),
        media_type=media_type,
        headers=headers,
    )


def fetch_rustfs_objects(
    status: FileStatus | None, db: Session = None
) -> list[RustfsObjectDB]:
    if db is None:
        db = SessionLocal()
    query = db.query(RustfsObjectDB)

    if status is not None:
        query = query.filter(RustfsObjectDB.status == status)
    return query.all()


def fetch_rustfs_object_by_id(db: Session, rustfs_object_id: int) -> RustfsObjectDB:
    rustfs_object = db.get(RustfsObjectDB, rustfs_object_id)
    if rustfs_object is None:
        raise HTTPException(
            status_code=404, detail=f"Объект {rustfs_object_id} не найден"
        )
    return rustfs_object


def queue_not_extracted_objects(
    db: Session, status: FileStatus = FileStatus.NOT_EXTRACTED
) -> int:
    """Отправляет все rustfs_objects со статусом NOT_EXTRACTED
    в топик features.tasks и переводит их в QUEUED."""
    objects = db.query(RustfsObjectDB).filter(RustfsObjectDB.status == status).all()
    for rustfs_object in objects:
        kafka_service.produce(
            kafka_service.settings.KAFKA_FTRS_TASKS_TOPIC,
            {
                "rustfs_object_id": rustfs_object.id,
                "extension": rustfs_object.extension,
            },
        )
        rustfs_object.status = FileStatus.QUEUED
    db.commit()
    return len(objects)


def reset_features(db: Session, status: FileStatus = FileStatus.EXTRACTED) -> int:
    """Сбрасывает статус всех rustfs_objects на NOT_EXTRACTED."""
    objects = db.query(RustfsObjectDB).filter(RustfsObjectDB.status == status).all()
    for rustfs_object in objects:
        rustfs_object.status = FileStatus.NOT_EXTRACTED
    db.commit()
    return len(objects)


def apply_feature_result(payload: dict) -> None:
    """Применяет результат от воркера features к rustfs_objects."""
    db = SessionLocal()
    try:
        rustfs_object = db.get(RustfsObjectDB, payload["rustfs_object_id"])
        if rustfs_object is None:
            print(
                f"[kafka] features result: объект {payload['rustfs_object_id']} не найден",
                flush=True,
            )
            return
        if payload.get("feature_set") is not None:
            rustfs_object.feature_set = payload["feature_set"]
        if payload.get("status"):
            rustfs_object.status = FileStatus(payload["status"])
        if payload.get("model_version"):
            rustfs_object.model_version = payload["model_version"]
        db.commit()
    finally:
        db.close()


def results_consumer_loop() -> None:
    """Фоновый поток: читает результаты из топика
    features.results и записывает их в rustfs_objects."""
    while True:
        consumer = None
        try:
            consumer = kafka_service.results_consumer(
                kafka_service.settings.KAFKA_FTRS_RESULTS_TOPIC,
                kafka_service.settings.KAFKA_FTRS_CONSUMER_GROUP,
            )
            for message in consumer:
                apply_feature_result(message.value)
        except Exception as exc:
            print(f"[kafka] features consumer error: {exc}", flush=True)
            time.sleep(5)
        finally:
            if consumer is not None:
                consumer.close()
