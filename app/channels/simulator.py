"""Simulator channel adapter — WebSocket-based mock channel for testing."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from app.channels.base import ChannelAdapter
from app.schemas.nlp_message import ChannelEnum, NLPMessage, OutboundMessage

logger = logging.getLogger(__name__)


class SimulatorAdapter(ChannelAdapter):
    """Mock channel adapter for the testing simulator."""

    async def parse_inbound(self, raw_payload: dict[str, Any]) -> NLPMessage | None:
        """Parse a simulator message."""
        return NLPMessage(
            channel=ChannelEnum.SIMULATOR,
            user_id=raw_payload.get("user_id", "simulator_user"),
            text=raw_payload.get("text", ""),
            timestamp=datetime.utcnow(),
            metadata={"simulate_channel": raw_payload.get("simulate_channel", "whatsapp")},
        )

    async def send_message(self, message: OutboundMessage) -> bool:
        """Simulator messages are returned directly via WebSocket — this is a no-op."""
        return True

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        return True  # No signature verification for simulator
