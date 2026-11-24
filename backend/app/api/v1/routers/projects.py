from datetime import datetime
from typing import Any

from app.core.database import get_db
from app.models.db import UserDB
from app.services.get_user import get_current_user
from app.services.project import (
    SortType,
    create_project,
    delete_project_by_id,
    fetch_project_db_by_id,
    fetch_projects_by_user_id,
    is_owner_of_project,
    update_project_by_id,
)
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy.orm import Session

router = APIRouter(prefix="/projects", tags=["Projects"])


class CreateProjectRequest(BaseModel):
    name: str
    description: str
    constraints_vector: dict[str, Any] = {}
    skills_vector: dict[str, Any] = {}

    @field_validator("name")
    def validate_name(cls, value):
        if len(value) > 255:
            raise HTTPException(
                status_code=400,
                detail="Название проекта не должно превышать 255 символов",
            )
        return value

    @field_validator("description")
    def validate_description(cls, value):
        if len(value) > 1024:
            raise HTTPException(
                status_code=400,
                detail="Описание проекта не должно превышать 1024 символов",
            )
        return value

    @field_validator("constraints_vector")
    def validate_constraints_vector(cls, value):
        if len(value) > 20000:
            raise HTTPException(
                status_code=400,
                detail="Вектор ограничений не должен превышать 20000 символов",
            )
        return value

    @field_validator("skills_vector")
    def validate_skills_vector(cls, value):
        if len(value) > 20000:
            raise HTTPException(
                status_code=400,
                detail="Вектор навыков не должен превышать 20000 символов",
            )
        return value


class CreateProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    constraints_vector: dict[str, Any]
    skills_vector: dict[str, Any]
    updated_at: datetime


@router.post("/", response_model=CreateProjectResponse)
async def post_create_project(
    projectrequest: CreateProjectRequest,
    db: Session = Depends(get_db),
    user: UserDB = Depends(get_current_user),
):
    project = create_project(
        user_id=user.id,
        db=db,
        name=projectrequest.name,
        description=projectrequest.description,
        constraints_vector=projectrequest.constraints_vector,
        skills_vector=projectrequest.skills_vector,
    )
    return project


class GetListProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class GetListProjectsResponse(BaseModel):
    data: list[GetListProjectResponse]


@router.get("/", response_model=GetListProjectsResponse)
async def get_list_projects(
    sort: SortType | None = Query(
        None,
        description="Сортировка: name_asc, name_desc, updated_at_asc, updated_at_desc",
    ),
    search: str | None = Query(
        None,
        description="Поиск по названию проекта",
    ),
    db: Session = Depends(get_db),
    user: UserDB = Depends(get_current_user),
):
    projects = fetch_projects_by_user_id(
        user_id=user.id, db=db, sort=sort, search=search
    )
    return GetListProjectsResponse(
        data=[GetListProjectResponse.model_validate(project) for project in projects]
    )


class GetProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    constraints_vector: dict[str, Any]
    skills_vector: dict[str, Any]
    updated_at: datetime


@router.get("/{project_id}", response_model=GetProjectResponse)
async def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    user: UserDB = Depends(get_current_user),
):
    project = fetch_project_db_by_id(project_id=project_id, user_id=user.id, db=db)
    return project


class PatchProjectRequest(CreateProjectRequest):
    pass


class PatchProjectResponse(CreateProjectResponse):
    pass


@router.patch("/{project_id}", response_model=PatchProjectResponse)
async def patch_update_project(
    project_id: int,
    projectrequest: PatchProjectRequest,
    db: Session = Depends(get_db),
    user: UserDB = Depends(get_current_user),
):
    is_owner_of_project(project_id=project_id, user_id=user.id, db=db)
    project = update_project_by_id(
        project_id=project_id,
        user_id=user.id,
        db=db,
        new_name=projectrequest.name,
        new_description=projectrequest.description,
        new_constraints_vector=projectrequest.constraints_vector,
        new_skills_vector=projectrequest.skills_vector,
    )

    return project


class GetEchoResponse(BaseModel):
    success: bool
    detail: str


@router.delete("/{project_id}", response_model=GetEchoResponse)
async def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    user: UserDB = Depends(get_current_user),
):
    delete_project_by_id(project_id=project_id, user_id=user.id, db=db)
    return GetEchoResponse(detail="Проект успешно удален!", success=True)
