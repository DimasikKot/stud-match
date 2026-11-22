import time

from app.services import kafka as kafka_service


def results_consumer_loop() -> None:
    """Фоновый поток: читает результаты predict-worker из топика
    llm.results_predict. Пока только логирует сообщения - логика
    обработки и таблица в БД для predict-задач ещё не добавлены."""
    while True:
        consumer = None
        try:
            consumer = kafka_service.results_consumer("predict")
            for message in consumer:
                print(f"[kafka] predict result: {message.value}", flush=True)
        except Exception as exc:
            print(f"[kafka] predict consumer error: {exc}", flush=True)
            time.sleep(5)
        finally:
            if consumer is not None:
                consumer.close()
