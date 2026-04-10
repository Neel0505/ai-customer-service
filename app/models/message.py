"""Message model — permanent store for all conversation messages."""

from __future__ import annotations

import enum

from sqlalchemy import Enum as SAEnum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class MessageDirection(str, enum.Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class ContentType(str, enum.Enum):
    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"
    INTERACTIVE = "interactive"


class Message(UUIDMixin, TimestampMixin, Base):
    """A single message in a conversation — kept permanently."""

    __tablename__ = "messages"

    conversation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id"), index=True
    )
    direction: Mapped[MessageDirection] = mapped_column(
        SAEnum(MessageDirection), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[ContentType] = mapped_column(
        SAEnum(ContentType), default=ContentType.TEXT
    )
    channel_message_id: Mapped[str | None] = mapped_column(String(128))
    intent: Mapped[str | None] = mapped_column(String(64))
    sentiment: Mapped[str | None] = mapped_column(String(20))
    tool_calls: Mapped[dict | None] = mapped_column(JSONB)
    llm_model: Mapped[str | None] = mapped_column(String(64))
    token_count: Mapped[int | None] = mapped_column(Integer)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
