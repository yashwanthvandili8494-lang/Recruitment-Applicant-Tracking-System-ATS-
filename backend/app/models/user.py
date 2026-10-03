"""User model — all authenticated users (staff and candidates)."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import UserRole


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_email", "email", unique=True),
        Index("ix_users_org_role", "organization_id", "role"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    organization_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(50), nullable=False, default=UserRole.CANDIDATE.value
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    organization = relationship("Organization", back_populates="users")
    candidate_profile = relationship(
        "CandidateProfile", back_populates="user", uselist=False, lazy="selectin"
    )
    resumes = relationship("Resume", back_populates="candidate", lazy="noload")
    applications = relationship(
        "Application", back_populates="candidate", foreign_keys="Application.candidate_id", lazy="noload"
    )
    interview_participations = relationship(
        "InterviewParticipant", back_populates="user", lazy="noload"
    )
    interview_feedbacks = relationship(
        "InterviewFeedback", back_populates="interviewer", lazy="noload"
    )
    notifications = relationship("Notification", back_populates="user", lazy="noload")
    audit_logs = relationship("AuditLog", back_populates="actor", lazy="noload")

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"
