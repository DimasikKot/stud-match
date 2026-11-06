import json
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from redis import Redis

from app.models.db import FileDB
from app.services import file as file_service

QUEUE_KEY = "llm:queue"
TASK_TTL_SECONDS = 24 * 60 * 60


def task_key(task_id: str) -> str:
    return f"llm:task:{task_id}"


def stream_key(task_id: str) -> str:
    """Redis Stream с кусками ответа, его пишет llm-worker."""
    return f"llm:task:{task_id}:stream"


def create_task(
    redis: Redis,
    prompt: str,
    file_ids: list[int],
    enable_thinking: bool,
    max_new_tokens: int,
) -> str:
    """Сохраняет задачу в Redis и ставит её в очередь для llm-worker."""
    task_id = uuid.uuid4().hex
    key = task_key(task_id)
    pipe = redis.pipeline()
    pipe.hset(
        key,
        mapping={
            "status": "queued",
            "prompt": prompt,
            "file_ids": json.dumps(file_ids),
            "enable_thinking": int(enable_thinking),
            "max_new_tokens": max_new_tokens,
            "result": "",
            "error": "",
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    pipe.expire(key, TASK_TTL_SECONDS)
    pipe.lpush(QUEUE_KEY, task_id)
    pipe.execute()
    return task_id


def get_task(redis: Redis, task_id: str) -> dict:
    task = redis.hgetall(task_key(task_id))
    if not task:
        raise HTTPException(status_code=404, detail=f"Задача {task_id} не найдена")
    return task


def update_task(redis: Redis, task_id: str, **fields) -> None:
    redis.hset(task_key(task_id), mapping=fields)


def read_file_text(file_db: FileDB, max_chars: int) -> str:
    """Читает файл из RustFS/S3 как UTF-8 текст (не больше max_chars символов)."""
    s3_response = file_service.get_file_object(file_db)
    body = s3_response["Body"]
    try:
        raw = body.read(max_chars * 4)  # в UTF-8 символ занимает до 4 байт
    finally:
        body.close()

    if b"\x00" in raw:
        raise HTTPException(
            status_code=415,
            detail=f"Файл «{file_db.name}» не текстовый, его нельзя передать в нейросеть",
        )
    return raw.decode("utf-8", errors="replace")[:max_chars]


def build_prompt(prompt: str, files: list[tuple[str, str]]) -> str:
    """Собирает итоговый запрос: содержимое файлов + вопрос пользователя."""
    if not files:
        return prompt
    parts = ["Используй содержимое приложенных файлов, чтобы ответить на запрос."]
    for name, text in files:
        parts.append(f"Файл «{name}»:\n```\n{text}\n```")
    parts.append(f"Запрос:\n{prompt}")
    return "\n\n".join(parts)
