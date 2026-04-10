"""Sales engine — BANT lead qualification and scoring."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.lead import Lead, LeadStatus

logger = logging.getLogger(__name__)


class SalesEngine:
    """BANT-based lead qualification and scoring engine."""

    # Score weights
    SCORES = {
        "budget_confirmed": 25,
        "decision_maker": 20,
        "need_identified": 15,
        "timeline_30": 20,
        "demo_requested": 30,
        "pricing_interest": 10,
        "message_bonus": 5,  # per message, cap 20
        "frustrated": -10,
    }
    MESSAGE_BONUS_CAP = 20

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()

    async def get_or_create_lead(
        self, contact_id: str, conversation_id: str
    ) -> Lead:
        """Get existing lead for this conversation or create a new one."""
        stmt = select(Lead).where(
            Lead.conversation_id == conversation_id,
            Lead.contact_id == contact_id,
        )
        result = await self.db.execute(stmt)
        lead = result.scalar_one_or_none()

        if not lead:
            lead = Lead(contact_id=contact_id, conversation_id=conversation_id)
            self.db.add(lead)
            await self.db.flush()

        return lead

    def calculate_score(self, lead: Lead, message_count: int = 0) -> int:
        """Calculate lead score from all BANT signals."""
        score = 0

        if lead.budget_confirmed:
            score += self.SCORES["budget_confirmed"]
        if lead.is_decision_maker:
            score += self.SCORES["decision_maker"]
        if lead.need_identified:
            score += self.SCORES["need_identified"]
        if lead.timeline_days is not None and lead.timeline_days <= 30:
            score += self.SCORES["timeline_30"]

        # Message engagement bonus
        msg_bonus = min(message_count * self.SCORES["message_bonus"], self.MESSAGE_BONUS_CAP)
        score += msg_bonus

        return max(0, min(100, score))

    async def update_qualification(
        self,
        lead: Lead,
        budget: bool | None = None,
        budget_range: str | None = None,
        authority: bool | None = None,
        role_title: str | None = None,
        need: bool | None = None,
        pain_points: list[str] | None = None,
        timeline: str | None = None,
        timeline_days: int | None = None,
        message_count: int = 0,
    ) -> Lead:
        """Update BANT fields and recalculate score."""
        if budget is not None:
            lead.budget_confirmed = budget
        if budget_range:
            lead.budget_range = budget_range
        if authority is not None:
            lead.is_decision_maker = authority
        if role_title:
            lead.role_title = role_title
        if need is not None:
            lead.need_identified = need
        if pain_points:
            existing = lead.pain_points or []
            lead.pain_points = list(set(existing + pain_points))
        if timeline:
            lead.timeline = timeline
        if timeline_days is not None:
            lead.timeline_days = timeline_days

        # Recalculate score
        lead.score = self.calculate_score(lead, message_count)

        # Update status based on score
        lead.status = self.get_status(lead.score)

        await self.db.flush()
        return lead

    def get_status(self, score: int) -> LeadStatus:
        """Determine lead status from score."""
        threshold = self.settings.escalation_lead_score_threshold
        if score >= threshold:
            return LeadStatus.ESCALATED
        elif score >= 40:
            return LeadStatus.NURTURING
        else:
            return LeadStatus.NEW

    def should_escalate(self, score: int) -> bool:
        """Check if lead score triggers escalation."""
        return score >= self.settings.escalation_lead_score_threshold
