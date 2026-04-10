"""Twilio WhatsApp channel adapter — supports text, buttons, lists, and media."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from twilio.rest import Client
from twilio.request_validator import RequestValidator

from app.channels.base import ChannelAdapter
from app.config import get_settings
from app.schemas.nlp_message import ChannelEnum, NLPMessage, OutboundMessage

logger = logging.getLogger(__name__)


class TwilioWhatsAppAdapter(ChannelAdapter):
    """Twilio WhatsApp Business API adapter."""

    def __init__(self):
        settings = get_settings()
        self.account_sid = settings.twilio_account_sid
        self.auth_token = settings.twilio_auth_token
        self.whatsapp_number = settings.twilio_whatsapp_number
        self.client = Client(self.account_sid, self.auth_token) if self.account_sid and self.auth_token else None
        self.validator = RequestValidator(self.auth_token) if self.auth_token else None

    async def parse_inbound(self, raw_payload: dict[str, Any]) -> NLPMessage | None:
        """Parse a Twilio WhatsApp webhook payload into NLPMessage."""
        try:
            # Twilio's payload comes as form data (dict)
            from_number = raw_payload.get("From", "")
            # Twilio prefixes WhatsApp numbers with "whatsapp:"
            if from_number.startswith("whatsapp:"):
                from_number = from_number.replace("whatsapp:", "")

            body = raw_payload.get("Body", "")
            message_id = raw_payload.get("MessageSid", "")
            
            # Check for media (images/documents)
            num_media = int(raw_payload.get("NumMedia", "0"))
            if num_media > 0 and not body:
                media_type = raw_payload.get("MediaContentType0", "")
                if media_type.startswith("image/"):
                    body = "[Image received]"
                else:
                    body = "[Document received]"

            return NLPMessage(
                channel=ChannelEnum.WHATSAPP,
                user_id=from_number,
                text=body,
                message_id=message_id,
                timestamp=datetime.utcnow(),
            )
        except Exception as e:
            logger.error("Failed to parse Twilio WhatsApp payload: %s", e)
            return None

    async def send_message(self, message: OutboundMessage) -> bool:
        """Send a message via Twilio REST API."""
        try:
            if not self.client:
                logger.error("Twilio client not initialized (missing credentials)")
                return False

            to_number = f"whatsapp:{message.user_id}"
            from_number = f"whatsapp:{self.whatsapp_number}"

            # Check if we should send interactive message
            if message.interactive:
                # Twilio requires pre-approved Content Templates for generic interactive messages (lists/buttons)
                # or formatting them in specific ways using Content API.
                # For basic compatibility without prior template creation, we will fallback to text rendering.
                text_content = self._render_interactive_as_text(message)
                self.client.messages.create(
                    body=text_content,
                    from_=from_number,
                    to=to_number
                )
                return True
            else:
                chunks = self._chunk_text(message.text, max_len=1600)  # Twilio recommends max 1600 for WhatsApp
                for chunk in chunks:
                    self.client.messages.create(
                        body=chunk,
                        from_=from_number,
                        to=to_number
                    )
                return True
        except Exception as e:
            logger.error("Twilio WhatsApp send failed: %s", e)
            return False

    def verify_signature(self, url: str, params: dict, signature: str) -> bool:
        """Verify Twilio webhook signature."""
        if not self.validator:
            return False
        return self.validator.validate(url, params, signature)

    # ── Interactive Message Builders & Fallbacks ───────────────────────────

    def _render_interactive_as_text(self, message: OutboundMessage) -> str:
        """Fallback: Render interactive buttons/lists as formatted text."""
        interactive = message.interactive or {}
        int_type = interactive.get("type", "button")
        
        lines = [message.text, ""]
        
        if int_type == "button":
            for idx, b in enumerate(interactive.get("buttons", [])[:3], 1):
                lines.append(f"{idx}. {b.get('title', '')}")
            lines.append("\n(Please reply with the option text)")
                
        elif int_type == "list":
            for section in interactive.get("sections", []):
                lines.append(f"*{section.get('title', 'Options')}*")
                for idx, row in enumerate(section.get("rows", []), 1):
                    lines.append(f"- {row.get('title', '')}: {row.get('description', '')}")
            lines.append("\n(Please reply with your choice)")
            
        return "\n".join(lines)

    @staticmethod
    def build_product_list(products: list[dict], intro_text: str) -> dict:
        """Build an interactive list representation."""
        rows = []
        for p in products[:10]:
            rows.append({
                "id": str(p.get("id", "")),
                "title": p.get("title", "")[:24],
                "description": f"{p.get('price_range', '')}".strip()[:72],
            })

        return {
            "type": "list",
            "button_text": "View Products",
            "sections": [{"title": "Products", "rows": rows}],
        }

    @staticmethod
    def build_action_buttons(buttons: list[dict[str, str]]) -> dict:
        """Build contextual action buttons."""
        return {
            "type": "button",
            "buttons": [{"id": b["id"], "title": b["title"][:20]} for b in buttons[:3]],
        }

    @staticmethod
    def _chunk_text(text: str, max_len: int = 1600) -> list[str]:
        """Split long text at sentence boundaries."""
        if len(text) <= max_len:
            return [text]

        chunks = []
        current = ""
        sentences = text.replace(". ", ".\\n").split("\\n")

        for sentence in sentences:
            if len(current) + len(sentence) + 1 > max_len:
                if current:
                    chunks.append(current.strip())
                current = sentence
            else:
                current += " " + sentence if current else sentence

        if current:
            chunks.append(current.strip())

        return chunks
