from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.db import LLMRequestDB, LLMRequestFileDB, UserDB
from app.services import llm as llm_service
from app.services.security_deps import get_optional_user

router: APIRouter = APIRouter(prefix="/llms", tags=["LLMs"])

TaskStatus = Literal["queued", "running", "done", "error"]
PENDING_STATUSES = ("queued", "running")


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


class LLMTaskDetail(LLMTaskResponse):
    prompt: str
    file_ids: list[int]
    enable_thinking: bool
    max_new_tokens: int
    created_at: datetime
    updated_at: datetime


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


def _task_detail(
    request_db: LLMRequestDB, file_ids: dict[int, list[int]]
) -> LLMTaskDetail:
    return LLMTaskDetail(
        task_id=request_db.task_id,
        status=request_db.status,
        result=request_db.result or "",
        error=request_db.error or "",
        prompt=request_db.prompt,
        file_ids=file_ids.get(request_db.id, []),
        enable_thinking=request_db.enable_thinking,
        max_new_tokens=request_db.max_new_tokens,
        created_at=request_db.created_at,
        updated_at=request_db.updated_at,
    )


def _file_ids_by_request(db: Session, request_ids: list[int]) -> dict[int, list[int]]:
    """Маппинг request_id -> [file_id] для списка запросов."""
    if not request_ids:
        return {}
    rows = (
        db.query(LLMRequestFileDB.request_id, LLMRequestFileDB.file_id)
        .filter(LLMRequestFileDB.request_id.in_(request_ids))
        .all()
    )
    result: dict[int, list[int]] = {}
    for request_id, file_id in rows:
        result.setdefault(request_id, []).append(file_id)
    return result


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


@router.get("/tasks", response_model=list[LLMTaskDetail])
def list_tasks(
    status: TaskStatus | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """Все запросы к нейросети с промптами и ответами (новые сверху)."""
    query = db.query(LLMRequestDB)
    if status is not None:
        query = query.filter(LLMRequestDB.status == status)
    request_dbs = (
        query.order_by(LLMRequestDB.created_at.desc()).offset(offset).limit(limit).all()
    )
    file_ids = _file_ids_by_request(db, [r.id for r in request_dbs])
    return [_task_detail(r, file_ids) for r in request_dbs]


# Важно: объявлен до /tasks/{task_id}, чтобы "pending" не попал в task_id
@router.get("/tasks/pending", response_model=list[LLMTaskDetail])
def list_pending_tasks(db: Session = Depends(get_db)):
    """Запросы, которые ещё ждут выполнения (queued/running), старые сверху."""
    request_dbs = (
        db.query(LLMRequestDB)
        .filter(LLMRequestDB.status.in_(PENDING_STATUSES))
        .order_by(LLMRequestDB.created_at.asc())
        .all()
    )
    file_ids = _file_ids_by_request(db, [r.id for r in request_dbs])
    return [_task_detail(r, file_ids) for r in request_dbs]


@router.get("/tasks/{task_id}", response_model=LLMTaskResponse)
def get_task(task_id: str, db: Session = Depends(get_db)):
    """Статус задачи и итоговый ответ (фронт опрашивает до done/error)."""
    return _task_response(_get_request(db, task_id))
