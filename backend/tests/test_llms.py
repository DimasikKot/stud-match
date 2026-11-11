import io

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.routers.llms import router as llms_router
from app.core.database import get_db
from app.models.db import FileDB, LLMRequestDB, LLMRequestFileDB
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
def llm_client(db_session, produced, monkeypatch):
    monkeypatch.setattr(
        file_service,
        "get_file_object",
        lambda file_db: {"Body": io.BytesIO(f"content of {file_db.name}".encode())},
    )
    app = FastAPI()
    app.include_router(llms_router)

    def _get_db():
        yield db_session

    app.dependency_overrides[get_db] = _get_db
    with TestClient(app) as client:
        yield client


@pytest.fixture()
def file_id(db_session):
    file_db = FileDB(name="notes.txt", object_key="k", path="/notes.txt", size=10)
    db_session.add(file_db)
    db_session.commit()
    return file_db.id


def test_task_lifecycle(llm_client, produced, file_id, db_session):
    resp = llm_client.post(
        "/llms/tasks",
        json={
            "prompt": "Что в файле?",
            "file_ids": [file_id],
            "enable_thinking": False,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    task_id = body["task_id"]
    assert body["status"] == "queued"

    # В Kafka ушла задача с готовым prompt (файл уже прочитан бэкендом)
    topic, message = produced[0]
    assert topic == kafka_service.TASKS_TOPIC
    assert message["task_id"] == task_id
    assert "content of notes.txt" in message["prompt"]
    assert "Что в файле?" in message["prompt"]

    # Статус задачи — из БД
    assert llm_client.get(f"/llms/tasks/{task_id}").json()["status"] == "queued"

    # llm-worker присылает running, затем результат
    llm_service.apply_result(db_session, {"task_id": task_id, "status": "running"})
    assert llm_client.get(f"/llms/tasks/{task_id}").json()["status"] == "running"

    llm_service.apply_result(db_session, {"task_id": task_id, "result": "Привет"})
    task = llm_client.get(f"/llms/tasks/{task_id}").json()
    assert task == {
        "task_id": task_id,
        "status": "done",
        "result": "Привет",
        "error": "",
    }

    request_db = db_session.query(LLMRequestDB).filter_by(task_id=task_id).one()
    assert request_db.prompt == "Что в файле?"
    assert request_db.status == "done"
    assert request_db.result == "Привет"
    assert request_db.error is None
    assert request_db.enable_thinking is False
    assert [f.file_id for f in db_session.query(LLMRequestFileDB).all()] == [file_id]


def test_error_result(llm_client, db_session):
    task_id = llm_client.post("/llms/tasks", json={"prompt": "hi"}).json()["task_id"]
    llm_service.apply_result(db_session, {"task_id": task_id, "error": "CUDA OOM"})
    task = llm_client.get(f"/llms/tasks/{task_id}").json()
    assert task["status"] == "error"
    assert task["error"] == "CUDA OOM"
    request_db = db_session.query(LLMRequestDB).filter_by(task_id=task_id).one()
    assert (request_db.status, request_db.error) == ("error", "CUDA OOM")
    assert request_db.result is None


def test_unknown_file_and_task(llm_client):
    assert (
        llm_client.post(
            "/llms/tasks", json={"prompt": "hi", "file_ids": [999]}
        ).status_code
        == 404
    )
    assert llm_client.get("/llms/tasks/nope").status_code == 404
