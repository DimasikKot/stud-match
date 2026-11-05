from typing import Any
from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.student import (
    delete_student_by_id,
    fetch_all_students,
    fetch_student_db_by_id,
    create_student_in_db,
    update_student_by_id,
    SortType,
)

router = APIRouter(prefix="/students", tags=["Students"])


class GetStudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
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


class UpdateStudentRequest(BaseModel):
    name: str | None
    description: str | None
    skills_vector: dict[str, Any] | None

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


class UpdateStudentResponse(BaseModel):
    name: str
    description: str
    skills_vector: dict[str, Any]


@router.patch("/{student_id}", response_model=UpdateStudentResponse)
async def update_student(
    student_id: int,
    studentrequest: UpdateStudentRequest,
    db: Session = Depends(get_db),
):
    student = update_student_by_id(
        student_id=student_id,
        db=db,
        new_name=studentrequest.name,
        new_description=studentrequest.description,
        new_skills_vector=studentrequest.skills_vector,
    )
    return student


class GetAllStudentsResponse(BaseModel):
    data: list[GetStudentResponse]


@router.get("/", response_model=GetAllStudentsResponse)
async def get_all_students(
    sort: SortType | None = Query(
        "created_at_desc",
        description="Сортировка: name_asc, name_desc, created_at_asc, created_at_desc, updated_at_asc, updated_at_desc",
    ),
    search: str | None = Query(
        None,
        description="Поиск по названию проекта",
    ),
    db: Session = Depends(get_db),
):
    students = fetch_all_students(db=db, sort=sort, search=search)
    return GetAllStudentsResponse(
        data=[GetStudentResponse.model_validate(student) for student in students]
    )


class GetEchoResponse(BaseModel):
    detail: str
    success: bool


@router.delete("/{student_id}", response_model=GetEchoResponse)
async def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
):
    delete_student_by_id(db=db, student_id=student_id)
    return GetEchoResponse(detail="Студент успешно удален!", success=True)
