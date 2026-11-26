import mimetypes
from typing import Any

from app.core.database import get_db
from app.core.db import FileStatus
from app.services import rustfs_object
from app.services.get_user import require_admin
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from pydantic.config import ConfigDict
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/rustfs-objects",
    tags=["Rustfs Objects"],
    dependencies=[Depends(require_admin)],
)


class RustfsObjectListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: int
    object_key: str
    status: FileStatus
    feature_set: dict[str, Any]
    model_version: str


class RustfsObjectListResponseData(BaseModel):
    count: int
    data: list[RustfsObjectListResponse]


@router.get("/")
async def get_rustfs_objects(
    status: FileStatus | None = None,
    db: Session = Depends(get_db),
):
    """Отдаёт содержимое rustfs_objects по id.

    Используется воркером features для скачивания файла на обработку,
    без cookie-авторизации."""
    rustfs_objects_list = rustfs_object.fetch_rustfs_objects(status, db)
    return RustfsObjectListResponseData(
        count=len(rustfs_objects_list),
        data=[
            RustfsObjectListResponse.model_validate(rustfs_object)
            for rustfs_object in rustfs_objects_list
        ],
    )


class MessageResponse(BaseModel):
    detail: str
    success: bool


@router.post(
    "/extract-features",
    response_model=MessageResponse,
    dependencies=[Depends(require_admin)],
)
def queue_feature_extraction(
    status: FileStatus = FileStatus.NOT_EXTRACTED,
    db: Session = Depends(get_db),
):
    """Ставит все rustfs_objects со статусом not_extracted
    в очередь features.tasks для воркера features."""
    count = rustfs_object.queue_not_extracted_objects(db, status)
    return MessageResponse(
        detail=f"В очередь отправлено объектов: {count}", success=True
    )


@router.post(
    "/reset-features",
    response_model=MessageResponse,
    dependencies=[Depends(require_admin)],
)
async def reset_features(
    status: FileStatus = FileStatus.EXTRACTED,
    db: Session = Depends(get_db),
):
    """Сбрасывает статус всех rustfs_objects на указанный."""
    count = rustfs_object.reset_features(db, status)
    return MessageResponse(detail=f"Сброшено статусов: {count}", success=True)


internal_router: APIRouter = APIRouter(prefix="/internal", tags=["Internal"])


@internal_router.get("/rustfs-objects/{rustfs_object_id}/content")
async def get_rustfs_object_content(
    rustfs_object_id: int,
    db: Session = Depends(get_db),
):
    """Отдаёт содержимое rustfs_objects по id.

    Используется воркером features для скачивания файла на обработку,
    без cookie-авторизации."""
    rustfs_object_db = rustfs_object.fetch_rustfs_object_by_id(db, rustfs_object_id)
    content_type, _ = mimetypes.guess_type(rustfs_object_db.object_key)
    return await rustfs_object.stream_rustfs_object(
        rustfs_object_db,
        rustfs_object_db.object_key,
        "attachment",
        content_type or "application/octet-stream",
    )


@internal_router.get("/rustfs-objects/{rustfs_object_id}")
async def update_rustfs_object_status(
    rustfs_object_id: int,
    db: Session = Depends(get_db),
):
    rustfs_object.update_rustfs_object(rustfs_object_id, db, FileStatus.EXTRACTING)
    return MessageResponse(detail="Статус обновлен", success=True)
