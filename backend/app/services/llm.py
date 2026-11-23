import io
import json
import uuid
from datetime import datetime, timezone
from pathlib import PurePath

import docx
from docx.table import Table
from fastapi import HTTPException
from pypdf import PdfReader
from redis import Redis
from sqlalchemy.orm import Session

from app.models.db import FileDB, LLMRequestDB, LLMRequestFileDB
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


def save_request(
    db: Session,
    task_id: str,
    user_id: int | None,
    prompt: str,
    file_ids: list[int],
    enable_thinking: bool,
    max_new_tokens: int,
) -> LLMRequestDB:
    """Сохраняет запрос к нейросети и использованные файлы в БД."""
    request_db = LLMRequestDB(
        task_id=task_id,
        user_id=user_id,
        prompt=prompt,
        enable_thinking=enable_thinking,
        max_new_tokens=max_new_tokens,
        status="queued",
    )
    db.add(request_db)
    db.flush()
    db.add_all(
        LLMRequestFileDB(request_id=request_db.id, file_id=file_id)
        for file_id in dict.fromkeys(file_ids)
    )
    db.commit()
    db.refresh(request_db)
    return request_db


def update_request(db: Session, task_id: str, **fields) -> None:
    """Обновляет статус/ответ нейросети в БД (если запрос там есть)."""
    request_db = db.query(LLMRequestDB).filter(LLMRequestDB.task_id == task_id).first()
    if request_db is None:
        return
    for name, value in fields.items():
        setattr(request_db, name, value)
    db.commit()


def _extract_pdf(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    return "\n\n".join((page.extract_text() or "").strip() for page in reader.pages)


def _extract_docx(data: bytes) -> str:
    document = docx.Document(io.BytesIO(data))
    parts = []
    for block in document.iter_inner_content():
        if isinstance(block, Table):
            for row in block.rows:
                parts.append(" | ".join(cell.text.strip() for cell in row.cells))
        else:
            parts.append(block.text)
    return "\n".join(parts)


DOCUMENT_EXTRACTORS = {".pdf": _extract_pdf, ".docx": _extract_docx}


def _read_document_text(file_db: FileDB, extension: str) -> str:
    s3_response = file_service.get_file_object(file_db)
    body = s3_response["Body"]
    try:
        data = body.read()
    finally:
        body.close()

    try:
        text = DOCUMENT_EXTRACTORS[extension](data).strip()
    except Exception:
        raise HTTPException(
            status_code=415,
            detail=f"Не удалось прочитать файл «{file_db.name}», возможно он повреждён",
        )
    if not text:
        raise HTTPException(
            status_code=415,
            detail=f"В файле «{file_db.name}» нет текста (возможно, это скан)",
        )
    return text


def read_file_text(file_db: FileDB, max_chars: int) -> str:
    """Возвращает текст файла (не больше max_chars символов): PDF и DOCX
    разбираются, остальные файлы читаются из RustFS/S3 как UTF-8."""
    extension = PurePath(file_db.name).suffix.lower()
    if extension in DOCUMENT_EXTRACTORS:
        return _read_document_text(file_db, extension)[:max_chars]
    if extension in (".doc", ".rtf", ".odt"):
        raise HTTPException(
            status_code=415,
            detail=f"Формат файла «{file_db.name}» не поддерживается, сохраните его как .docx или .pdf",
        )

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
