from typing import Any
from pydantic import BaseModel, ConfigDict
import uuid
from datetime import timedelta

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
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


class ProjectRequest(BaseModel):
    name: str
    description: str
    skills_vector: dict[str, Any]


class ProjectResponse(BaseModel):
    name: str
    description: str
    skills_vector: dict[str, Any]


class PatchProjectRequest(BaseModel):
    id: int
    name: str
    description: str
    skills_vector: dict[str, Any]


class PatchProjectResponse(BaseModel):
    name: str
    description: str
    skills_vector: dict[str, Any]


@router.post("/", response_model=ProjectResponse)
async def post_create_project(
    projectrequest: ProjectRequest,
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


@router.post("/patch", response_model=PatchProjectResponse)
async def patch_update_project(
    projectrequest: PatchProjectRequest,
    db: Session = Depends(get_db),
    user: UserDB = Depends(get_current_user),
):
    is_owner_of_project(project_id=projectrequest.id, user_id=user.id, db=db)

    project = update_project_by_id(
        project_id=projectrequest.id,
        user_id=user.id,
        db=db,
        new_name=projectrequest.name,
        new_description=projectrequest.description,
        new_skills_vector=projectrequest.skills_vector,
    )

    return project
