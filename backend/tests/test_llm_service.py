import io
import json

import fakeredis
import pytest
from fastapi import HTTPException

from app.models.db import FileDB
from app.services import file as file_service
from app.services import llm as llm_service


@pytest.fixture()
def redis():
    return fakeredis.FakeRedis(decode_responses=True)


def test_create_and_get_task(redis):
    task_id = llm_service.create_task(
        redis, prompt="hi", file_ids=[1, 2], enable_thinking=True, max_new_tokens=64
    )
    task = llm_service.get_task(redis, task_id)
    assert task["status"] == "queued"
    assert json.loads(task["file_ids"]) == [1, 2]
    assert task["enable_thinking"] == "1"
    assert task["max_new_tokens"] == "64"
    assert redis.ttl(llm_service.task_key(task_id)) > 0
    assert redis.lrange(llm_service.QUEUE_KEY, 0, -1) == [task_id]


def test_update_and_missing_task(redis):
    task_id = llm_service.create_task(redis, "hi", [], False, 1)
    llm_service.update_task(redis, task_id, status="done", result="ok")
    assert llm_service.get_task(redis, task_id)["result"] == "ok"
    with pytest.raises(HTTPException) as exc:
        llm_service.get_task(redis, "missing")
    assert exc.value.status_code == 404


def test_build_prompt():
    assert llm_service.build_prompt("вопрос", []) == "вопрос"
    prompt = llm_service.build_prompt("вопрос", [("a.txt", "AAA"), ("b.md", "BBB")])
    assert prompt.index("a.txt") < prompt.index("b.md") < prompt.index("вопрос")
    assert "```\nAAA\n```" in prompt


@pytest.fixture()
def stored(monkeypatch):
    def _store(name: str, data: bytes) -> FileDB:
        monkeypatch.setattr(
            file_service, "get_file_object", lambda f: {"Body": io.BytesIO(data)}
        )
        return FileDB(name=name, object_key="k", path="/", size=len(data))

    return _store


def test_plain_text_file(stored):
    text = llm_service.read_file_text(stored("a.txt", "привет мир".encode()), 6)
    assert text == "привет"


def test_invalid_utf8_is_replaced(stored):
    assert llm_service.read_file_text(stored("a.txt", b"ok\xff"), 100) == "ok\ufffd"


def test_binary_file_rejected(stored):
    with pytest.raises(HTTPException) as exc:
        llm_service.read_file_text(stored("a.bin", b"a\x00b"), 100)
    assert exc.value.status_code == 415
