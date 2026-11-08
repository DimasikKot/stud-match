import io

import fakeredis
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.routers.llms import router as llms_router
from app.core.config import settings
from app.core.database import get_db
from app.models.db import FileDB, LLMRequestDB, LLMRequestFileDB
from app.services import file as file_service
from app.services import llm as llm_service
from app.services.security_deps import get_async_redis, get_redis

TOKEN = settings.TRAIN_JWT_ACCESS_TOKENS[0]
WORKER_HEADERS = {"Authorization": f"Bearer {TOKEN}"}


@pytest.fixture()
def redis_server():
    return fakeredis.FakeServer()


@pytest.fixture()
def sync_redis(redis_server):
    return fakeredis.FakeRedis(server=redis_server, decode_responses=True)


@pytest.fixture()
def llm_client(db_session, redis_server, sync_redis, monkeypatch):
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
    app.dependency_overrides[get_redis] = lambda: sync_redis
    app.dependency_overrides[get_async_redis] = lambda: fakeredis.FakeAsyncRedis(
        server=redis_server, decode_responses=True
    )
    with TestClient(app) as client:
        yield client


@pytest.fixture()
def file_id(db_session):
    file_db = FileDB(name="notes.txt", object_key="k", path="/notes.txt", size=10)
    db_session.add(file_db)
    db_session.commit()
    return file_db.id


def test_task_full_cycle(llm_client, sync_redis, file_id, db_session):
    resp = llm_client.post(
        "/llms/tasks",
        json={
            "prompt": "Что в файле?",
            "file_ids": [file_id],
            "enable_thinking": False,
        },
    )
    assert resp.status_code == 200
    task_id = resp.json()["task_id"]
    assert resp.json()["status"] == "queued"
    assert sync_redis.rpop(llm_service.QUEUE_KEY) == task_id

    # llm-worker забирает запрос и файлы
    resp = llm_client.get(f"/llms/tasks/{task_id}/context", headers=WORKER_HEADERS)
    assert resp.status_code == 200
    context = resp.json()
    assert "content of notes.txt" in context["prompt"]
    assert "Что в файле?" in context["prompt"]
    assert context["enable_thinking"] is False
    assert llm_client.get(f"/llms/tasks/{task_id}").json()["status"] == "running"

    # llm-worker стримит токены в Redis и сохраняет итог
    stream_key = llm_service.stream_key(task_id)
    sync_redis.xadd(stream_key, {"chunk": "При"})
    sync_redis.xadd(stream_key, {"chunk": "вет"})
    resp = llm_client.post(
        f"/llms/tasks/{task_id}/result",
        json={"result": "Привет"},
        headers=WORKER_HEADERS,
    )
    assert resp.json()["status"] == "done"
    sync_redis.xadd(stream_key, {"event": "done"})

    assert llm_client.get(f"/llms/tasks/{task_id}/stream").text == "Привет"
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


def test_worker_endpoints_require_token(llm_client):
    task_id = llm_client.post("/llms/tasks", json={"prompt": "hi"}).json()["task_id"]
    assert llm_client.get(f"/llms/tasks/{task_id}/context").status_code == 401
    resp = llm_client.post(
        f"/llms/tasks/{task_id}/result",
        json={"result": "x"},
        headers={"Authorization": "Bearer wrong"},
    )
    assert resp.status_code == 401


def test_error_result(llm_client, db_session):
    task_id = llm_client.post("/llms/tasks", json={"prompt": "hi"}).json()["task_id"]
    llm_client.post(
        f"/llms/tasks/{task_id}/result",
        json={"error": "CUDA OOM"},
        headers=WORKER_HEADERS,
    )
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
    assert llm_client.get("/llms/tasks/nope/stream").status_code == 404
