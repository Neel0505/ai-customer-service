"""Escalation model — logs every escalation event for audit trail."""

from __future__ import annotations

import enum

from sqlalchemy import Boolean, Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class EscalationTrigger(str, enum.Enum):
    USER_REQUEST = "user_request"
    SENTIMENT = "sentiment"
    LEAD_SCORE = "lead_score"
    MAX_RETRIES = "max_retries"
    LEGAL = "legal"
    VIP = "vip"
    UNKNOWN_INTENT = "unknown_intent"
    SYSTEM_ERROR = "system_error"


class Escalation(UUIDMixin, TimestampMixin, Base):
    """Record of a conversation escalation to a human agent."""

    __tablename__ = "escalations"

    conversation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id"), index=True
    )
    contact_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id"), index=True
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    trigger_type: Mapped[EscalationTrigger] = mapped_column(
        SAEnum(EscalationTrigger), nullable=False
    )
    context_summary: Mapped[str | None] = mapped_column(Text)
    email_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    conversation = relationship("Conversation")
    contact = relationship("Contact")
