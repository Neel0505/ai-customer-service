"""Escalation service — trigger checks and email alert delivery."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.escalation import Escalation, EscalationTrigger

logger = logging.getLogger(__name__)

# Keywords that trigger immediate escalation
LEGAL_KEYWORDS = ["lawyer", "lawsuit", "sue", "fraud", "legal action", "report to authorities"]
HUMAN_KEYWORDS = [
    "human", "agent", "person", "talk to someone", "real person",
    "speak to someone", "representative", "live agent",
]


class EscalationService:
    """Manages escalation trigger checks and email alert delivery."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()

    def check_triggers(
        self,
        text: str,
        intent: str,
        confidence: float,
        sentiment_history: list[str],
        lead_score: int | None,
        retry_count: int,
        contact_tags: list[str] | None = None,
    ) -> tuple[bool, EscalationTrigger | None, str]:
        """Check all escalation triggers. Returns (should_escalate, trigger_type, reason)."""

        text_lower = text.lower()

        # 1. User explicitly requests human
        if any(kw in text_lower for kw in HUMAN_KEYWORDS):
            return True, EscalationTrigger.USER_REQUEST, "User requested human agent"

        # 2. Legal / compliance keywords
        if any(kw in text_lower for kw in LEGAL_KEYWORDS):
            return True, EscalationTrigger.LEGAL, f"Legal keyword detected: {text[:100]}"

        # 3. Negative sentiment (2+ consecutive frustrated turns)
        if len(sentiment_history) >= 2:
            last_two = sentiment_history[-2:]
            if all(s in ("frustrated", "negative") for s in last_two):
                return True, EscalationTrigger.SENTIMENT, "Sustained negative sentiment (2+ turns)"

        # 4. High lead score
        if lead_score is not None and lead_score >= self.settings.escalation_lead_score_threshold:
            return True, EscalationTrigger.LEAD_SCORE, f"Lead score {lead_score} exceeds threshold"

        # 5. Max retries exceeded
        if retry_count >= self.settings.sla_max_retries:
            return True, EscalationTrigger.MAX_RETRIES, f"Unresolved after {retry_count} attempts"

        # 6. Low confidence / unknown intent
        if confidence < self.settings.escalation_confidence_threshold:
            return True, EscalationTrigger.UNKNOWN_INTENT, f"Low intent confidence: {confidence}"

        # 7. VIP customer
        if contact_tags and "VIP" in contact_tags:
            return True, EscalationTrigger.VIP, "VIP customer flagged for priority handling"

        return False, None, ""

    async def create_escalation(
        self,
        conversation_id: str,
        contact_id: str,
        trigger_type: EscalationTrigger,
        reason: str,
        context_summary: str,
    ) -> Escalation:
        """Create an escalation record in the database."""
        escalation = Escalation(
            conversation_id=conversation_id,
            contact_id=contact_id,
            trigger_type=trigger_type,
            reason=reason,
            context_summary=context_summary,
            email_sent=False,
            resolved=False,
        )
        self.db.add(escalation)
        await self.db.flush()
        return escalation

    async def send_escalation_email(
        self,
        escalation: Escalation,
        contact_name: str | None,
        channel: str,
        last_messages: list[dict[str, Any]],
        lead_score: int | None = None,
    ) -> bool:
        """Send an escalation alert email."""
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, Content

            settings = self.settings
            if not settings.sendgrid_api_key or not settings.escalation_email_to:
                logger.warning("Escalation email not configured — skipping")
                return False

            # Build email body
            messages_text = "\n".join(
                f"[{m.get('role', 'unknown')}]: {m.get('content', '')[:200]}"
                for m in last_messages[-5:]
            )

            body = f"""🚨 ESCALATION REQUIRED
━━━━━━━━━━━━━━━━━━━━━━━━
Customer: {contact_name or 'Unknown'}
Channel: {channel}
Reason: {escalation.reason}
Trigger: {escalation.trigger_type.value}
{f"Lead Score: {lead_score}/100" if lead_score else ""}
━━━━━━━━━━━━━━━━━━━━━━━━

Last messages:
{messages_text}

━━━━━━━━━━━━━━━━━━━━━━━━
Conversation ID: {escalation.conversation_id}
"""
            message = Mail(
                from_email=settings.escalation_email_from or settings.email_from_address,
                to_emails=settings.escalation_email_to,
                subject=f"🚨 Escalation: {escalation.reason[:50]} — {contact_name or 'Customer'}",
                plain_text_content=body,
            )

            sg = SendGridAPIClient(settings.sendgrid_api_key)
            sg.send(message)

            escalation.email_sent = True
            await self.db.flush()
            logger.info("Escalation email sent for conversation %s", escalation.conversation_id)
            return True

        except Exception as e:
            logger.error("Failed to send escalation email: %s", e)
            return False

    def get_hold_message(self) -> str:
        """Return the message sent to the user during escalation."""
        return (
            "I'm connecting you with a team member who can help further. "
            "They'll reach out to you shortly. Thank you for your patience! 🙏"
        )
