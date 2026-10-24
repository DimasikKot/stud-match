from datetime import datetime
from typing import Any
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import (
    Enum,
    Integer,
    String,
    Boolean,
    TIMESTAMP,
    ForeignKey,
)

from app.core.database import Base

ModelFileRole = Enum(
    "training",
    "for_prediction",
    "predicted",
    name="model_file_role",
)


class ProjectDB(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    files = relationship(
        "FileDB",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    models = relationship(
        "ModelDB",
        back_populates="project",
        cascade="all, delete-orphan",
    )


class FileDB(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False)
    origin_file_id: Mapped[int] = mapped_column(Integer)
    is_labeled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    tags: Mapped[list[dict[str, str]]] = mapped_column(
        JSONB,
        nullable=False,
        default=[
            {
                "value": "art",
                "label": "Иновационные проекты",
                "color": "bg-yellow-300",
            },
            {
                "value": "eve",
                "label": "Событие",
                "color": "bg-orange-300",
            },
            {
                "value": "geo",
                "label": "Географическое место",
                "color": "bg-green-300",
            },
            {
                "value": "gpe",
                "label": "Страна/город (полит.)",
                "color": "bg-emerald-400",
            },
            {
                "value": "nat",
                "label": "Природное явление",
                "color": "bg-teal-300",
            },
            {
                "value": "org",
                "label": "Организация",
                "color": "bg-purple-300",
            },
            {
                "value": "per",
                "label": "Человек",
                "color": "bg-pink-300",
            },
            {
                "value": "tim",
                "label": "Дата/время",
                "color": "bg-blue-300",
            },
        ],
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    project = relationship("ProjectDB", back_populates="files")
    model_links = relationship(
        "ModelFileDB",
        back_populates="file",
        cascade="all, delete-orphan",
    )


class ModelFileDB(Base):
    __tablename__ = "model_files"

    model_id: Mapped[int] = mapped_column(
        ForeignKey("models.id", ondelete="CASCADE"),
        primary_key=True,
    )
    file_id: Mapped[int] = mapped_column(
        ForeignKey("files.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role: Mapped[str] = mapped_column(
        ModelFileRole,
        primary_key=True,
    )

    model = relationship("ModelDB", back_populates="file_links")
    file: Mapped[FileDB] = relationship("FileDB", back_populates="model_links")


class ModelDB(Base):
    __tablename__ = "models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    redis_id: Mapped[str | None] = mapped_column(String(64))

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    parameters: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
        default={
            "Эпохи": 2,
            "Размер батчей": 16,
            "Базовая модель": "albert-base-v2",
            "Скорость обучения": 2e-5,
            "Размер тренировочного набора": 0.8,
            "Максимальная длина предложения": 128,
        },
    )
    metrics: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default="{}"
    )
    graphs: Mapped[dict[str, str]] = mapped_column(
        JSONB, nullable=False, server_default="{}"
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    project = relationship("ProjectDB", back_populates="models")
    file_links: Mapped[list[ModelFileDB]] = relationship(
        "ModelFileDB",
        back_populates="model",
        cascade="all, delete-orphan",
    )
