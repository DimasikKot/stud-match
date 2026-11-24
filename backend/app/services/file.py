import io
import mimetypes
import os
import uuid
import zipfile
from typing import BinaryIO

import boto3
from app.core.config import settings
from app.models.db import FileDB, StudentDB, StudentFilesDB, ZipDB
from botocore.client import Config
from botocore.exceptions import ClientError
from fastapi import HTTPException
from sqlalchemy.orm import Session


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


def _get_or_create_student(db: Session, fullname: str) -> StudentDB:
    student = db.query(StudentDB).filter(StudentDB.fullname == fullname).first()
    if student is None:
        student = StudentDB(fullname=fullname, skills_vector={})
        db.add(student)
        db.flush()
    return student


def upload_zip(
    db: Session,
    fileobj: BinaryIO,
    filename: str,
) -> list[FileDB]:
    """Распаковывает zip-архив с работами студентов.

    Архив содержит папки вида "ФИО_идентификатор_...", внутри каждой
    папки лежат файлы студента по одной работе (название работы - имя архива).
    Каждый файл загружается в RustFS, для него создаётся запись в files,
    студент создаётся при отсутствии и связывается с файлом в student_files.
    """
    if not filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Разрешены только zip-архивы")

    fileobj.seek(0)
    try:
        archive = zipfile.ZipFile(fileobj)
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Файл не является zip-архивом")

    zip_record = ZipDB(name=filename)
    db.add(zip_record)
    db.flush()

    uploaded_keys: list[str] = []
    file_records: list[FileDB] = []
    try:
        with archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                entry_name = info.filename.replace("\\", "/")
                parts = entry_name.split("/")
                if len(parts) < 2 or parts[0] == "__MACOSX":
                    continue
                base_name = parts[-1]
                if not base_name:
                    continue

                folder_name = parts[0]
                fullname = folder_name.split("_", 1)[0].strip() or folder_name
                student = _get_or_create_student(db, fullname)

                data = archive.read(info)
                ext = os.path.splitext(base_name)[1]
                object_key = f"{uuid.uuid4()}{ext}"
                content_type, _ = mimetypes.guess_type(base_name)
                s3_client.upload_fileobj(
                    io.BytesIO(data),
                    settings.RUSTFS_BUCKET,
                    object_key,
                    ExtraArgs={
                        "ContentType": content_type or "application/octet-stream"
                    },
                )
                uploaded_keys.append(object_key)

                file_record = FileDB(
                    name=base_name,
                    rustfs_object_key=object_key,
                    rustfs_bucket=settings.RUSTFS_BUCKET,
                    size=info.file_size,
                    work_zip_id=zip_record.id,
                )
                db.add(file_record)
                db.flush()
                file_records.append(file_record)
                db.add(StudentFilesDB(file_id=file_record.id, student_id=student.id))
        db.commit()
    except ClientError as exc:
        db.rollback()
        for key in uploaded_keys:
            _delete_s3_object(key)
        raise HTTPException(status_code=502, detail=f"RustFS error: {exc}")
    except HTTPException:
        db.rollback()
        for key in uploaded_keys:
            _delete_s3_object(key)
        raise
    except Exception as exc:
        db.rollback()
        for key in uploaded_keys:
            _delete_s3_object(key)
        raise HTTPException(status_code=500, detail=f"Upload failed: {exc}")

    return file_records


def fetch_file_by_id(db: Session, file_id: int) -> FileDB:
    file_db = db.query(FileDB).filter(FileDB.id == file_id).first()
    if file_db is None:
        raise HTTPException(status_code=404, detail=f"Файл {file_id} не найден")
    return file_db


def fetch_files(db: Session) -> list[FileDB]:
    """Список всех файлов, отсортированный по дате работы (новые первыми)."""
    return db.query(FileDB).all()


def get_file_object(file_db: FileDB) -> dict:
    """Возвращает ответ S3 get_object (содержит Body - StreamingBody)."""
    try:
        return s3_client.get_object(
            Bucket=file_db.rustfs_bucket,
            Key=file_db.rustfs_object_key,
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
        s3_client.delete_object(
            Bucket=file_db.rustfs_bucket, Key=file_db.rustfs_object_key
        )
    except ClientError as exc:
        raise HTTPException(status_code=502, detail=f"RustFS error: {exc}")

    db.delete(file_db)
    db.commit()
