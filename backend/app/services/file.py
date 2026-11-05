import mimetypes
import os
import uuid
from typing import BinaryIO

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.db import FileDB


def create_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.RUSTFS_URL,
        aws_access_key_id=settings.RUSTFS_ACCESS_KEY,
        aws_secret_access_key=settings.RUSTFS_SECRET_KEY,
        region_name=settings.RUSTFS_REGION,
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},  # Обязательно для RustFS
        ),
        verify=False,  # отключаем проверку TLS для botocore
    )


s3_client = create_s3_client()


def _delete_s3_object(object_key: str) -> None:
    try:
        s3_client.delete_object(Bucket=settings.RUSTFS_BUCKET, Key=object_key)
    except Exception:
        pass


def upload_file(
    db: Session,
    fileobj: BinaryIO,
    filename: str,
    content_type: str,
) -> FileDB:
    """Загружает файл в RustFS/S3 и сохраняет запись о нём в БД."""
    ext = os.path.splitext(filename)[1]
    object_key = f"{uuid.uuid4()}{ext}"

    fileobj.seek(0, os.SEEK_END)
    size = fileobj.tell()
    fileobj.seek(0)

    try:
        s3_client.upload_fileobj(
            fileobj,
            settings.RUSTFS_BUCKET,
            object_key,
            ExtraArgs={"ContentType": content_type},
        )
    except ClientError as exc:
        raise HTTPException(status_code=502, detail=f"RustFS error: {exc}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Upload failed: {exc}")

    file_record = FileDB(
        name=filename,
        object_key=object_key,
        path=settings.RUSTFS_BUCKET,
        size=size,
    )
    try:
        db.add(file_record)
        db.commit()
        db.refresh(file_record)
    except Exception as exc:
        db.rollback()
        _delete_s3_object(object_key)
        raise HTTPException(status_code=500, detail=f"DB error: {exc}")

    return file_record


def fetch_file_by_id(db: Session, file_id: int) -> FileDB:
    file_db = db.query(FileDB).filter(FileDB.id == file_id).first()
    if file_db is None:
        raise HTTPException(status_code=404, detail=f"Файл {file_id} не найден")
    return file_db


def fetch_files(db: Session) -> list[FileDB]:
    """Список всех файлов, отсортированный по дате создания (новые первыми)."""
    return db.query(FileDB).order_by(FileDB.created_at.desc()).all()


def get_file_object(file_db: FileDB) -> dict:
    """Возвращает ответ S3 get_object (содержит Body — StreamingBody)."""
    try:
        return s3_client.get_object(
            Bucket=settings.RUSTFS_BUCKET,
            Key=file_db.object_key,
        )
    except ClientError as exc:
        code = str(exc.response.get("Error", {}).get("Code", ""))
        if code in ("NoSuchKey", "NoSuchBucket", "404", "NotFound"):
            raise HTTPException(status_code=404, detail="Файл не найден в хранилище")
        raise HTTPException(status_code=502, detail=f"RustFS error: {exc}")


def guess_content_type(file_db: FileDB) -> str:
    content_type, _ = mimetypes.guess_type(file_db.name)
    return content_type or "application/octet-stream"


def delete_file_by_id(db: Session, file_id: int) -> None:
    file_db = fetch_file_by_id(db, file_id)

    try:
        s3_client.delete_object(Bucket=settings.RUSTFS_BUCKET, Key=file_db.object_key)
    except ClientError as exc:
        raise HTTPException(status_code=502, detail=f"RustFS error: {exc}")

    db.delete(file_db)
    db.commit()
