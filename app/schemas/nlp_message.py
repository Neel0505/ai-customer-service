"""Normalized NLPMessage schema — the universal message format across all channels."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ChannelEnum(str, Enum):
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    INSTAGRAM = "instagram"
    SIMULATOR = "simulator"


class DirectionEnum(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class SentimentEnum(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    FRUSTRATED = "frustrated"


class MediaAttachment(BaseModel):
    """An attached media file (image, document, voice note)."""
    type: str  # image, document, audio, video
    url: str
    mime_type: str | None = None
    filename: str | None = None


class NLPMessage(BaseModel):
    """Normalized message object — every channel adapter produces this."""

    session_id: str | None = None
    channel: ChannelEnum
    user_id: str  # Platform user ID (phone number, email, PSID)
    contact_id: str | None = None  # Resolved CRM contact ID
    message_id: str | None = None  # Platform message ID
    text: str = ""
    media: list[MediaAttachment] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    direction: DirectionEnum = DirectionEnum.INBOUND
    intent: str | None = None
    sentiment: SentimentEnum | None = None
    escalate: bool = False
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Email-specific fields
    subject: str | None = None
    in_reply_to: str | None = None
    email_thread_id: str | None = None


class IntentResult(BaseModel):
    """Output of the intent classifier."""
    intent: str
    confidence: float = 0.0
    mode: str = "general"  # sales | customer_service | general
    needs_rag: bool = True


class OutboundMessage(BaseModel):
    """Response message to send back to the user."""
    text: str
    channel: ChannelEnum
    user_id: str
    interactive: dict[str, Any] | None = None  # WhatsApp buttons/lists
    media: list[MediaAttachment] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Debug info (for simulator)
    debug: dict[str, Any] | None = None
