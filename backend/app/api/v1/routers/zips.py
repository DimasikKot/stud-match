from datetime import datetime

from app.core.database import get_db
from app.services import file as file_service
from app.services.get_user import require_admin
from fastapi import (
    APIRouter,
    Depends,
    File,
    UploadFile,
)
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

router: APIRouter = APIRouter(
    prefix="/zips", tags=["Zips"], dependencies=[Depends(require_admin)]
)


class ZipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    status: str
    date: datetime
    files_count: int = 0


class ZipListResponse(BaseModel):
    data: list[ZipResponse]


class ZipFileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    size: int
    status: str
    student_fullname: str | None = None


class ZipDetailResponse(ZipResponse):
    files: list[ZipFileResponse] = []


class MessageResponse(BaseModel):
    success: bool
    detail: str


@router.post("/", response_model=list[ZipResponse])
async def upload_zips(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    """Загружает zip-архивы и сразу отвечает, распаковка идёт в фоне."""
    try:
        results = []
        for file in files:
            zip_record = await run_in_threadpool(
                file_service.upload_zip,
                db,
                file.file,
                file.filename or "file",
            )
            results.append(
                ZipResponse(
                    id=zip_record.id,
                    name=zip_record.name,
                    status=zip_record.status.value,
                    date=zip_record.date,
                    files_count=0,
                )
            )
        return results
    finally:
        for file in files:
            await file.close()


@router.get("/", response_model=ZipListResponse)
def list_zips(db: Session = Depends(get_db)):
    rows = file_service.fetch_zips(db)
    return ZipListResponse(
        data=[
            ZipResponse(
                id=zip_record.id,
                name=zip_record.name,
                status=zip_record.status.value,
                date=zip_record.date,
                files_count=files_count,
            )
            for zip_record, files_count in rows
        ]
    )


@router.get("/{zip_id}", response_model=ZipDetailResponse)
def get_zip(
    zip_id: int,
    db: Session = Depends(get_db),
):
    zip_record = file_service.fetch_zip_by_id(db, zip_id)
    return ZipDetailResponse(
        id=zip_record.id,
        name=zip_record.name,
        status=zip_record.status.value,
        date=zip_record.date,
        files_count=len(zip_record.files),
        files=[ZipFileResponse.model_validate(file_db) for file_db in zip_record.files],
    )


@router.delete("/{zip_id}", response_model=MessageResponse)
def delete_zip(
    zip_id: int,
    db: Session = Depends(get_db),
):
    file_service.delete_zip_by_id(db, zip_id)
    return MessageResponse(detail="Архив успешно удален!", success=True)
