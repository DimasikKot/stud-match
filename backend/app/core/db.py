import enum
from datetime import datetime
from typing import Any

from app.core.database import Base
from sqlalchemy import (
    TIMESTAMP,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    TEACHER = "teacher"


class ZipStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class FileStatus(str, enum.Enum):
    NOT_EXTRACTED = "not_extracted"
    QUEUED = "queued"
    EXTRACTING = "extracting"
    EXTRACTED = "extracted"
    FAILED = "failed"
    APPLIED = "applied"


class DistributionStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    QUEUED = "queued"
    DISTRIBUTING = "distributing"
    DISTRIBUTED = "distributed"
    FAILED = "failed"


ROLE_ADMIN = UserRole.ADMIN
ROLE_TEACHER = UserRole.TEACHER


def _enum_values(enum_cls: type[enum.Enum]) -> list[str]:
    return [member.value for member in enum_cls]


class SkillDB(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )


class UserDB(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )
    fullname: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
    )
    email: Mapped[str] = mapped_column(
        String(256),
        unique=True,
        nullable=False,
        index=True,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", values_callable=_enum_values),
        nullable=False,
        default=UserRole.TEACHER,
        server_default=UserRole.TEACHER.value,
    )
    skills_set: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
    )
    model_version: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="-",
        server_default="-",
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class ZipDB(Base):
    __tablename__ = "zips"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )
    status: Mapped[ZipStatus] = mapped_column(
        Enum(ZipStatus, name="zip_status", values_callable=_enum_values),
        nullable=False,
        default=ZipStatus.PENDING,
        server_default=ZipStatus.PENDING.value,
    )
    name: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
    )
    date: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=func.now(),
    )
    files: Mapped[list["FileDB"]] = relationship(
        back_populates="zip", cascade="all, delete-orphan"
    )


class RustfsObjectDB(Base):
    __tablename__ = "rustfs_objects"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )
    object_key: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=False,
    )
    bucket: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    extension: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )
    size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    status: Mapped[FileStatus] = mapped_column(
        Enum(FileStatus, name="file_status", values_callable=_enum_values),
        nullable=False,
        default=FileStatus.NOT_EXTRACTED,
        server_default=FileStatus.NOT_EXTRACTED.value,
        index=True,
    )
    feature_set: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
    )
    model_version: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="-",
        server_default="-",
    )
    files: Mapped[list["FileDB"]] = relationship(
        back_populates="rustfs_object", cascade="all, delete-orphan"
    )


class FileDB(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
    )
    zip_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("zips.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rustfs_object_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("rustfs_objects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    zip: Mapped["ZipDB"] = relationship(back_populates="files")
    rustfs_object: Mapped["RustfsObjectDB"] = relationship(back_populates="files")
    students: Mapped[list["StudentDB"]] = relationship(
        secondary="student_files", back_populates="files"
    )

    @property
    def student_fullname(self) -> str | None:
        names = [student.fullname for student in self.students]
        return ", ".join(names) if names else None


class StudentDB(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )
    fullname: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
    )
    skills_set: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
    )
    model_version: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="-",
        server_default="-",
    )
    files: Mapped[list["FileDB"]] = relationship(
        secondary="student_files", back_populates="students"
    )


class StudentFilesDB(Base):
    __tablename__ = "student_files"

    file_id: Mapped[int] = mapped_column(
        ForeignKey("files.id", ondelete="CASCADE"),
        primary_key=True,
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"),
        primary_key=True,
    )


class ProjectDB(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    constraints_set: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
    )
    skills_set: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
    )
    model_version: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="-",
        server_default="-",
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class DistributionDB(Base):
    __tablename__ = "distributions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
    )
    status: Mapped[DistributionStatus] = mapped_column(
        Enum(
            DistributionStatus, name="distribution_status", values_callable=_enum_values
        ),
        nullable=False,
        default=DistributionStatus.NOT_STARTED,
        server_default=DistributionStatus.NOT_STARTED.value,
    )
    selected_project_ids: Mapped[list[int]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="[]",
    )
    selected_student_ids: Mapped[list[int]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="[]",
    )
    selected_teacher_ids: Mapped[list[int]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="[]",
    )
    result_set: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
    )
    model_version: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="-",
        server_default="-",
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now()
    )
