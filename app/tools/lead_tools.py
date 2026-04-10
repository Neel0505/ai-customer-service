"""Lead and escalation tools for LLM function calling."""

from __future__ import annotations

import json
from typing import Any

from app.tools.registry import ToolRegistry


def register_lead_tools(registry: ToolRegistry, qualify_callback):
    """Register lead qualification tools."""

    async def qualify_lead(
        budget_confirmed: bool | None = None,
        budget_range: str | None = None,
        is_decision_maker: bool | None = None,
        role_title: str | None = None,
        need_identified: bool | None = None,
        pain_points: list[str] | None = None,
        timeline: str | None = None,
        timeline_days: int | None = None,
    ) -> str:
        result = await qualify_callback(
            budget=budget_confirmed,
            budget_range=budget_range,
            authority=is_decision_maker,
            role_title=role_title,
            need=need_identified,
            pain_points=pain_points,
            timeline=timeline,
            timeline_days=timeline_days,
        )
        return json.dumps(result, indent=2)

    registry.register(
        name="qualify_lead",
        description="Record lead qualification data (BANT framework). Call this when you've extracted budget, authority, need, or timeline information from the conversation.",
        parameters={
            "type": "object",
            "properties": {
                "budget_confirmed": {"type": "boolean", "description": "Has the lead confirmed a budget?"},
                "budget_range": {"type": "string", "description": "Budget range (e.g., '₹2000-5000')"},
                "is_decision_maker": {"type": "boolean", "description": "Is this person the decision maker?"},
                "role_title": {"type": "string", "description": "Their role or title"},
                "need_identified": {"type": "boolean", "description": "Has a clear need been identified?"},
                "pain_points": {"type": "array", "items": {"type": "string"}, "description": "List of pain points"},
                "timeline": {"type": "string", "description": "Timeline (e.g., 'ASAP', 'next quarter')"},
                "timeline_days": {"type": "integer", "description": "Estimated days to purchase decision"},
            },
        },
        handler=qualify_lead,
    )


def register_escalation_tools(registry: ToolRegistry, escalate_callback):
    """Register the escalate_to_human tool."""

    async def escalate_to_human(reason: str) -> str:
        result = await escalate_callback(reason)
        return result

    registry.register(
        name="escalate_to_human",
        description="Escalate the conversation to a human agent. Use when you cannot resolve the issue, the customer explicitly asks for a human, or the situation requires human judgment.",
        parameters={
            "type": "object",
            "properties": {
                "reason": {"type": "string", "description": "Why this is being escalated"}
            },
            "required": ["reason"],
        },
        handler=escalate_to_human,
    )


def register_knowledge_tools(registry: ToolRegistry, search_callback):
    """Register knowledge base search tool."""

    async def search_knowledge_base(query: str) -> str:
        results = await search_callback(query)
        return results

    registry.register(
        name="search_knowledge_base",
        description="Search the product knowledge base for information about products, policies, or FAQs. Use this when the customer asks about products, pricing, or company policies.",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"}
            },
            "required": ["query"],
        },
        handler=search_knowledge_base,
    )
