import io

import pytest
from fastapi import HTTPException

from app.models.db import FileDB, LLMRequestDB
from app.services import file as file_service
from app.services import kafka as kafka_service
from app.services import llm as llm_service


@pytest.fixture()
def produced(monkeypatch):
    """Перехватывает сообщения, которые сервис отправил бы в Kafka."""
    messages = []
    monkeypatch.setattr(
        kafka_service,
        "produce",
        lambda topic, payload: messages.append((topic, payload)),
    )
    return messages


@pytest.fixture()
def stored(monkeypatch):
    def _store(name: str, data: bytes) -> FileDB:
        monkeypatch.setattr(
            file_service, "get_file_object", lambda f: {"Body": io.BytesIO(data)}
        )
        return FileDB(name=name, object_key="k", path="/" + name, size=len(data))

    return _store


def _add_file(db_session, name: str = "notes.txt") -> FileDB:
    file_db = FileDB(name=name, object_key="k", path="/" + name, size=10)
    db_session.add(file_db)
    db_session.commit()
    db_session.refresh(file_db)
    return file_db


def test_create_llm_task(db_session, produced, monkeypatch):
    monkeypatch.setattr(
        file_service,
        "get_file_object",
        lambda f: {"Body": io.BytesIO(b"file text")},
    )
    file_db = _add_file(db_session)

    request_db = llm_service.create_llm_task(
        db_session, "вопрос", [file_db.id], True, 64, user_id=None
    )

    assert request_db.status == "queued"
    assert request_db.prompt == "вопрос"
    topic, message = produced[0]
    assert topic == kafka_service.TASKS_TOPIC
    assert message["task_id"] == request_db.task_id
    assert message["enable_thinking"] is True
    assert message["max_new_tokens"] == 64
    assert "file text" in message["prompt"]
    assert "вопрос" in message["prompt"]


def test_create_llm_task_kafka_down(db_session, monkeypatch):
    def _fail(topic, payload):
        raise RuntimeError("kafka down")

    monkeypatch.setattr(kafka_service, "produce", _fail)

    with pytest.raises(HTTPException) as exc:
        llm_service.create_llm_task(db_session, "hi", [], False, 1, user_id=None)
    assert exc.value.status_code == 503

    request_db = db_session.query(LLMRequestDB).one()
    assert request_db.status == "error"
    assert "kafka down" in request_db.error


def test_apply_result(db_session, produced):
    request_db = llm_service.create_llm_task(
        db_session, "hi", [], False, 1, user_id=None
    )

    llm_service.apply_result(
        db_session, {"task_id": request_db.task_id, "status": "running"}
    )
    db_session.refresh(request_db)
    assert request_db.status == "running"

    llm_service.apply_result(
        db_session, {"task_id": request_db.task_id, "result": "ok"}
    )
    db_session.refresh(request_db)
    assert request_db.status == "done"
    assert request_db.result == "ok"


def test_apply_result_error_and_missing(db_session, produced):
    request_db = llm_service.create_llm_task(
        db_session, "hi", [], False, 1, user_id=None
    )

    llm_service.apply_result(
        db_session, {"task_id": request_db.task_id, "error": "CUDA OOM"}
    )
    db_session.refresh(request_db)
    assert request_db.status == "error"
    assert request_db.error == "CUDA OOM"
    assert request_db.result is None

    # Сообщение по несуществующей задаче не должно падать
    llm_service.apply_result(db_session, {"task_id": "missing", "result": "x"})
    llm_service.apply_result(db_session, {})


def test_build_prompt():
    assert llm_service.build_prompt("вопрос", []) == "вопрос"
    prompt = llm_service.build_prompt("вопрос", [("a.txt", "AAA"), ("b.md", "BBB")])
    assert prompt.index("a.txt") < prompt.index("b.md") < prompt.index("вопрос")
    assert "```\nAAA\n```" in prompt


def test_plain_text_file(stored):
    text = llm_service.read_file_text(stored("a.txt", "привет мир".encode()), 6)
    assert text == "привет"


def test_invalid_utf8_is_replaced(stored):
    assert llm_service.read_file_text(stored("a.txt", b"ok\xff"), 100) == "ok\ufffd"


def test_binary_file_rejected(stored):
    with pytest.raises(HTTPException) as exc:
        llm_service.read_file_text(stored("a.bin", b"a\x00b"), 100)
    assert exc.value.status_code == 415
