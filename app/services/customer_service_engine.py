"""Customer service engine — complaint handling, SLA tracking, intent-specific logic."""

from __future__ import annotations

import logging
from typing import Any

from app.config import get_settings

logger = logging.getLogger(__name__)


class CustomerServiceEngine:
    """Handles customer service-specific logic: complaints, SLA, retry management."""

    def __init__(self):
        self.settings = get_settings()

    def get_complaint_instructions(self) -> str:
        """Return complaint-handling instructions to inject into the system prompt."""
        return (
            "\n\nCOMPLAINT HANDLING PROTOCOL:\n"
            "The customer has expressed a complaint. Follow these steps:\n"
            "1. ACKNOWLEDGE their frustration immediately — never argue or defend.\n"
            "2. THANK them for bringing the issue to your attention.\n"
            "3. ASK clarifying questions to fully understand — do NOT jump to solutions.\n"
            "4. OFFER a concrete resolution (refund, replacement, credit, follow-up call).\n"
            "5. If you cannot resolve it, escalate to a human with the full context.\n"
            "6. ALWAYS end by asking if there's anything else you can help with."
        )

    def get_return_instructions(self, return_window_days: int, return_policy_url: str) -> str:
        """Return-specific instructions for the system prompt."""
        return (
            f"\n\nRETURN POLICY:\n"
            f"- Return window: {return_window_days} days from delivery\n"
            f"- Return policy URL: {return_policy_url}\n"
            "- If within the window: use the shopify_initiate_return tool\n"
            "- If outside the window: offer to escalate as a goodwill exception\n"
            "- Always confirm the order number before initiating"
        )

    def should_add_complaint_protocol(self, intent: str, sentiment: str | None) -> bool:
        """Check if complaint protocol should be added to the prompt."""
        return intent == "complaint" or sentiment in ("negative", "frustrated")

    def check_sla_retry_limit(self, retry_count: int) -> bool:
        """Check if we've exceeded the SLA retry limit for the same intent."""
        return retry_count >= self.settings.sla_max_retries
