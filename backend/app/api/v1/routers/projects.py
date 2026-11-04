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
from app.services.project import (
    create_project,
    is_owner_of_project,
    update_project_by_id,
    fetch_project_db_by_id,
    SortType,
    fetch_projects_by_user_id,
    delete_project_by_id,
)
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

router = APIRouter(prefix="/projects", tags=["Projects"])


class CreateProjectRequest(BaseModel):
    name: str
    description: str
    skills_vector: dict[str, Any]

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

    @field_validator("skills_vector")
    def validate_skills_vector(cls, value):
        if len(value) > 1024:
            raise HTTPException(
                status_code=400,
                detail="Вектор навыков не должен превышать 1024 символов",
            )
        return value


class CreateProjectResponse(BaseModel):
    name: str
    description: str
    skills_vector: dict[str, Any]


class PatchProjectRequest(BaseModel):
    name: str
    description: str
    skills_vector: dict[str, Any]

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

    @field_validator("skills_vector")
    def validate_skills_vector(cls, value):
        if len(value) > 1024:
            raise HTTPException(
                status_code=400,
                detail="Вектор навыков не должен превышать 1024 символов",
            )
        return value


class PatchProjectResponse(BaseModel):
    name: str
    description: str
    skills_vector: dict[str, Any]


class GetProjectResponse(BaseModel):
    name: str
    description: str
    skills_vector: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class GetListProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class GetListProjectsResponse(BaseModel):
    data: list[GetListProjectResponse]


class GetEchoResponse(BaseModel):
    detail: str
    success: bool


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
        skills_vector=projectrequest.skills_vector,
    )
    return project


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
        new_skills_vector=projectrequest.skills_vector,
    )

    return project


@router.get("/{project_id}", response_model=GetProjectResponse)
async def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    user: UserDB = Depends(get_current_user),
):
    project = fetch_project_db_by_id(project_id=project_id, user_id=user.id, db=db)
    return project


@router.get("/", response_model=GetListProjectsResponse)
async def get_list_projects(
    sort: SortType | None = Query(
        "created_at_desc",
        description="Сортировка: name_asc, name_desc, created_at_asc, created_at_desc, updated_at_asc, updated_at_desc",
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


@router.delete("/{project_id}", response_model=GetEchoResponse)
async def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    user: UserDB = Depends(get_current_user),
):
    delete_project_by_id(project_id=project_id, user_id=user.id, db=db)
    return GetEchoResponse(detail="Проект успешно удален!", success=True)
