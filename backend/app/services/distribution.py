import time

from app.core.database import SessionLocal
from app.core.db import DistributionDB, DistributionStatus
from app.services import kafka
from sqlalchemy.orm import Session


def queue_not_extracted_objects(db: Session) -> int:
    """Отправляет все rustfs_objects со статусом NOT_EXTRACTED
    в топик features.tasks и переводит их в QUEUED."""
    distributions = (
        db.query(DistributionDB)
        .filter(DistributionDB.status == DistributionStatus.NOT_STARTED)
        .all()
    )
    for distribution in distributions:
        kafka.produce(
            kafka.settings.KAFKA_FTRS_TASKS_TOPIC,
            {
                "distribution_id": distribution.id,
                "selected_student_ids": distribution.selected_student_ids,
                "selected_teacher_ids": distribution.selected_teacher_ids,
                "selected_project_ids": distribution.selected_project_ids,
            },
        )
        distribution.status = DistributionStatus.QUEUED
    db.commit()
    return len(distributions)


def apply_distribution_result(payload: dict) -> None:
    """Применяет результат от воркера distribution к базе данных."""
    db = SessionLocal()
    try:
        distribution_db = db.get(DistributionDB, payload["distribution_id"])
        if distribution_db is None:
            print(
                "[kafka] distribution result: distribution_result не найден",
                flush=True,
            )
            return
        if payload.get("result_set") is not None:
            distribution_db.result_set = payload["result_set"]
        if payload.get("status"):
            distribution_db.status = DistributionStatus(payload["status"])
        if payload.get("model_version"):
            distribution_db.model_version = payload["model_version"]
        db.commit()
    finally:
        db.close()


def results_consumer_loop() -> None:
    """Фоновый поток: читает результаты из топика
    distribution.results и записывает их в базу данных."""
    while True:
        consumer = None
        try:
            consumer = kafka.results_consumer(
                kafka.settings.KAFKA_DIST_RESULTS_TOPIC,
                kafka.settings.KAFKA_DIST_CONSUMER_GROUP,
            )
            for message in consumer:
                apply_distribution_result(message.value)
        except Exception as exc:
            print(f"[kafka] distribution consumer error: {exc}", flush=True)
            time.sleep(5)
        finally:
            if consumer is not None:
                consumer.close()
