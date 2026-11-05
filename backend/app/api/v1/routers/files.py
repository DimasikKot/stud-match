import uuid
import os
from datetime import datetime
from typing import Any
from sqlalchemy.orm import Session
from botocore.exceptions import ClientError
from fastapi import (
    APIRouter,
    Depends,
    File,
    UploadFile,
    HTTPException,
)
from pydantic import BaseModel, ConfigDict
from starlette.concurrency import run_in_threadpool

from app.core.database import get_db
from app.models.db import FileDB
from app.services.file import s3_client
from app.core.config import settings

router: APIRouter = APIRouter(prefix="/files", tags=["Files"])


class UploadFileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str
    object_key: str
    original_filename: str
    download_url: str


@router.post("/", response_model=UploadFileResponse)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    original_name = file.filename or "file"
    ext = os.path.splitext(original_name)[1]
    object_key = f"{uuid.uuid4()}{ext}"

    try:
        await run_in_threadpool(
            s3_client.upload_fileobj,
            file.file,
            settings.RUSTFS_BUCKET,
            object_key,
            ExtraArgs={
                "ContentType": file.content_type or "application/octet-stream",
            },
        )
    except ClientError as exc:
        raise HTTPException(status_code=502, detail=f"RustFS error: {exc}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Upload failed: {exc}")
    finally:
        await file.close()

    # Сохраняем метаданные в БД
    file_record = FileDB(
        name=original_name,
        object_key=object_key,
        path=settings.RUSTFS_BUCKET,
    )
    try:
        db.add(file_record)
        db.commit()
        db.refresh(file_record)
    except Exception as exc:
        db.rollback()
        # Откатываем загрузку в S3, чтобы не оставлять «сиротский» объект
        try:
            await run_in_threadpool(
                s3_client.delete_object,
                Bucket=settings.RUSTFS_BUCKET,
                Key=object_key,
            )
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"DB error: {exc}")

    return file_record
