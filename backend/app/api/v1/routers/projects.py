from datetime import datetime
from typing import Any

from app.core.database import get_db
from app.core.db import UserDB
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


class CreateProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    constraints_set: dict[str, Any]
    skills_set: dict[str, Any]
    model_version: str

    updated_at: datetime


@router.post("/", response_model=CreateProjectResponse)
async def post_create_project(
    project: CreateProjectRequest,
    db: Session = Depends(get_db),
    user: UserDB = Depends(get_current_user),
):
    project_db = create_project(
        user_id=user.id, db=db, name=project.name, description=project.description
    )
    return CreateProjectResponse.model_validate(project_db)


class GetListProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    updated_at: datetime


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
    constraints_set: dict[str, Any]
    skills_set: dict[str, Any]
    model_version: str
    updated_at: datetime


@router.get("/{project_id}", response_model=GetProjectResponse)
async def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    user: UserDB = Depends(get_current_user),
):
    project_db = fetch_project_db_by_id(project_id=project_id, user_id=user.id, db=db)
    return GetProjectResponse.model_validate(project_db)


class PatchProjectRequest(CreateProjectRequest):
    constraints_set: dict[str, Any] | None = None
    skills_set: dict[str, Any] | None = None
    model_version: str | None = None


class PatchProjectResponse(CreateProjectResponse):
    constraints_set: dict[str, Any]
    skills_set: dict[str, Any]
    model_version: str


@router.patch("/{project_id}", response_model=PatchProjectResponse)
async def patch_update_project(
    project_id: int,
    projectrequest: PatchProjectRequest,
    db: Session = Depends(get_db),
    user: UserDB = Depends(get_current_user),
):
    is_owner_of_project(project_id=project_id, user_id=user.id, db=db)
    project_db = update_project_by_id(
        project_id=project_id,
        user_id=user.id,
        db=db,
        new_name=projectrequest.name,
        new_description=projectrequest.description,
        new_constraints_set=projectrequest.constraints_set,
        new_skills_set=projectrequest.skills_set,
        new_model_version=projectrequest.model_version,
    )

    return PatchProjectResponse.model_validate(project_db)


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
