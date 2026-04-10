"""Orchestration engine — the 'brain' that processes every inbound message."""

from __future__ import annotations

import logging
import time
from typing import Any

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.schemas.nlp_message import NLPMessage, OutboundMessage, ChannelEnum
from app.services.conversation_service import ConversationService
from app.services.customer_service_engine import CustomerServiceEngine
from app.services.escalation_service import EscalationService
from app.services.identity_service import IdentityService
from app.services.intent_classifier import IntentClassifier
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService
from app.services.sales_engine import SalesEngine
from app.services.session_service import SessionService
from app.services.shopify_service import ShopifyService
from app.tools.lead_tools import register_escalation_tools, register_knowledge_tools, register_lead_tools
from app.tools.registry import ToolRegistry
from app.tools.shopify_tools import register_shopify_tools
from app.utils.error_handler import FALLBACK_MESSAGE

logger = logging.getLogger(__name__)


class Orchestrator:
    """Central orchestration engine — processes every inbound message through the 12-step pipeline."""

    def __init__(self, db: AsyncSession, redis: aioredis.Redis):
        self.db = db
        self.settings = get_settings()

        # Initialize all services
        self.llm = LLMService()
        self.shopify = ShopifyService()
        self.session_service = SessionService(redis)
        self.identity_service = IdentityService(db, self.session_service, self.shopify)
        self.intent_classifier = IntentClassifier(self.llm)
        self.rag = RAGService(db, self.llm)
        self.sales_engine = SalesEngine(db)
        self.cs_engine = CustomerServiceEngine()
        self.escalation_service = EscalationService(db)
        self.conversation_service = ConversationService(db)

        # Build tool registry
        self.tool_registry = ToolRegistry()
        self._register_tools()

    def _register_tools(self):
        """Register all LLM-callable tools."""
        register_shopify_tools(self.tool_registry, self.shopify)

        # Lead tools (with callback placeholder — set per-request)
        self._lead_qualify_callback = None
        self._escalate_callback = None
        self._knowledge_callback = None

    async def process_message(self, nlp_message: NLPMessage) -> OutboundMessage:
        """Process an inbound message through the full pipeline.

        This is the main entry point — called by every webhook handler.
        """
        start_time = time.time()
        debug_info: dict[str, Any] = {}

        try:
            return await self._process_pipeline(nlp_message, debug_info, start_time)
        except Exception as e:
            logger.exception("Orchestrator error: %s", e)
            # Attempt to send fallback message
            return OutboundMessage(
                text=FALLBACK_MESSAGE,
                channel=nlp_message.channel,
                user_id=nlp_message.user_id,
                debug={"error": str(e)},
            )

    async def _process_pipeline(
        self, msg: NLPMessage, debug: dict[str, Any], start_time: float
    ) -> OutboundMessage:
        """The 12-step orchestration pipeline."""

        # ── Step 1: Load or create session ─────────────────────
        session = await self.session_service.get_or_create(msg.channel.value, msg.user_id)
        conversation_id = session["conversation_id"]

        # ── Step 2: Resolve customer identity ──────────────────
        identity = await self.identity_service.resolve(
            msg.channel.value,
            msg.user_id,
            email=msg.metadata.get("email"),
        )
        session["contact_id"] = identity.get("contact_id")
        session["identity"] = identity
        debug["identity"] = identity

        # ── Step 3: Classify intent ────────────────────────────
        intent_result = await self.intent_classifier.classify(msg.text)
        debug["intent"] = {
            "intent": intent_result.intent,
            "confidence": intent_result.confidence,
            "mode": intent_result.mode,
        }

        # Track retry count for same intent
        if session.get("last_intent") == intent_result.intent:
            await self.session_service.increment_retry(session)
        else:
            await self.session_service.reset_retry(session)

        # ── Step 4: Ensure conversation exists in DB ───────────
        # (Must happen BEFORE escalation check, which inserts into escalations table with FK to conversations)
        contact_id = identity.get("contact_id", "")
        await self.conversation_service.get_or_create_conversation(
            conversation_id=conversation_id,
            contact_id=contact_id,
            channel=msg.channel.value,
            mode=intent_result.mode,
        )

        # ── Step 5: Check escalation triggers ──────────────────
        should_escalate, trigger_type, reason = self.escalation_service.check_triggers(
            text=msg.text,
            intent=intent_result.intent,
            confidence=intent_result.confidence,
            sentiment_history=session.get("sentiment_history", []),
            lead_score=None,  # Will check after lead scoring
            retry_count=session.get("retry_count", 0),
            contact_tags=None,
        )

        if should_escalate and trigger_type:
            return await self._handle_escalation(
                session, identity, conversation_id, trigger_type, reason, msg, debug
            )

        # ── Step 6: RAG retrieval ──────────────────────────────
        rag_context_str = ""
        if intent_result.needs_rag:
            rag_results = await self.rag.search(msg.text)
            rag_context_str = self.rag.format_context(rag_results)
            debug["rag_results"] = [
                {"title": r["title"], "similarity": round(r["similarity"], 3)}
                for r in rag_results
            ]

        # ── Step 7: Assemble prompt ────────────────────────────
        system_prompt = self.llm.build_system_prompt(
            channel=msg.channel.value,
            mode=intent_result.mode,
            rag_context=rag_context_str if rag_context_str else None,
            identity=identity,
        )

        # Add complaint protocol if needed
        if self.cs_engine.should_add_complaint_protocol(
            intent_result.intent, session.get("sentiment_history", [""])[-1] if session.get("sentiment_history") else None
        ):
            system_prompt += self.cs_engine.get_complaint_instructions()

        # Add return instructions if needed
        if intent_result.intent == "return_request":
            system_prompt += self.cs_engine.get_return_instructions(
                self.settings.shopify_return_window_days,
                self.settings.shopify_return_policy_url,
            )

        # Build messages array
        history = self.llm.trim_history(session.get("history", []))
        messages = [
            {"role": "system", "content": system_prompt},
            *history,
            {"role": "user", "content": msg.text},
        ]

        # ── Step 8: Call LLM (call #1) with tools ─────────────
        # Build dynamic tool registry with callbacks for this request
        tool_registry = self._build_request_tools(session, identity, conversation_id)

        llm_response = await self.llm.chat_completion(
            messages=messages,
            tools=tool_registry.get_definitions(),
        )
        debug["llm_model"] = llm_response.get("model")
        debug["tokens"] = llm_response.get("usage", {})

        # ── Step 9: Execute tool calls ─────────────────────────
        all_tool_calls = []
        if llm_response.get("tool_calls"):
            tool_results = await tool_registry.execute_all(llm_response["tool_calls"])
            all_tool_calls = [
                {"name": tc["function"]["name"], "result": tr["content"][:500]}
                for tc, tr in zip(llm_response["tool_calls"], tool_results)
            ]
            debug["tool_calls"] = all_tool_calls

            # Call #2: Feed tool results back to LLM
            messages.append(llm_response)  # assistant message with tool_calls
            messages.extend(tool_results)   # tool result messages
            llm_response = await self.llm.chat_completion(
                messages=messages,
                tools=tool_registry.get_definitions(),
            )
            debug["tokens"]["total_tokens"] = (
                debug["tokens"].get("total_tokens", 0) +
                llm_response.get("usage", {}).get("total_tokens", 0)
            )

        response_text = llm_response.get("content", FALLBACK_MESSAGE)

        # ── Step 10: Update lead score if sales mode ───────────
        lead_score = None
        if intent_result.mode == "sales" and contact_id:
            try:
                lead = await self.sales_engine.get_or_create_lead(contact_id, conversation_id)
                msg_count = len(session.get("history", [])) // 2 + 1
                lead.score = self.sales_engine.calculate_score(lead, msg_count)
                lead_score = lead.score
                debug["lead_score"] = lead_score

                if self.sales_engine.should_escalate(lead_score):
                    # Escalate hot lead
                    return await self._handle_escalation(
                        session, identity, conversation_id,
                        trigger_type=__import__("app.models.escalation", fromlist=["EscalationTrigger"]).EscalationTrigger.LEAD_SCORE,
                        reason=f"Hot lead: score {lead_score}",
                        msg=msg, debug=debug,
                        append_response=response_text,
                    )
            except Exception as e:
                logger.warning("Lead scoring failed: %s", e)

        # ── Step 11: Update session in Redis ───────────────────
        # Detect sentiment (simple heuristic — could use LLM later)
        sentiment = self._detect_simple_sentiment(msg.text)
        await self.session_service.update(
            session,
            inbound_text=msg.text,
            outbound_text=response_text,
            intent=intent_result.intent,
            sentiment=sentiment,
        )

        # ── Step 12: Persist to Postgres ───────────────────────
        await self.conversation_service.save_inbound_message(
            conversation_id=conversation_id,
            content=msg.text,
            intent=intent_result.intent,
            sentiment=sentiment,
            channel_message_id=msg.message_id,
        )
        await self.conversation_service.save_outbound_message(
            conversation_id=conversation_id,
            content=response_text,
            intent=intent_result.intent,
            tool_calls=all_tool_calls if all_tool_calls else None,
            llm_model=llm_response.get("model"),
            token_count=llm_response.get("usage", {}).get("total_tokens"),
        )

        # ── Build response ─────────────────────────────────────
        debug["response_time_ms"] = round((time.time() - start_time) * 1000)

        return OutboundMessage(
            text=response_text,
            channel=msg.channel,
            user_id=msg.user_id,
            debug=debug,
        )

    def _build_request_tools(
        self, session: dict, identity: dict, conversation_id: str
    ) -> ToolRegistry:
        """Build a fresh tool registry with request-scoped callbacks."""
        registry = ToolRegistry()
        register_shopify_tools(registry, self.shopify)

        # Lead qualification callback
        async def qualify_callback(**kwargs):
            contact_id = identity.get("contact_id", "")
            if not contact_id:
                return {"status": "no_contact"}
            lead = await self.sales_engine.get_or_create_lead(contact_id, conversation_id)
            msg_count = len(session.get("history", [])) // 2 + 1
            lead = await self.sales_engine.update_qualification(lead, message_count=msg_count, **kwargs)
            return {"score": lead.score, "status": lead.status.value}

        register_lead_tools(registry, qualify_callback)

        # Escalation callback
        async def escalate_callback(reason: str):
            from app.models.escalation import EscalationTrigger
            contact_id = identity.get("contact_id", "")
            esc = await self.escalation_service.create_escalation(
                conversation_id=conversation_id,
                contact_id=contact_id,
                trigger_type=EscalationTrigger.USER_REQUEST,
                reason=reason,
                context_summary="\n".join(
                    f"[{m['role']}]: {m['content'][:200]}" for m in session.get("history", [])[-5:]
                ),
            )
            await self.escalation_service.send_escalation_email(
                esc, identity.get("name"), session.get("channel", ""), session.get("history", [])
            )
            await self.conversation_service.mark_escalated(conversation_id, reason)
            return self.escalation_service.get_hold_message()

        register_escalation_tools(registry, escalate_callback)

        # Knowledge base search callback
        async def knowledge_callback(query: str):
            results = await self.rag.search(query)
            return self.rag.format_context(results)

        register_knowledge_tools(registry, knowledge_callback)

        return registry

    async def _handle_escalation(
        self,
        session: dict,
        identity: dict,
        conversation_id: str,
        trigger_type,
        reason: str,
        msg: NLPMessage,
        debug: dict,
        append_response: str | None = None,
    ) -> OutboundMessage:
        """Handle an escalation event."""
        contact_id = identity.get("contact_id", "")

        esc = await self.escalation_service.create_escalation(
            conversation_id=conversation_id,
            contact_id=contact_id,
            trigger_type=trigger_type,
            reason=reason,
            context_summary="\n".join(
                f"[{m['role']}]: {m['content'][:200]}" for m in session.get("history", [])[-5:]
            ),
        )
        await self.escalation_service.send_escalation_email(
            esc, identity.get("name"), msg.channel.value, session.get("history", [])
        )
        await self.conversation_service.mark_escalated(conversation_id, reason)

        debug["escalated"] = True
        debug["escalation_reason"] = reason

        hold_msg = self.escalation_service.get_hold_message()
        response_text = f"{append_response}\n\n{hold_msg}" if append_response else hold_msg

        await self.session_service.update(
            session, inbound_text=msg.text, outbound_text=response_text
        )

        return OutboundMessage(
            text=response_text,
            channel=msg.channel,
            user_id=msg.user_id,
            debug=debug,
        )

    @staticmethod
    def _detect_simple_sentiment(text: str) -> str:
        """Very basic sentiment detection via keywords (placeholder for LLM-based)."""
        text_lower = text.lower()
        frustrated_words = [
            "frustrated", "angry", "terrible", "worst", "horrible",
            "unacceptable", "disgusted", "furious", "disappointed", "useless",
            "waste", "scam", "pathetic", "ridiculous",
        ]
        negative_words = [
            "unhappy", "not happy", "bad", "issue", "problem", "broken",
            "wrong", "complaint", "annoyed", "upset",
        ]
        positive_words = [
            "thank", "great", "excellent", "awesome", "perfect", "love",
            "wonderful", "happy", "satisfied", "impressed",
        ]

        if any(w in text_lower for w in frustrated_words):
            return "frustrated"
        if any(w in text_lower for w in negative_words):
            return "negative"
        if any(w in text_lower for w in positive_words):
            return "positive"
        return "neutral"
