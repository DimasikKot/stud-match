from typing import Any, Literal

from app.core.db import StudentDB
from fastapi import HTTPException
from sqlalchemy.orm import Session


def fetch_student_db_by_id(db: Session, student_id: int):
    return db.query(StudentDB).filter(StudentDB.id == student_id).first()


def create_student_in_db(
    db: Session,
    fullname: str,
) -> StudentDB:
    student_db: StudentDB = StudentDB(fullname=fullname)

    db.add(student_db)
    db.commit()
    db.refresh(student_db)

    return student_db


def update_student_by_id(
    student_id: int,
    db: Session,
    new_fullname: str | None,
    new_skills_set: dict[str, Any] | None,
    new_model_version: str | None = None,
) -> StudentDB:
    student_db = fetch_student_db_by_id(db=db, student_id=student_id)

    if student_db is None:
        raise HTTPException(status_code=404, detail="студент не найден")

    if new_fullname is not None:
        student_db.fullname = new_fullname

    if new_skills_set is not None:
        student_db.skills_set = new_skills_set

    if new_model_version is not None:
        student_db.model_version = new_model_version

    db.commit()
    db.refresh(student_db)

    return student_db


SortType = Literal[
    "fullname_asc",
    "fullname_desc",
]


def fetch_all_students(
    db: Session,
    sort: SortType | None,
    search: str | None,
) -> list[StudentDB]:
    """Получение списка студентов"""

    student_db = db.query(StudentDB)

    if search is not None:
        student_db = student_db.filter(StudentDB.fullname.ilike(f"%{search}%"))

    if sort == "fullname_asc":
        student_db = student_db.order_by(StudentDB.fullname.asc())
    elif sort == "fullname_desc":
        student_db = student_db.order_by(StudentDB.fullname.desc())

    return student_db.all()


def delete_student_by_id(db: Session, student_id: int) -> None:
    student_db = fetch_student_db_by_id(db=db, student_id=student_id)
    if student_db is None:
        raise HTTPException(status_code=404, detail="студент не найден")
    db.delete(student_db)
    db.commit()
