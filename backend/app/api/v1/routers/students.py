from typing import Any

from app.core.database import get_db
from app.services.get_user import require_admin
from app.services.student import (
    SortType,
    create_student_in_db,
    delete_student_by_id,
    fetch_all_students,
    fetch_student_db_by_id,
    update_student_by_id,
)
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/students", tags=["Students"], dependencies=[Depends(require_admin)]
)


class CreateStudentRequest(BaseModel):
    fullname: str

    @field_validator("fullname")
    def validate_fullname(cls, value):
        if len(value) > 255:
            raise HTTPException(
                status_code=400,
                detail="ФИО студента не должно превышать 255 символов",
            )
        return value


class CreateStudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: int
    fullname: str
    skills_set: dict[str, Any]
    model_version: str


@router.post("/", response_model=CreateStudentResponse)
async def create_student(
    student: CreateStudentRequest,
    db: Session = Depends(get_db),
):
    student_db = create_student_in_db(db=db, fullname=student.fullname)
    return student_db


class GetListStudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fullname: str


class GetListStudentsResponse(BaseModel):
    data: list[GetListStudentResponse]


@router.get("/", response_model=GetListStudentsResponse)
async def get_all_students(
    sort: SortType | None = Query(
        None,
        description="Сортировка: fullname_asc, fullname_desc",
    ),
    search: str | None = Query(
        None,
        description="Поиск по ФИО студента",
    ),
    db: Session = Depends(get_db),
):
    students = fetch_all_students(db=db, sort=sort, search=search)
    return GetListStudentsResponse(
        data=[GetListStudentResponse.model_validate(student) for student in students]
    )


class GetStudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: int
    fullname: str
    skills_set: dict[str, Any]
    model_version: str


@router.get("/{student_id}", response_model=GetStudentResponse)
async def get_student(
    student_id: int,
    db: Session = Depends(get_db),
):
    student_db = fetch_student_db_by_id(db=db, student_id=student_id)
    if student_db is None:
        raise HTTPException(status_code=404, detail="студент не найден")
    return GetStudentResponse.model_validate(student_db)


class UpdateStudentRequest(CreateStudentRequest):
    model_config = ConfigDict(protected_namespaces=())

    skills_set: dict[str, Any] | None = None
    model_version: str | None = None


class UpdateStudentResponse(CreateStudentResponse):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    skills_set: dict[str, Any]
    model_version: str


@router.patch("/{student_id}", response_model=UpdateStudentResponse)
async def update_student(
    student_id: int,
    student: UpdateStudentRequest,
    db: Session = Depends(get_db),
):
    student_db = update_student_by_id(
        student_id=student_id,
        db=db,
        new_fullname=student.fullname,
        new_skills_set=student.skills_set,
        new_model_version=student.model_version,
    )
    return UpdateStudentResponse.model_validate(student_db)


class GetEchoResponse(BaseModel):
    success: bool
    detail: str


@router.delete("/{student_id}", response_model=GetEchoResponse)
async def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
):
    delete_student_by_id(db=db, student_id=student_id)
    return GetEchoResponse(detail="Студент успешно удален!", success=True)
