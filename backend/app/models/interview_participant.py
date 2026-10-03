"""Interview participant — links users to interviews as panel members."""

import uuid

from sqlalchemy import String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class InterviewParticipant(Base):
    __tablename__ = "interview_participants"
    __table_args__ = (
        UniqueConstraint(
            "interview_id", "user_id",
            name="uq_interview_participant",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    interview_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str | None] = mapped_column(String(50), nullable=True, default="interviewer")

    # Relationships
    interview = relationship("Interview", back_populates="participants")
    user = relationship("User", back_populates="interview_participations", lazy="selectin")

    def __repr__(self) -> str:
        return f"<InterviewParticipant interview={self.interview_id} user={self.user_id}>"
