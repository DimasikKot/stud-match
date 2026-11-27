from app.core.db import SkillDB
from fastapi import HTTPException, status
from sqlalchemy.orm import Session


def fetch_skills(db: Session) -> list[SkillDB]:
    return db.query(SkillDB).order_by(SkillDB.name).all()


def create_skill(db: Session, name: str) -> SkillDB:
    name = name.strip()
    existing = db.query(SkillDB).filter(SkillDB.name.ilike(name)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Навык с таким названием уже существует",
        )

    skill_db = SkillDB(name=name)
    db.add(skill_db)
    db.commit()
    db.refresh(skill_db)
    return skill_db


def delete_skill(db: Session, skill_id: int) -> None:
    skill_db = db.query(SkillDB).filter(SkillDB.id == skill_id).first()
    if skill_db is None:
        raise HTTPException(status_code=404, detail="Навык не найден")
    db.delete(skill_db)
    db.commit()
