from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.db import LLMRequestDB, UserDB
from app.services import llm as llm_service
from app.services.security_deps import get_optional_user

router: APIRouter = APIRouter(prefix="/llms", tags=["LLMs"])

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


def _get_request(db: Session, task_id: str) -> LLMRequestDB:
    request_db = db.query(LLMRequestDB).filter(LLMRequestDB.task_id == task_id).first()
    if request_db is None:
        raise HTTPException(status_code=404, detail=f"Задача {task_id} не найдена")
    return request_db


def _task_response(request_db: LLMRequestDB) -> LLMTaskResponse:
    return LLMTaskResponse(
        task_id=request_db.task_id,
        status=request_db.status,
        result=request_db.result or "",
        error=request_db.error or "",
    )


# ===== Для фронтенда =====


@router.post("/tasks", response_model=LLMTaskResponse)
def create_task(
    request: LLMTaskCreate,
    db: Session = Depends(get_db),
    user: UserDB | None = Depends(get_optional_user),
):
    """Ставит запрос к нейросети в очередь Kafka и сохраняет его в БД.
    Файлы передаются по id из БД."""
    request_db = llm_service.create_llm_task(
        db,
        prompt=request.prompt,
        file_ids=request.file_ids,
        enable_thinking=request.enable_thinking,
        max_new_tokens=request.max_new_tokens,
        user_id=user.id if user else None,
    )
    return _task_response(request_db)


@router.get("/tasks/{task_id}", response_model=LLMTaskResponse)
def get_task(task_id: str, db: Session = Depends(get_db)):
    """Статус задачи и итоговый ответ (фронт опрашивает до done/error)."""
    return _task_response(_get_request(db, task_id))
