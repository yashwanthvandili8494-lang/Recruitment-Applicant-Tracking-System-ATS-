"""Application model — a candidate's application to a specific job."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ApplicationStatus


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint(
            "job_id", "candidate_id",
            name="uq_application_job_candidate",
        ),
        Index("ix_applications_status", "status"),
        Index("ix_applications_job", "job_id"),
        Index("ix_applications_candidate", "candidate_id"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False
    )
    candidate_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    resume_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=ApplicationStatus.APPLIED.value
    )
    cover_letter: Mapped[str | None] = mapped_column(Text, nullable=True)
    applied_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    job = relationship("Job", back_populates="applications", lazy="selectin")
    candidate = relationship(
        "User", back_populates="applications", foreign_keys=[candidate_id], lazy="selectin"
    )
    resume = relationship("Resume", back_populates="applications", lazy="selectin")
    status_history = relationship(
        "ApplicationStatusHistory",
        back_populates="application",
        order_by="ApplicationStatusHistory.created_at",
        lazy="noload",
    )
    interviews = relationship("Interview", back_populates="application", lazy="noload")
    offers = relationship("Offer", back_populates="application", lazy="noload")

    def __repr__(self) -> str:
        return f"<Application {self.id} ({self.status})>"
