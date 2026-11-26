from app.core.database import get_db
from app.core.db import FileDB
from app.services import file, rustfs_object
from app.services.get_user import require_admin
from fastapi import (
    APIRouter,
    Depends,
)
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

router: APIRouter = APIRouter(
    prefix="/files", tags=["Files"], dependencies=[Depends(require_admin)]
)


class FileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: int
    name: str
    size: int
    status: str
    feature_set: dict
    model_version: str
    zip_id: int
    student_fullname: str | None = None


class FileListResponse(BaseModel):
    data: list[FileResponse]


class MessageResponse(BaseModel):
    success: bool
    detail: str


def _file_response(file_db: FileDB) -> FileResponse:
    rustfs_object = file_db.rustfs_object
    return FileResponse(
        id=file_db.id,
        name=file_db.name,
        size=rustfs_object.size,
        status=rustfs_object.status.value,
        feature_set=rustfs_object.feature_set,
        model_version=rustfs_object.model_version,
        zip_id=file_db.zip_id,
        student_fullname=file_db.student_fullname,
    )


@router.get("/", response_model=FileListResponse, dependencies=[Depends(require_admin)])
def list_files(db: Session = Depends(get_db)):
    files = file.fetch_files(db)
    return FileListResponse(data=[_file_response(file) for file in files])


@router.get(
    "/duplicate-hash-different-extensions",
    response_model=FileListResponse,
    dependencies=[Depends(require_admin)],
)
def list_files_by_hash(db: Session = Depends(get_db)):
    files = file.fetch_files_duplicate_hash_and_different_extensions(db)
    return FileListResponse(data=[_file_response(file) for file in files])


@router.get("/{file_id}/view")
async def view_file(
    file_id: int,
    db: Session = Depends(get_db),
):
    """Просмотр файла inline (браузер откроет его, не скачивая)."""
    file_db = file.fetch_file_by_id(db, file_id)
    return await rustfs_object.stream_file(file_db, "inline")


@router.get("/{file_id}/download")
async def download_file(
    file_id: int,
    db: Session = Depends(get_db),
):
    """Скачивание файла как вложения (attachment)."""
    file_db = file.fetch_file_by_id(db, file_id)
    return await rustfs_object.stream_file(file_db, "attachment")


@router.delete(
    "/{file_id}", response_model=MessageResponse, dependencies=[Depends(require_admin)]
)
def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
):
    file.delete_file_by_id(db, file_id)
    return MessageResponse(detail="Файл успешно удален!", success=True)
