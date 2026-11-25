import time

from app.core.database import SessionLocal
from app.core.db import FileStatus, RustfsObjectDB
from app.services import kafka as kafka_service
from sqlalchemy.orm import Session


def queue_not_extracted_objects(db: Session) -> int:
    """Отправляет все rustfs_objects со статусом NOT_EXTRACTED
    в топик features.tasks и переводит их в QUEUED."""
    objects = (
        db.query(RustfsObjectDB)
        .filter(RustfsObjectDB.status == FileStatus.NOT_EXTRACTED)
        .all()
    )
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


def reset_features(db: Session) -> int:
    """Сбрасывает статус всех rustfs_objects на NOT_EXTRACTED."""
    objects = (
        db.query(RustfsObjectDB)
        .filter(RustfsObjectDB.status == FileStatus.EXTRACTED)
        .all()
    )
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
