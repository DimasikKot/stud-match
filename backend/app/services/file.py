import hashlib
import io
import logging
import mimetypes
import os
import threading
import zipfile
from typing import BinaryIO

import boto3
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.db import (
    FileDB,
    FileStatus,
    RustfsObjectDB,
    StudentDB,
    StudentFilesDB,
    ZipDB,
    ZipStatus,
)
from botocore.client import Config
from botocore.exceptions import ClientError
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

logger = logging.getLogger(__name__)


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


def _delete_s3_object(object_key: str, bucket: str | None = None) -> None:
    try:
        s3_client.delete_object(Bucket=bucket or settings.RUSTFS_BUCKET, Key=object_key)
    except Exception:
        logger.exception("Не удалось удалить объект %s из RustFS", object_key)


def _get_rustfs_object(
    db: Session, object_key: str, bucket: str
) -> RustfsObjectDB | None:
    return (
        db.query(RustfsObjectDB)
        .filter(
            RustfsObjectDB.object_key == object_key,
            RustfsObjectDB.bucket == bucket,
        )
        .first()
    )


def _is_object_referenced(db: Session, object_key: str, bucket: str) -> bool:
    return _get_rustfs_object(db, object_key, bucket) is not None


def _delete_object_if_unreferenced(db: Session, object_key: str, bucket: str) -> None:
    if not _is_object_referenced(db, object_key, bucket):
        _delete_s3_object(object_key, bucket)


def _delete_rustfs_object_if_orphan(db: Session, rustfs_object: RustfsObjectDB) -> None:
    """Удаляет запись rustfs_objects и сам объект из S3, если на него
    не осталось ссылок в таблице files."""
    remaining = (
        db.query(FileDB.id).filter(FileDB.rustfs_object_id == rustfs_object.id).first()
    )
    if remaining is not None:
        return

    object_key = rustfs_object.object_key
    bucket = rustfs_object.bucket
    db.delete(rustfs_object)
    db.commit()
    _delete_s3_object(object_key, bucket)


def _get_or_create_student(db: Session, fullname: str) -> StudentDB:
    student = db.query(StudentDB).filter(StudentDB.fullname == fullname).first()
    if student is None:
        student = StudentDB(fullname=fullname)
        db.add(student)
        db.flush()
    return student


def upload_zip(
    db: Session,
    fileobj: BinaryIO,
    filename: str,
) -> ZipDB:
    """Принимает zip-архив с работами студентов и сразу возвращает запись зипа.

    Распаковка файлов и загрузка в RustFS выполняются в фоновом потоке,
    статус зипа меняется с processing на completed или failed.
    """
    if not filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Разрешены только zip-архивы")

    fileobj.seek(0)
    data = fileobj.read()
    try:
        with zipfile.ZipFile(io.BytesIO(data)):
            pass
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Файл не является zip-архивом")

    zip_record = ZipDB(name=filename, status=ZipStatus.PROCESSING)
    db.add(zip_record)
    db.commit()
    db.refresh(zip_record)

    threading.Thread(
        target=_process_zip,
        args=(zip_record.id, data),
        daemon=True,
    ).start()

    return zip_record


def _process_zip(zip_id: int, data: bytes) -> None:
    """Распаковывает zip и загружает файлы студентов в RustFS.

    Архив содержит папки вида "ФИО_идентификатор_...", внутри каждой
    папки лежат файлы студента по одной работе (название работы - имя архива).
    Каждый файл загружается в RustFS, для него создаётся запись в files,
    студент создаётся при отсутствии и связывается с файлом в student_files.
    Одинаковые по содержимому файлы (одинаковый sha512) ссылаются на одну
    запись rustfs_objects; extension берётся из первого такого файла.
    """
    db = SessionLocal()
    uploaded_keys: list[str] = []
    try:
        zip_record = db.get(ZipDB, zip_id)
        if zip_record is None:
            return

        try:
            archive = zipfile.ZipFile(io.BytesIO(data))
        except zipfile.BadZipFile:
            zip_record.status = ZipStatus.FAILED
            db.commit()
            return

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

                    file_data = archive.read(info)
                    object_key = hashlib.sha512(file_data).hexdigest()
                    rustfs_object = _get_rustfs_object(
                        db, object_key, settings.RUSTFS_BUCKET
                    )
                    if rustfs_object is None:
                        content_type, _ = mimetypes.guess_type(base_name)
                        s3_client.upload_fileobj(
                            io.BytesIO(file_data),
                            settings.RUSTFS_BUCKET,
                            object_key,
                            ExtraArgs={
                                "ContentType": content_type
                                or "application/octet-stream"
                            },
                        )
                        uploaded_keys.append(object_key)
                        rustfs_object = RustfsObjectDB(
                            object_key=object_key,
                            bucket=settings.RUSTFS_BUCKET,
                            extension=os.path.splitext(base_name)[1].lower(),
                            size=len(file_data),
                            status=FileStatus.EXTRACTED,
                        )
                        db.add(rustfs_object)
                        db.flush()

                    file_record = FileDB(
                        name=base_name,
                        zip_id=zip_id,
                        rustfs_object_id=rustfs_object.id,
                    )
                    db.add(file_record)
                    db.flush()
                    db.add(
                        StudentFilesDB(file_id=file_record.id, student_id=student.id)
                    )
            zip_record.status = ZipStatus.COMPLETED
            db.commit()
        except Exception:
            db.rollback()
            for key in uploaded_keys:
                _delete_object_if_unreferenced(db, key, settings.RUSTFS_BUCKET)
            zip_record = db.get(ZipDB, zip_id)
            if zip_record is not None:
                zip_record.status = ZipStatus.FAILED
                db.commit()
            logger.exception("Ошибка обработки архива %s", zip_id)
    finally:
        db.close()


