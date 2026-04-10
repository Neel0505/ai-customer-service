"""Conversation model — chat sessions between contacts and the agent."""

from __future__ import annotations

import enum

from sqlalchemy import Boolean, Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class ConversationChannel(str, enum.Enum):
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    INSTAGRAM = "instagram"
    SIMULATOR = "simulator"


class ConversationStatus(str, enum.Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


class ConversationMode(str, enum.Enum):
    SALES = "sales"
    CUSTOMER_SERVICE = "customer_service"
    GENERAL = "general"


class Conversation(UUIDMixin, TimestampMixin, Base):
    """A conversation session — groups messages for a single interaction."""

    __tablename__ = "conversations"

    contact_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id"), index=True
    )
    channel: Mapped[ConversationChannel] = mapped_column(
        SAEnum(ConversationChannel), nullable=False
    )
    status: Mapped[ConversationStatus] = mapped_column(
        SAEnum(ConversationStatus), default=ConversationStatus.ACTIVE
    )
    mode: Mapped[ConversationMode] = mapped_column(
        SAEnum(ConversationMode), default=ConversationMode.GENERAL
    )
    overall_sentiment: Mapped[str | None] = mapped_column(String(20))
    escalated: Mapped[bool] = mapped_column(Boolean, default=False)
    escalation_reason: Mapped[str | None] = mapped_column(Text)

    # Relationships
    contact = relationship("Contact", back_populates="conversations")
    messages = relationship(
        "Message", back_populates="conversation", lazy="selectin", order_by="Message.created_at"
    )
