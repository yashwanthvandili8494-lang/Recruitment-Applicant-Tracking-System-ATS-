"""Interview feedback — structured scorecard submitted by interviewers."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import Recommendation


class InterviewFeedback(Base):
    __tablename__ = "interview_feedbacks"
    __table_args__ = (
        UniqueConstraint(
            "interview_id", "interviewer_id",
            name="uq_feedback_interview_interviewer",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    interview_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False
    )
    interviewer_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    criterion_scores: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, default=dict,
        comment='e.g. {"technical_skills": 4, "communication": 5, "problem_solving": 3}',
    )
    strengths: Mapped[str | None] = mapped_column(Text, nullable=True)
    concerns: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation: Mapped[str | None] = mapped_column(String(50), nullable=True)
    overall_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    interview = relationship("Interview", back_populates="feedbacks")
    interviewer = relationship("User", back_populates="interview_feedbacks", lazy="selectin")

    def __repr__(self) -> str:
        return f"<InterviewFeedback interview={self.interview_id} by={self.interviewer_id}>"
