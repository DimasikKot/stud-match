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

from app.core.database import get_db
from app.services.security_deps import (
    get_current_user,
    get_redis,
    refresh_cookie_scheme,
)
from app.models.db import Project, User
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


class ProjectResponse(ProjectRequest):
    name: str
    description: str
    skills_vector: dict[str, Any]


@router.post("/", response_model=ProjectResponse)
async def create_project(
    projectrequest: ProjectRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    user = db.query(User).filter(User.id == user.id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    project = Project(
        user_id=user.id,
        name=projectrequest.name,
        description=projectrequest.description,
        skills_vector=projectrequest.skills_vector,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project
