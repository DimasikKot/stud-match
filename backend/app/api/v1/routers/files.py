from datetime import datetime
from urllib.parse import quote

from fastapi import (
    APIRouter,
    Depends,
    File,
    UploadFile,
)
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.core.database import get_db
from app.models.db import FileDB
from app.services import file as file_service
from app.services.security_deps import require_admin

router: APIRouter = APIRouter(
    prefix="/files", tags=["Files"], dependencies=[Depends(require_admin)]
)


class FileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    object_key: str
    path: str
    size: int
    created_at: datetime
    updated_at: datetime


class FileListResponse(BaseModel):
    data: list[FileResponse]


class MessageResponse(BaseModel):
    success: bool
    detail: str


def _content_disposition(disposition: str, filename: str) -> str:
    """Content-Disposition с поддержкой не-ASCII имён (RFC 5987)."""
    return f"{disposition}; filename*=UTF-8''{quote(filename)}"


async def _stream_file(file_db: FileDB, disposition: str) -> StreamingResponse:
    """Отдаёт файл из RustFS/S3 потоком."""
    s3_response = await run_in_threadpool(file_service.get_file_object, file_db)
    body = s3_response["Body"]

    def iterator():
        try:
            while chunk := body.read(64 * 1024):
                yield chunk
        finally:
            body.close()

    headers = {
        "Content-Disposition": _content_disposition(disposition, file_db.name),
    }
    content_length = s3_response.get("ContentLength")
    if content_length is not None:
        headers["Content-Length"] = str(content_length)

    return StreamingResponse(
        iterator(),
        media_type=file_service.guess_content_type(file_db),
        headers=headers,
    )


@router.post("/", response_model=list[FileResponse])
async def upload_files(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    """Загружает один или несколько файлов (multipart/form-data, поле `files`)."""
    try:
        results = []
        for file in files:
            results.append(
                await run_in_threadpool(
                    file_service.upload_file,
                    db,
                    file.file,
                    file.filename or "file",
                    file.content_type or "application/octet-stream",
                )
            )
        return results
    finally:
        for file in files:
            await file.close()


@router.get("/", response_model=FileListResponse)
def list_files(db: Session = Depends(get_db)):
    files = file_service.fetch_files(db)
    return FileListResponse(data=[FileResponse.model_validate(file) for file in files])


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


@router.delete("/{file_id}", response_model=MessageResponse)
def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
):
    file_service.delete_file_by_id(db, file_id)
    return MessageResponse(detail="Файл успешно удален!", success=True)
