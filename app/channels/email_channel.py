"""Email channel adapter — SendGrid Inbound Parse + branded HTML outbound."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import httpx
from jinja2 import Template

from app.channels.base import ChannelAdapter
from app.config import get_settings
from app.schemas.nlp_message import ChannelEnum, NLPMessage, OutboundMessage

logger = logging.getLogger(__name__)

# Branded HTML email template (inline for simplicity)
EMAIL_TEMPLATE = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f4f4f4;font-family:Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;margin:20px auto;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
  <tr><td style="background:{{ brand_color }};padding:20px 30px;text-align:center;">
    {% if logo_url %}<img src="{{ logo_url }}" alt="{{ company_name }}" style="max-height:40px;">{% endif %}
    {% if not logo_url %}<h1 style="color:#fff;margin:0;font-size:20px;">{{ company_name }}</h1>{% endif %}
  </td></tr>
  <tr><td style="padding:30px;">
    <div style="font-size:15px;line-height:1.6;color:#333;">{{ body }}</div>
  </td></tr>
  <tr><td style="padding:20px 30px;background:#f9f9f9;border-top:1px solid #eee;">
    <p style="margin:0;font-size:13px;color:#666;">
      Best regards,<br><strong>{{ agent_name }}</strong><br>{{ company_name }}
    </p>
  </td></tr>
</table>
</body></html>"""


class EmailAdapter(ChannelAdapter):
    """Email adapter using SendGrid for sending, Inbound Parse for receiving."""

    def __init__(self):
        settings = get_settings()
        self.sendgrid_api_key = settings.sendgrid_api_key
        self.from_address = settings.email_from_address
        self.from_name = settings.email_from_name
        self.brand_logo_url = settings.email_brand_logo_url
        self.brand_color = settings.email_brand_primary_color
        self.company_name = settings.email_brand_company_name or settings.client_name
        self.agent_name = settings.agent_name
        self.template = Template(EMAIL_TEMPLATE)

    async def parse_inbound(self, raw_payload: dict[str, Any]) -> NLPMessage | None:
        """Parse a SendGrid Inbound Parse webhook payload."""
        try:
            from_email = raw_payload.get("from", "")
            # Extract just the email address
            if "<" in from_email and ">" in from_email:
                from_email = from_email.split("<")[1].split(">")[0]

            subject = raw_payload.get("subject", "")
            text_body = raw_payload.get("text", "")
            html_body = raw_payload.get("html", "")

            # Prefer text, fall back to stripped HTML
            content = text_body.strip()
            if not content and html_body:
                from bs4 import BeautifulSoup
                content = BeautifulSoup(html_body, "html.parser").get_text(separator="\n").strip()

            if not content:
                return None

            return NLPMessage(
                channel=ChannelEnum.EMAIL,
                user_id=from_email,
                text=content,
                subject=subject,
                in_reply_to=raw_payload.get("In-Reply-To"),
                email_thread_id=raw_payload.get("Message-ID"),
                timestamp=datetime.utcnow(),
                metadata={"email": from_email, "subject": subject},
            )
        except Exception as e:
            logger.error("Failed to parse email payload: %s", e)
            return None

    async def send_message(self, message: OutboundMessage) -> bool:
        """Send a branded HTML email via SendGrid API."""
        try:
            # Render HTML
            html_body = self.template.render(
                brand_color=self.brand_color,
                logo_url=self.brand_logo_url,
                company_name=self.company_name,
                agent_name=self.agent_name,
                body=message.text.replace("\n", "<br>"),
            )

            # Build SendGrid request
            payload = {
                "personalizations": [{"to": [{"email": message.user_id}]}],
                "from": {"email": self.from_address, "name": self.from_name},
                "subject": message.metadata.get("subject", f"Re: Your inquiry — {self.company_name}"),
                "content": [
                    {"type": "text/plain", "value": message.text},
                    {"type": "text/html", "value": html_body},
                ],
            }

            # Add threading headers if replying
            if message.metadata.get("in_reply_to"):
                payload["headers"] = {
                    "In-Reply-To": message.metadata["in_reply_to"],
                    "References": message.metadata["in_reply_to"],
                }

            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://api.sendgrid.com/v3/mail/send",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.sendgrid_api_key}",
                        "Content-Type": "application/json",
                    },
                    timeout=15,
                )
                if resp.status_code >= 400:
                    logger.error("SendGrid send error: %s %s", resp.status_code, resp.text)
                    return False
            return True
        except Exception as e:
            logger.error("Email send failed: %s", e)
            return False

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        # SendGrid Inbound Parse doesn't have HMAC by default
        # Could be validated via IP allowlisting or webhook secret
        return True

    @staticmethod
    def is_out_of_office(text: str) -> bool:
        """Detect out-of-office auto-replies."""
        ooo_patterns = [
            "out of office", "away from my desk", "automatic reply",
            "auto-reply", "on vacation", "currently unavailable",
            "i am currently out", "limited access to email",
        ]
        text_lower = text.lower()
        return any(p in text_lower for p in ooo_patterns)

    @staticmethod
    def is_spam(text: str, subject: str) -> bool:
        """Basic spam detection."""
        if len(text) < 5:
            return True
        spam_indicators = ["unsubscribe", "click here", "win a", "congratulations"]
        combined = (text + " " + subject).lower()
        return sum(1 for s in spam_indicators if s in combined) >= 2
