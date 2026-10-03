"""Job model — job vacancies posted by organizations."""

import uuid
from datetime import datetime, timezone, date

from sqlalchemy import (
    String, Text, Integer, Numeric, Date,
    DateTime, ForeignKey, Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import JobStatus, EmploymentType, WorkMode


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        Index("ix_jobs_org_status", "organization_id", "status"),
        Index("ix_jobs_department", "department"),
        Index("ix_jobs_deadline", "deadline"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    responsibilities: Mapped[str | None] = mapped_column(Text, nullable=True)
    requirements: Mapped[str | None] = mapped_column(Text, nullable=True)
    preferred_skills: Mapped[str | None] = mapped_column(Text, nullable=True)
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    employment_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default=EmploymentType.FULL_TIME.value
    )
    work_mode: Mapped[str] = mapped_column(
        String(50), nullable=False, default=WorkMode.ONSITE.value
    )
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    experience_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    experience_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_min: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    salary_max: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    openings: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    hiring_manager_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=JobStatus.DRAFT.value, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    organization = relationship("Organization", back_populates="jobs")
    hiring_manager = relationship("User", foreign_keys=[hiring_manager_id], lazy="selectin")
    applications = relationship("Application", back_populates="job", lazy="noload")

    def __repr__(self) -> str:
        return f"<Job {self.title} ({self.status})>"
