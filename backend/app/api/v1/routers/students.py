from typing import Any
from pydantic import BaseModel, ConfigDict, field_validator
import uuid
from datetime import timedelta, datetime
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    Security,
    status,
)
from redis import Redis
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.security_deps import (
    get_current_user,
    get_redis,
    refresh_cookie_scheme,
)
from app.models.db import ProjectDB, UserDB
from app.services.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from app.core.config import settings
from app.services.student import (
    fetch_student_db_by_id,
    create_student_in_db,
)

router = APIRouter(prefix="/students", tags=["Students"])


class GetStudentResponse(BaseModel):
    name: str
    description: str
    skills_vector: dict[str, Any]
    created_at: datetime
    updated_at: datetime


@router.get("/{student_id}", response_model=GetStudentResponse)
async def get_student(
    student_id: int,
    db: Session = Depends(get_db),
):
    student = fetch_student_db_by_id(db=db, student_id=student_id)
    return student


class CreateStudentRequest(BaseModel):
    name: str
    description: str
    skills_vector: dict[str, Any]

    @field_validator("name")
    def validate_name(cls, value):
        if len(value) > 255:
            raise HTTPException(
                status_code=400,
                detail="Имя студента не должно превышать 255 символов",
            )
        return value

    @field_validator("description")
    def validate_description(cls, value):
        if len(value) > 1024:
            raise HTTPException(
                status_code=400,
                detail="Описание студента не должно превышать 1024 символов",
            )
        return value

    @field_validator("skills_vector")
    def validate_skills_vector(cls, value):
        if len(value) > 1024:
            raise HTTPException(
                status_code=400,
                detail="Вектор навыков не должен превышать 1024 символов",
            )
        return value


class CreateStudentResponse(BaseModel):
    name: str
    description: str
    skills_vector: dict[str, Any]


@router.post("/", response_model=GetStudentResponse)
async def create_student(
    studentrequest: CreateStudentRequest,
    db: Session = Depends(get_db),
):
    student = create_student_in_db(
        db=db,
        name=studentrequest.name,
        description=studentrequest.description,
        skills_vector=studentrequest.skills_vector,
    )
    return student
