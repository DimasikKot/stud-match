from app.core.database import get_db
from app.core.db import SkillDB, UserDB
from app.services import skill as skill_service
from app.services.get_user import get_current_user, require_admin
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy.orm import Session

router = APIRouter(prefix="/skills", tags=["Skills"])


class SkillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class SkillListResponse(BaseModel):
    data: list[SkillResponse]


class CreateSkillRequest(BaseModel):
    name: str

    @field_validator("name")
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise HTTPException(status_code=400, detail="Название навыка пустое")
        if len(value) > 64:
            raise HTTPException(
                status_code=400,
                detail="Название навыка не должно превышать 64 символа",
            )
        return value


class GetEchoResponse(BaseModel):
    success: bool
    detail: str


@router.get("/", response_model=SkillListResponse)
def get_skills(
    db: Session = Depends(get_db),
    _: UserDB = Depends(get_current_user),
):
    skills = skill_service.fetch_skills(db)
    return SkillListResponse(
        data=[SkillResponse.model_validate(skill) for skill in skills]
    )


@router.post("/", response_model=SkillResponse, status_code=201)
def post_create_skill(
    skill_in: CreateSkillRequest,
    db: Session = Depends(get_db),
    _: UserDB = Depends(require_admin),
):
    skill_db = skill_service.create_skill(db=db, name=skill_in.name)
    return SkillResponse.model_validate(skill_db)


@router.delete("/{skill_id}", response_model=GetEchoResponse)
def delete_skill(
    skill_id: int,
    db: Session = Depends(get_db),
    _: UserDB = Depends(require_admin),
):
    skill_service.delete_skill(db=db, skill_id=skill_id)
    return GetEchoResponse(detail="Навык успешно удален!", success=True)
