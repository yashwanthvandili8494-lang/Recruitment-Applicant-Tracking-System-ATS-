"""Interview model — scheduled interviews for applications."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, DateTime, ForeignKey, Integer, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import InterviewType, InterviewStatus


class Interview(Base):
    __tablename__ = "interviews"
    __table_args__ = (
        Index("ix_interviews_application", "application_id"),
        Index("ix_interviews_start_time", "start_time"),
        Index("ix_interviews_status", "status"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    application_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False
    )
    interview_round: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    interview_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default=InterviewType.VIDEO.value
    )
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="UTC")
    meeting_location: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=InterviewStatus.SCHEDULED.value
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    application = relationship("Application", back_populates="interviews", lazy="selectin")
    participants = relationship(
        "InterviewParticipant", back_populates="interview", lazy="selectin"
    )
    feedbacks = relationship(
        "InterviewFeedback", back_populates="interview", lazy="noload"
    )

    def __repr__(self) -> str:
        return f"<Interview round={self.interview_round} ({self.status})>"
