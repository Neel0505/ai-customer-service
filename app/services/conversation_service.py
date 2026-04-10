"""Conversation service — persists messages and conversations to Postgres."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation, ConversationChannel, ConversationMode, ConversationStatus
from app.models.message import Message, MessageDirection, ContentType

logger = logging.getLogger(__name__)


class ConversationService:
    """Handles persistent storage of conversations and messages."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_conversation(
        self,
        conversation_id: str,
        contact_id: str,
        channel: str,
        mode: str = "general",
    ) -> Conversation:
        """Get existing conversation by ID or create a new one."""
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        result = await self.db.execute(stmt)
        conv = result.scalar_one_or_none()

        if not conv:
            conv = Conversation(
                id=uuid.UUID(conversation_id),
                contact_id=contact_id,
                channel=ConversationChannel(channel),
                mode=ConversationMode(mode) if mode in ConversationMode.__members__.values() else ConversationMode.GENERAL,
            )
            self.db.add(conv)
            await self.db.flush()

        return conv

    async def save_inbound_message(
        self,
        conversation_id: str,
        content: str,
        intent: str | None = None,
        sentiment: str | None = None,
        channel_message_id: str | None = None,
    ) -> Message:
        """Save an inbound (user) message."""
        msg = Message(
            conversation_id=conversation_id,
            direction=MessageDirection.INBOUND,
            content=content,
            intent=intent,
            sentiment=sentiment,
            channel_message_id=channel_message_id,
        )
        self.db.add(msg)
        await self.db.flush()
        return msg

    async def save_outbound_message(
        self,
        conversation_id: str,
        content: str,
        intent: str | None = None,
        tool_calls: list[dict] | None = None,
        llm_model: str | None = None,
        token_count: int | None = None,
    ) -> Message:
        """Save an outbound (agent) message."""
        msg = Message(
            conversation_id=conversation_id,
            direction=MessageDirection.OUTBOUND,
            content=content,
            intent=intent,
            tool_calls=tool_calls,
            llm_model=llm_model,
            token_count=token_count,
        )
        self.db.add(msg)
        await self.db.flush()
        return msg

    async def mark_escalated(self, conversation_id: str, reason: str) -> None:
        """Mark a conversation as escalated."""
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        result = await self.db.execute(stmt)
        conv = result.scalar_one_or_none()
        if conv:
            conv.status = ConversationStatus.ESCALATED
            conv.escalated = True
            conv.escalation_reason = reason
            await self.db.flush()

    async def mark_resolved(self, conversation_id: str) -> None:
        """Mark a conversation as resolved."""
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        result = await self.db.execute(stmt)
        conv = result.scalar_one_or_none()
        if conv:
            conv.status = ConversationStatus.RESOLVED
            await self.db.flush()

    # ── Analytics Queries ──────────────────────────────────────

    async def get_conversation_count(self, since_hours: int = 24) -> int:
        """Count conversations in the last N hours."""
        from datetime import datetime, timedelta
        cutoff = datetime.utcnow() - timedelta(hours=since_hours)
        stmt = select(func.count(Conversation.id)).where(Conversation.created_at >= cutoff)
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def get_channel_breakdown(self, since_hours: int = 24) -> dict[str, int]:
        """Get conversation count breakdown by channel."""
        from datetime import datetime, timedelta
        cutoff = datetime.utcnow() - timedelta(hours=since_hours)
        stmt = (
            select(Conversation.channel, func.count(Conversation.id))
            .where(Conversation.created_at >= cutoff)
            .group_by(Conversation.channel)
        )
        result = await self.db.execute(stmt)
        return {str(row[0].value): row[1] for row in result.all()}

    async def get_escalation_count(self, since_hours: int = 24) -> int:
        """Count escalated conversations in the last N hours."""
        from datetime import datetime, timedelta
        cutoff = datetime.utcnow() - timedelta(hours=since_hours)
        stmt = select(func.count(Conversation.id)).where(
            Conversation.escalated == True,
            Conversation.created_at >= cutoff,
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def get_recent_conversations(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get recent conversations with basic info."""
        stmt = (
            select(Conversation)
            .order_by(Conversation.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        convos = result.scalars().all()

        return [
            {
                "id": str(c.id),
                "channel": c.channel.value,
                "status": c.status.value,
                "mode": c.mode.value,
                "escalated": c.escalated,
                "message_count": len(c.messages) if c.messages else 0,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in convos
        ]
