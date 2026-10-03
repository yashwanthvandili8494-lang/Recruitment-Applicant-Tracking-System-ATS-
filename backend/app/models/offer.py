"""Offer model — job offers issued to candidates."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import OfferStatus


class Offer(Base):
    __tablename__ = "offers"
    __table_args__ = (
        Index("ix_offers_application", "application_id"),
        Index("ix_offers_status", "status"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    application_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False
    )
    compensation_details: Mapped[dict | None] = mapped_column(
        JSON, nullable=True,
        comment='e.g. {"base_salary": 120000, "currency": "USD", "benefits": "..."}',
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=OfferStatus.DRAFT.value
    )
    issued_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approved_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    candidate_response_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
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
    application = relationship("Application", back_populates="offers", lazy="selectin")
    issuer = relationship("User", foreign_keys=[issued_by], lazy="selectin")
    approver = relationship("User", foreign_keys=[approved_by], lazy="selectin")

    def __repr__(self) -> str:
        return f"<Offer {self.id} ({self.status})>"
