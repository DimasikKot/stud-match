import io
import time
import uuid
from pathlib import PurePath

import docx
from docx.table import Table
from fastapi import HTTPException
from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.db import FileDB, LLMRequestDB, LLMRequestFileDB
from app.services import file as file_service
from app.services import kafka as kafka_service


def build_task_prompt(db: Session, file_ids: list[int], prompt: str) -> str:
    """Итоговый запрос для нейросети: текст пользователя + содержимое файлов."""
    files: list[tuple[str, str]] = []
    chars_left = settings.LLM_MAX_FILES_CHARS
    for file_id in file_ids:
        if chars_left <= 0:
            raise HTTPException(
                status_code=413,
                detail=f"Слишком много текста в файлах (лимит {settings.LLM_MAX_FILES_CHARS} символов)",
            )
        file_db = file_service.fetch_file_by_id(db, file_id)
        text = read_file_text(file_db, chars_left)
        chars_left -= len(text)
        files.append((file_db.name, text))
    return build_prompt(prompt, files)


def create_llm_task(
    db: Session,
    prompt: str,
    file_ids: list[int],
    enable_thinking: bool,
    max_new_tokens: int,
    user_id: int | None,
) -> LLMRequestDB:
    """Сохраняет задачу в БД и отправляет её в Kafka для llm-worker."""
    task_id = uuid.uuid4().hex
    full_prompt = build_task_prompt(db, file_ids, prompt)

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

    try:
        kafka_service.produce(
            kafka_service.TASKS_TOPIC,
            {
                "task_id": task_id,
                "prompt": full_prompt,
                "enable_thinking": enable_thinking,
                "max_new_tokens": max_new_tokens,
            },
        )
    except Exception as exc:
        update_request(db, task_id, status="error", error=str(exc))
        raise HTTPException(status_code=503, detail="Kafka недоступна")

    return request_db


def update_request(db: Session, task_id: str, **fields) -> None:
    """Обновляет статус/ответ нейросети в БД (если запрос там есть)."""
    request_db = db.query(LLMRequestDB).filter(LLMRequestDB.task_id == task_id).first()
    if request_db is None:
        return
    for name, value in fields.items():
        setattr(request_db, name, value)
    db.commit()


def apply_result(db: Session, payload: dict) -> None:
    """Применяет сообщение llm-worker из топика llm.results к задаче в БД."""
    task_id = payload.get("task_id")
    request_db = (
        db.query(LLMRequestDB).filter(LLMRequestDB.task_id == task_id).first()
        if task_id
        else None
    )
    if request_db is None:
        return

    if payload.get("status") == "running":
        request_db.status = "running"
    elif payload.get("error") is not None:
        request_db.status = "error"
        request_db.error = payload["error"]
    elif "result" in payload:
        request_db.status = "done"
        request_db.result = payload["result"] or ""
    else:
        return
    db.commit()


def results_consumer_loop() -> None:
    """Фоновый поток: читает llm.results и обновляет статусы задач в БД."""
    while True:
        consumer = None
        try:
            consumer = kafka_service.results_consumer()
            for message in consumer:
                db = SessionLocal()
                try:
                    apply_result(db, message.value)
                except Exception as exc:
                    db.rollback()
                    print(f"[kafka] llm.results error: {exc}", flush=True)
                finally:
                    db.close()
        except Exception as exc:
            print(f"[kafka] consumer error: {exc}", flush=True)
            time.sleep(5)
        finally:
            if consumer is not None:
                consumer.close()


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
