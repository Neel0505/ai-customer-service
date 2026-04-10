"""Abstract channel adapter base class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.schemas.nlp_message import NLPMessage, OutboundMessage


class ChannelAdapter(ABC):
    """Base class for all channel adapters."""

    @abstractmethod
    async def parse_inbound(self, raw_payload: dict[str, Any]) -> NLPMessage | None:
        """Parse a raw webhook payload into a normalized NLPMessage."""
        ...

    @abstractmethod
    async def send_message(self, message: OutboundMessage) -> bool:
        """Send a message to the user via this channel. Returns True on success."""
        ...

    @abstractmethod
    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify the webhook payload signature."""
        ...
