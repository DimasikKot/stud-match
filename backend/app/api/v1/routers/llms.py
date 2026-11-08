import json
from typing import Literal

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from redis import Redis
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.services import file as file_service
from app.services import llm as llm_service
from app.models.db import UserDB
from app.services.security_deps import (
    get_async_redis,
    get_optional_user,
    get_redis,
    verify_service_token,
)

router: APIRouter = APIRouter(prefix="/llms", tags=["LLMs"])

# Меньше socket_timeout клиента Redis (5 c)
STREAM_BLOCK_MS = 4000

TaskStatus = Literal["queued", "running", "done", "error"]


class LLMTaskCreate(BaseModel):
    prompt: str = Field(min_length=1)
    file_ids: list[int] = []
    enable_thinking: bool = True
    max_new_tokens: int = Field(default=1024, ge=1, le=8192)


class LLMTaskResponse(BaseModel):
    task_id: str
    status: TaskStatus
    result: str = ""
    error: str = ""


class LLMTaskContext(BaseModel):
    task_id: str
    prompt: str
    enable_thinking: bool
    max_new_tokens: int


class LLMTaskResult(BaseModel):
    result: str | None = None
    error: str | None = None


def _task_response(task_id: str, task: dict) -> LLMTaskResponse:
    return LLMTaskResponse(
        task_id=task_id,
        status=task["status"],
        result=task.get("result", ""),
        error=task.get("error", ""),
    )


# ===== Для фронтенда =====


@router.post("/tasks", response_model=LLMTaskResponse)
def create_task(
    request: LLMTaskCreate,
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
    user: UserDB | None = Depends(get_optional_user),
):
    """Ставит запрос к нейросети в очередь Redis и сохраняет его в БД.
    Файлы передаются по id из БД."""
    for file_id in request.file_ids:
        file_service.fetch_file_by_id(db, file_id)

    task_id = llm_service.create_task(
        redis,
        prompt=request.prompt,
        file_ids=request.file_ids,
        enable_thinking=request.enable_thinking,
        max_new_tokens=request.max_new_tokens,
    )
    llm_service.save_request(
        db,
        task_id=task_id,
        user_id=user.id if user else None,
        prompt=request.prompt,
        file_ids=request.file_ids,
        enable_thinking=request.enable_thinking,
        max_new_tokens=request.max_new_tokens,
    )
    return LLMTaskResponse(task_id=task_id, status="queued")


@router.get("/tasks/{task_id}", response_model=LLMTaskResponse)
def get_task(task_id: str, redis: Redis = Depends(get_redis)):
    """Статус задачи и итоговый ответ."""
    return _task_response(task_id, llm_service.get_task(redis, task_id))


@router.get("/tasks/{task_id}/stream", response_class=StreamingResponse)
async def stream_task(
    task_id: str,
    redis: aioredis.Redis = Depends(get_async_redis),
):
    """Ответ нейросети по мере генерации (text/plain).

    Рассуждения модели (thinking) приходят внутри `<think>...</think>`.
    Стрим закрывается, когда задача завершена; итог — в `GET /llms/tasks/{task_id}`.
    """
    task_key = llm_service.task_key(task_id)
    stream_key = llm_service.stream_key(task_id)
    if not await redis.exists(task_key):
        await redis.aclose()
        raise HTTPException(status_code=404, detail=f"Задача {task_id} не найдена")

    async def chunks():
        last_id = "0"
        try:
            while True:
                response = await redis.xread(
                    {stream_key: last_id}, count=100, block=STREAM_BLOCK_MS
                )
                if not response:
                    status = await redis.hget(task_key, "status")
                    if status in (None, "done", "error") and not await redis.exists(
                        stream_key
                    ):
                        return
                    continue
                for _, entries in response:
                    for entry_id, fields in entries:
                        last_id = entry_id
                        if "chunk" in fields:
                            yield fields["chunk"]
                        elif fields.get("event") in ("done", "error"):
                            return
        finally:
            await redis.aclose()

    return StreamingResponse(
        chunks(),
        media_type="text/plain; charset=utf-8",
        headers={"X-Accel-Buffering": "no"},  # nginx не буферизует стрим
    )


# ===== Для llm-worker (Bearer-токен из TRAIN_JWT_ACCESS_TOKENS) =====


@router.get(
    "/tasks/{task_id}/context",
    response_model=LLMTaskContext,
    dependencies=[Depends(verify_service_token)],
)
def get_task_context(
    task_id: str,
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """Итоговый запрос для нейросети: текст пользователя + содержимое файлов."""
    task = llm_service.get_task(redis, task_id)

    files: list[tuple[str, str]] = []
    chars_left = settings.LLM_MAX_FILES_CHARS
    for file_id in json.loads(task["file_ids"]):
        if chars_left <= 0:
            raise HTTPException(
                status_code=413,
                detail=f"Слишком много текста в файлах (лимит {settings.LLM_MAX_FILES_CHARS} символов)",
            )
        file_db = file_service.fetch_file_by_id(db, file_id)
        text = llm_service.read_file_text(file_db, chars_left)
        chars_left -= len(text)
        files.append((file_db.name, text))

    llm_service.update_task(redis, task_id, status="running")
    llm_service.update_request(db, task_id, status="running")
    return LLMTaskContext(
        task_id=task_id,
        prompt=llm_service.build_prompt(task["prompt"], files),
        enable_thinking=bool(int(task["enable_thinking"])),
        max_new_tokens=int(task["max_new_tokens"]),
    )


@router.post(
    "/tasks/{task_id}/result",
    response_model=LLMTaskResponse,
    dependencies=[Depends(verify_service_token)],
)
def save_task_result(
    task_id: str,
    request: LLMTaskResult,
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """Сохраняет итоговый ответ (или ошибку) нейросети в Redis и БД."""
    llm_service.get_task(redis, task_id)
    if request.error:
        llm_service.update_task(redis, task_id, status="error", error=request.error)
        llm_service.update_request(db, task_id, status="error", error=request.error)
    else:
        result = request.result or ""
        llm_service.update_task(redis, task_id, status="done", result=result)
        llm_service.update_request(db, task_id, status="done", result=result)
    return _task_response(task_id, llm_service.get_task(redis, task_id))
