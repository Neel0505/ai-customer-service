"""Instagram DM channel adapter — Meta Graph API."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import httpx

from app.channels.base import ChannelAdapter
from app.config import get_settings
from app.schemas.nlp_message import ChannelEnum, NLPMessage, OutboundMessage
from app.utils.signature_verify import verify_meta_signature

logger = logging.getLogger(__name__)

GRAPH_API_URL = "https://graph.facebook.com/v21.0"


class InstagramAdapter(ChannelAdapter):
    """Instagram Direct Message adapter via Meta Graph API."""

    def __init__(self):
        settings = get_settings()
        self.access_token = settings.instagram_access_token
        self.page_id = settings.instagram_page_id
        self.app_secret = settings.instagram_app_secret

    async def parse_inbound(self, raw_payload: dict[str, Any]) -> NLPMessage | None:
        """Parse an Instagram webhook payload into NLPMessage."""
        try:
            entry = raw_payload.get("entry", [{}])[0]
            messaging = entry.get("messaging", [])

            if not messaging:
                return None

            event = messaging[0]
            sender_id = event.get("sender", {}).get("id", "")
            message = event.get("message", {})

            if not message:
                return None  # Not a message event (e.g., read receipt)

            text = message.get("text", "")
            attachments = message.get("attachments", [])

            # If image attachment, note it
            if attachments and not text:
                att_type = attachments[0].get("type", "")
                text = f"[{att_type} received]"

            return NLPMessage(
                channel=ChannelEnum.INSTAGRAM,
                user_id=sender_id,
                text=text,
                message_id=message.get("mid", ""),
                timestamp=datetime.utcnow(),
            )
        except Exception as e:
            logger.error("Failed to parse Instagram payload: %s", e)
            return None

    async def send_message(self, message: OutboundMessage) -> bool:
        """Send a DM via Instagram Graph API."""
        try:
            url = f"{GRAPH_API_URL}/{self.page_id}/messages"
            payload = {
                "recipient": {"id": message.user_id},
                "message": {"text": message.text},
            }

            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    url,
                    json=payload,
                    params={"access_token": self.access_token},
                    timeout=15,
                )
                if resp.status_code >= 400:
                    logger.error("Instagram send error: %s", resp.text)
                    return False
            return True
        except Exception as e:
            logger.error("Instagram send failed: %s", e)
            return False

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        return verify_meta_signature(payload, signature, self.app_secret)
