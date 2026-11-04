import shutil
from pathlib import Path
from typing import Literal
from fastapi import HTTPException
from pydantic import field_validator
from sqlalchemy.orm import Session
from typing import Any
from app.core.config import settings
from app.models.db import ProjectDB, StudentDB, UserDB
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    Security,
    status,
)
from app.services.security_deps import (
    get_current_user,
    get_redis,
    refresh_cookie_scheme,
)


def fetch_student_db_by_id(db: Session, student_id: int):
    return db.query(StudentDB).filter(StudentDB.id == student_id).first()


def create_student_in_db(
    db: Session,
    name: str,
    description: str,
    skills_vector: dict[str, Any],
) -> StudentDB:
    student_db: StudentDB = StudentDB(
        name=name, description=description, skills_vector=skills_vector
    )

    db.add(student_db)
    db.commit()
    db.refresh(student_db)

    return student_db
