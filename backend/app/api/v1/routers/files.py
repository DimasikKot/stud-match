import mimetypes
from urllib.parse import quote

from app.core.database import get_db
from app.core.db import FileDB, RustfsObjectDB
from app.services import features as features_service
from app.services import file as file_service
from app.services.get_user import require_admin
from fastapi import (
    APIRouter,
    Depends,
)
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

router: APIRouter = APIRouter(
    prefix="/files", tags=["Files"], dependencies=[Depends(require_admin)]
)


class FileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: int
    name: str
    size: int
    rustfs_object_key: str
    rustfs_bucket: str
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
        rustfs_object_key=rustfs_object.object_key,
        rustfs_bucket=rustfs_object.bucket,
        status=rustfs_object.status.value,
        feature_set=rustfs_object.feature_set,
        model_version=rustfs_object.model_version,
        zip_id=file_db.zip_id,
        student_fullname=file_db.student_fullname,
    )


def _content_disposition(disposition: str, filename: str) -> str:
    """Content-Disposition с поддержкой не-ASCII имён (RFC 5987)."""
    return f"{disposition}; filename*=UTF-8''{quote(filename)}"


async def _stream_rustfs_object(
    rustfs_object: RustfsObjectDB,
    filename: str,
    disposition: str,
    media_type: str,
) -> StreamingResponse:
    """Отдаёт объект из RustFS/S3 потоком."""
    s3_response = await run_in_threadpool(
        file_service.get_rustfs_object_file, rustfs_object
    )
    body = s3_response["Body"]

    def iterator():
        try:
            while chunk := body.read(64 * 1024):
                yield chunk
        finally:
            body.close()

    headers = {
        "Content-Disposition": _content_disposition(disposition, filename),
    }
    content_length = s3_response.get("ContentLength")
    if content_length is not None:
        headers["Content-Length"] = str(content_length)

    return StreamingResponse(
        iterator(),
        media_type=media_type,
        headers=headers,
    )


async def _stream_file(file_db: FileDB, disposition: str) -> StreamingResponse:
    """Отдаёт файл из RustFS/S3 потоком."""
    return await _stream_rustfs_object(
        file_db.rustfs_object,
        file_db.name,
        disposition,
        file_service.guess_content_type(file_db),
    )


@router.get("/", response_model=FileListResponse, dependencies=[Depends(require_admin)])
def list_files(db: Session = Depends(get_db)):
    files = file_service.fetch_files(db)
    return FileListResponse(data=[_file_response(file) for file in files])


@router.get(
    "/by-hash", response_model=FileListResponse, dependencies=[Depends(require_admin)]
)
def list_files_by_hash(db: Session = Depends(get_db)):
    files = file_service.fetch_files_by_hash(db)
    return FileListResponse(data=[_file_response(file) for file in files])


@router.get("/{file_id}/view")
async def view_file(
    file_id: int,
    db: Session = Depends(get_db),
):
    """Просмотр файла inline (браузер откроет его, не скачивая)."""
    file_db = file_service.fetch_file_by_id(db, file_id)
    return await _stream_file(file_db, "inline")


@router.get("/{file_id}/download")
async def download_file(
    file_id: int,
    db: Session = Depends(get_db),
):
    """Скачивание файла как вложения (attachment)."""
    file_db = file_service.fetch_file_by_id(db, file_id)
    return await _stream_file(file_db, "attachment")


@router.post("/extract-features", response_model=MessageResponse)
def queue_feature_extraction(
    db: Session = Depends(get_db),
):
    """Ставит все rustfs_objects со статусом not_extracted
    в очередь features.tasks для воркера features."""
    count = features_service.queue_not_extracted_objects(db)
    return MessageResponse(
        detail=f"В очередь отправлено объектов: {count}", success=True
    )


@router.delete(
    "/{file_id}", response_model=MessageResponse, dependencies=[Depends(require_admin)]
)
def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
):
    file_service.delete_file_by_id(db, file_id)
    return MessageResponse(detail="Файл успешно удален!", success=True)


internal_router: APIRouter = APIRouter(prefix="/internal", tags=["Internal"])


@internal_router.get("/rustfs-objects/{rustfs_object_id}/content")
async def get_rustfs_object_content(
    rustfs_object_id: int,
    db: Session = Depends(get_db),
):
    """Отдаёт содержимое rustfs_objects по id.

    Используется воркером features для скачивания файла на обработку,
    без cookie-авторизации."""
    rustfs_object = file_service.fetch_rustfs_object_by_id(db, rustfs_object_id)
    content_type, _ = mimetypes.guess_type(rustfs_object.object_key)
    return await _stream_rustfs_object(
        rustfs_object,
        rustfs_object.object_key,
        "attachment",
        content_type or "application/octet-stream",
    )
