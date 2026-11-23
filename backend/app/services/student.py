from typing import Literal
from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import Any
from app.models.db import StudentDB
from fastapi import HTTPException


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


def update_student_by_id(
    student_id: int,
    db: Session,
    new_name: str | None,
    new_description: str | None,
    new_skills_vector: dict[str, Any] | None,
) -> StudentDB:
    student_db = fetch_student_db_by_id(db=db, student_id=student_id)

    if student_db is None:
        raise HTTPException(status_code=404, detail="студент не найден")

    if new_name is not None:
        student_db.name = new_name

    if new_description is not None:
        student_db.description = new_description

    if new_skills_vector is not None:
        student_db.skills_vector = new_skills_vector

    db.commit()
    db.refresh(student_db)

    return student_db


SortType = Literal[
    "name_asc",
    "name_desc",
    "created_at_asc",
    "created_at_desc",
    "updated_at_asc",
    "updated_at_desc",
]


def fetch_all_students(
    db: Session,
    sort: SortType | None,
    search: str | None,
) -> list[StudentDB]:
    """Получение списка студентов"""

    student_db = db.query(StudentDB)

    if search is not None:
        student_db = student_db.filter(StudentDB.name.ilike(f"%{search}%"))

    if sort == "name_asc":
        student_db = student_db.order_by(StudentDB.name.asc())
    elif sort == "name_desc":
        student_db = student_db.order_by(StudentDB.name.desc())
    elif sort == "created_at_asc":
        student_db = student_db.order_by(StudentDB.created_at.asc())
    elif sort == "created_at_desc":
        student_db = student_db.order_by(StudentDB.created_at.desc())
    elif sort == "updated_at_asc":
        student_db = student_db.order_by(StudentDB.updated_at.asc())
    elif sort == "updated_at_desc":
        student_db = student_db.order_by(StudentDB.updated_at.desc())

    return student_db.all()


def delete_student_by_id(db: Session, student_id: int) -> None:
    student_db = fetch_student_db_by_id(db=db, student_id=student_id)
    if student_db is None:
        raise HTTPException(status_code=404, detail="студент не найден")
    db.delete(student_db)
    db.commit()