def fetch_zips(db: Session) -> list[tuple[ZipDB, int]]:
    """Список всех зипов с количеством файлов в каждом."""
    files_count = (
        db.query(func.count(FileDB.id))
        .filter(FileDB.zip_id == ZipDB.id)
        .correlate(ZipDB)
        .scalar_subquery()
    )
    return db.query(ZipDB, files_count.label("files_count")).all()


def fetch_zip_by_id(db: Session, zip_id: int) -> ZipDB:
    zip_record = (
        db.query(ZipDB)
        .options(
            selectinload(ZipDB.files).selectinload(FileDB.students),
            selectinload(ZipDB.files).selectinload(FileDB.rustfs_object),
        )
        .filter(ZipDB.id == zip_id)
        .first()
    )
    if zip_record is None:
        raise HTTPException(status_code=404, detail=f"Архив {zip_id} не найден")
    return zip_record


def delete_zip_by_id(db: Session, zip_id: int) -> None:
    """Удаляет зип и его файлы из БД.

    Записи rustfs_objects и сами объекты в RustFS удаляются только
    если на них не осталось ссылок в таблице files.
    Студенты не удаляются, они остаются даже без файлов.
    """
    zip_record = fetch_zip_by_id(db, zip_id)

    files = db.query(FileDB).filter(FileDB.zip_id == zip_id).all()
    rustfs_objects = {file_db.rustfs_object for file_db in files}

    db.delete(zip_record)
    db.commit()

    for rustfs_object in rustfs_objects:
        _delete_rustfs_object_if_orphan(db, rustfs_object)


def fetch_file_by_id(db: Session, file_id: int) -> FileDB:
    file_db = (
        db.query(FileDB)
        .options(selectinload(FileDB.rustfs_object))
        .filter(FileDB.id == file_id)
        .first()
    )
    if file_db is None:
        raise HTTPException(status_code=404, detail=f"Файл {file_id} не найден")
    return file_db


def fetch_files(db: Session) -> list[FileDB]:
    """Список всех файлов с привязанными студентами."""
    return (
        db.query(FileDB)
        .options(
            selectinload(FileDB.students),
            selectinload(FileDB.rustfs_object),
        )
        .order_by(FileDB.id.desc())
        .all()
    )


def fetch_files_by_hash(db: Session) -> list[FileDB]:
    """Список всех файлов, сгруппированных по rustfs-объекту (sha512),
    у которых в names разные extension."""
    files = (
        db.query(FileDB)
        .options(
            selectinload(FileDB.students),
            selectinload(FileDB.rustfs_object),
        )
        .order_by(FileDB.rustfs_object_id)
        .all()
    )

    result = set()

    for i in range(len(files) - 1):
        if (
            files[i].rustfs_object_id == files[i + 1].rustfs_object_id
            and os.path.splitext(files[i].name)[1].lower()
            != os.path.splitext(files[i + 1].name)[1].lower()
        ):
            result.add(files[i])
            result.add(files[i + 1])

    return list(result)


def fetch_rustfs_object_by_id(db: Session, rustfs_object_id: int) -> RustfsObjectDB:
    rustfs_object = db.get(RustfsObjectDB, rustfs_object_id)
    if rustfs_object is None:
        raise HTTPException(
            status_code=404, detail=f"Объект {rustfs_object_id} не найден"
        )
    return rustfs_object


def get_rustfs_object_file(rustfs_object: RustfsObjectDB) -> dict:
    """Возвращает ответ S3 get_object для записи rustfs_objects
    (содержит Body - StreamingBody)."""
    try:
        return s3_client.get_object(
            Bucket=rustfs_object.bucket,
            Key=rustfs_object.object_key,
        )
    except ClientError as exc:
        code = str(exc.response.get("Error", {}).get("Code", ""))
        if code in ("NoSuchKey", "NoSuchBucket", "404", "NotFound"):
            raise HTTPException(status_code=404, detail="Файл не найден в хранилище")
        raise HTTPException(status_code=502, detail=f"RustFS error: {exc}")


def get_file_object(file_db: FileDB) -> dict:
    """Возвращает ответ S3 get_object (содержит Body - StreamingBody)."""
    return get_rustfs_object_file(file_db.rustfs_object)


def guess_content_type(file_db: FileDB) -> str:
    content_type, _ = mimetypes.guess_type(file_db.name)
    return content_type or "application/octet-stream"


def delete_file_by_id(db: Session, file_id: int) -> None:
    file_db = fetch_file_by_id(db, file_id)
    rustfs_object = file_db.rustfs_object

    db.delete(file_db)
    db.commit()

    _delete_rustfs_object_if_orphan(db, rustfs_object)
