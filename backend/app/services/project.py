import shutil
from pathlib import Path
from typing import Literal
from fastapi import HTTPException
from pydantic import field_validator
from sqlalchemy.orm import Session
from typing import Any
from app.core.config import settings
from app.models.db import UserDB, ProjectDB
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


def is_owner_of_project(project_id: int, user_id: int, db: Session) -> None:
    """Проверяет, является ли пользователь владельцем проекта"""

    project_db = db.query(ProjectDB).filter(ProjectDB.id == project_id).first()

    if project_db is None:
        raise HTTPException(status_code=404, detail=f"Проект {project_id} не найден")

    if project_db.user_id != user_id:
        raise HTTPException(
            status_code=403, detail=f"Нет доступа к проекту {project_id}"
        )


SortType = Literal[
    "name_asc",
    "name_desc",
    "created_at_asc",
    "created_at_desc",
    "updated_at_asc",
    "updated_at_desc",
]


def create_project(
    user_id: int,
    db: Session,
    name: str,
    description: str,
    skills_vector: dict[str, Any],
) -> ProjectDB:
    project_db: ProjectDB = ProjectDB(
        name=name, user_id=user_id, description=description, skills_vector=skills_vector
    )
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    db.add(project_db)
    db.commit()
    db.refresh(project_db)

    return project_db


def fetch_projects_by_user_id(
    user_id: int,
    db: Session,
    sort: SortType | None,
    search: str | None,
) -> list[ProjectDB]:
    """Получение списка проектов пользователя по его id"""

    projects_db = db.query(ProjectDB).filter(ProjectDB.user_id == user_id)

    if search is not None:
        projects_db = projects_db.filter(ProjectDB.name.ilike(f"%{search}%"))

    if sort == "name_asc":
        projects_db = projects_db.order_by(ProjectDB.name.asc())
    elif sort == "name_desc":
        projects_db = projects_db.order_by(ProjectDB.name.desc())
    elif sort == "created_at_asc":
        projects_db = projects_db.order_by(ProjectDB.created_at.asc())
    elif sort == "created_at_desc":
        projects_db = projects_db.order_by(ProjectDB.created_at.desc())
    elif sort == "updated_at_asc":
        projects_db = projects_db.order_by(ProjectDB.updated_at.asc())
    elif sort == "updated_at_desc":
        projects_db = projects_db.order_by(ProjectDB.updated_at.desc())

    return projects_db.all()


def fetch_project_db_by_id(project_id: int, user_id: int, db: Session) -> ProjectDB:
    """Получение проекта по его id"""
    is_owner_of_project(project_id, user_id, db)
    project_db = db.query(ProjectDB).filter(ProjectDB.id == project_id).first()

    if not project_db:
        raise HTTPException(status_code=404, detail="Проект не найден")

    return project_db


def update_project_by_id(
    project_id: int,
    user_id: int,
    db: Session,
    new_name: str | None,
    new_description: str | None,
    new_skills_vector: dict[str, Any] | None,
) -> ProjectDB:
    project_db = fetch_project_db_by_id(project_id=project_id, user_id=user_id, db=db)

    if new_name is not None:
        project_db.name = new_name

    if new_description is not None:
        project_db.description = new_description

    if new_skills_vector is not None:
        project_db.skills_vector = new_skills_vector

    db.commit()
    db.refresh(project_db)

    return project_db


def delete_project_by_id(project_id: int, user_id: int, db: Session) -> None:
    project_db = fetch_project_db_by_id(project_id=project_id, user_id=user_id, db=db)
    db.delete(project_db)
    db.commit()
