"""Lead model — BANT lead scoring and qualification data."""

from __future__ import annotations

import enum

from sqlalchemy import Boolean, Enum as SAEnum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class LeadStatus(str, enum.Enum):
    NEW = "new"
    NURTURING = "nurturing"
    QUALIFIED = "qualified"
    ESCALATED = "escalated"
    CLOSED = "closed"


class Lead(UUIDMixin, TimestampMixin, Base):
    """Lead qualification record — tracks BANT signals and score."""

    __tablename__ = "leads"

    contact_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id"), index=True
    )
    conversation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id"), index=True
    )
    score: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[LeadStatus] = mapped_column(
        SAEnum(LeadStatus), default=LeadStatus.NEW
    )

    # BANT: Budget
    budget_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    budget_range: Mapped[str | None] = mapped_column(String(64))

    # BANT: Authority
    is_decision_maker: Mapped[bool] = mapped_column(Boolean, default=False)
    role_title: Mapped[str | None] = mapped_column(String(128))

    # BANT: Need
    need_identified: Mapped[bool] = mapped_column(Boolean, default=False)
    pain_points: Mapped[dict | None] = mapped_column(JSONB, default=list)

    # BANT: Timeline
    timeline: Mapped[str | None] = mapped_column(String(64))
    timeline_days: Mapped[int | None] = mapped_column(Integer)

    # Relationships
    contact = relationship("Contact", back_populates="leads")
    conversation = relationship("Conversation")
