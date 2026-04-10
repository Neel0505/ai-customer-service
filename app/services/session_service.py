"""Session management — Redis-backed conversation sessions with 24h TTL."""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any

import redis.asyncio as aioredis

from app.config import get_settings

logger = logging.getLogger(__name__)


class SessionService:
    """Manages conversation sessions in Redis with automatic expiry."""

    def __init__(self, redis: aioredis.Redis):
        self.redis = redis
        self.ttl = get_settings().session_ttl_seconds

    def _session_key(self, channel: str, user_id: str) -> str:
        return f"session:{channel}:{user_id}"

    async def get_or_create(self, channel: str, user_id: str) -> dict[str, Any]:
        """Load an existing session or create a new one."""
        key = self._session_key(channel, user_id)
        data = await self.redis.get(key)

        if data:
            session = json.loads(data)
            logger.debug("Loaded session %s for %s:%s", session["conversation_id"], channel, user_id)
            return session

        # Create new session
        session = {
            "conversation_id": str(uuid.uuid4()),
            "contact_id": None,
            "channel": channel,
            "user_id": user_id,
            "history": [],
            "identity": None,
            "retry_count": 0,
            "last_intent": None,
            "sentiment_history": [],
        }
        await self.redis.setex(key, self.ttl, json.dumps(session))
        logger.info("Created new session %s for %s:%s", session["conversation_id"], channel, user_id)
        return session

    async def update(
        self,
        session: dict[str, Any],
        inbound_text: str | None = None,
        outbound_text: str | None = None,
        intent: str | None = None,
        sentiment: str | None = None,
    ) -> None:
        """Update session with new messages and refresh TTL."""
        if inbound_text:
            session["history"].append({"role": "user", "content": inbound_text})
        if outbound_text:
            session["history"].append({"role": "assistant", "content": outbound_text})
        if intent:
            session["last_intent"] = intent
        if sentiment:
            session["sentiment_history"].append(sentiment)
            # Keep only last 10 sentiments
            session["sentiment_history"] = session["sentiment_history"][-10:]

        key = self._session_key(session["channel"], session["user_id"])
        await self.redis.setex(key, self.ttl, json.dumps(session))

    async def increment_retry(self, session: dict[str, Any]) -> int:
        """Increment the retry counter for the current intent."""
        session["retry_count"] = session.get("retry_count", 0) + 1
        await self.update(session)
        return session["retry_count"]

    async def reset_retry(self, session: dict[str, Any]) -> None:
        """Reset retry counter (on intent change or successful resolution)."""
        session["retry_count"] = 0
        await self.update(session)

    async def close(self, channel: str, user_id: str) -> None:
        """Delete a session (conversation resolved)."""
        key = self._session_key(channel, user_id)
        await self.redis.delete(key)

    # ── Identity Cache ─────────────────────────────────────────

    def _identity_key(self, channel: str, user_id: str) -> str:
        return f"identity:{channel}:{user_id}"

    async def get_identity(self, channel: str, user_id: str) -> dict[str, Any] | None:
        """Get cached customer identity."""
        key = self._identity_key(channel, user_id)
        data = await self.redis.get(key)
        return json.loads(data) if data else None

    async def set_identity(self, channel: str, user_id: str, identity: dict[str, Any]) -> None:
        """Cache customer identity."""
        key = self._identity_key(channel, user_id)
        await self.redis.setex(key, self.ttl, json.dumps(identity))
