"""Intent classifier — fast GPT-4o-mini classification of inbound messages."""

from __future__ import annotations

import logging
from typing import Any

from app.schemas.nlp_message import IntentResult
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

CLASSIFICATION_PROMPT = """You are an intent classifier for a customer service and sales AI agent.

Classify the following user message into EXACTLY ONE of these intent categories:

CUSTOMER SERVICE intents:
- order_inquiry: asking about order status, tracking, delivery
- return_request: wants to return, exchange, or get a refund
- product_info: asking about product specs, availability, features, comparisons
- technical_support: setup help, errors, troubleshooting
- billing: invoices, payment issues, payment methods
- complaint: unhappy about service, product, or experience
- appointment: booking, rescheduling, cancelling meetings or demos
- faq: general questions about hours, location, policies

SALES intents:
- sales_inquiry: interested in buying, pricing questions, comparing products for purchase

OTHER intents:
- greeting: hello, hi, hey, good morning, etc. — a simple greeting or conversation starter
- human_request: explicitly asking to talk to a real person or human agent
- spam: gibberish, irrelevant, or spam content

Respond with ONLY a JSON object like this:
{
  "intent": "<one of the above categories>",
  "confidence": <0.0 to 1.0>,
  "mode": "<sales or customer_service>",
  "needs_rag": <true if product/knowledge info would help, false otherwise>
}

Rules:
- sales_inquiry and product_info with purchase intent -> mode = "sales"
- Everything else -> mode = "customer_service"
- greeting -> mode = "general", confidence should be high (0.9+)
- human_request always gets confidence 1.0
- If the message is ambiguous, choose the most likely intent and lower the confidence
"""


class IntentClassifier:
    """Classifies inbound messages using GPT-4o-mini for fast, cheap intent detection."""

    def __init__(self, llm_service: LLMService):
        self.llm = llm_service

    async def classify(self, text: str) -> IntentResult:
        """Classify a user message into an intent category."""
        if not text.strip():
            return IntentResult(
                intent="spam", confidence=1.0, mode="general", needs_rag=False
            )

        text_lower = text.strip().lower()

        # Check for greetings (fast path — no LLM call needed)
        greeting_keywords = [
            "hi", "hello", "hey", "good morning", "good afternoon",
            "good evening", "howdy", "hiya", "greetings", "yo", "sup",
            "what's up", "whats up",
        ]
        if text_lower in greeting_keywords or any(text_lower.startswith(g + " ") or text_lower.startswith(g + "!") for g in greeting_keywords):
            return IntentResult(
                intent="greeting", confidence=0.95, mode="general", needs_rag=False
            )

        # Check for explicit human request keywords (fast path)
        human_keywords = [
            "human", "agent", "person", "talk to someone",
            "real person", "speak to someone", "speak to a person",
            "representative", "live agent",
        ]
        if any(kw in text_lower for kw in human_keywords):
            return IntentResult(
                intent="human_request", confidence=1.0, mode="customer_service", needs_rag=False
            )

        try:
            result = await self.llm.classify(CLASSIFICATION_PROMPT, text)
            return IntentResult(
                intent=result.get("intent", "faq"),
                confidence=result.get("confidence", 0.5),
                mode=result.get("mode", "general"),
                needs_rag=result.get("needs_rag", True),
            )
        except Exception as e:
            logger.warning("Intent classification failed, defaulting to general: %s", e)
            return IntentResult(
                intent="faq", confidence=0.7, mode="general", needs_rag=True
            )
