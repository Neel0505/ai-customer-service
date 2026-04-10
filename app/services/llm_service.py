"""LLM service — OpenRouter (OpenAI-compatible) SDK calls, prompt assembly, and tool execution."""

from __future__ import annotations

import json
import logging
from typing import Any

import tiktoken
from openai import AsyncOpenAI

from app.config import get_settings
from app.utils.error_handler import LLMError, retry_async

logger = logging.getLogger(__name__)


class LLMService:
    """Handles all LLM interactions via OpenRouter (OpenAI-compatible SDK)."""

    def __init__(self):
        settings = get_settings()
        self.client = AsyncOpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            default_headers={
                "HTTP-Referer": f"https://{settings.client_name.lower().replace(' ', '')}.com",
                "X-Title": settings.client_name,
            },
        )
        self.model = settings.llm_model
        self.fast_model = settings.llm_fast_model
        self.temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens
        self.embedding_model = settings.embedding_model
        try:
            self.tokenizer = tiktoken.encoding_for_model(self.model)
        except KeyError:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")

    # ── Chat Completion ────────────────────────────────────────

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Make a chat completion call to OpenAI.

        Returns the full response message dict including any tool_calls.
        """
        model = model or self.model
        temperature = temperature if temperature is not None else self.temperature
        max_tokens = max_tokens or self.max_tokens

        async def _call():
            kwargs: dict[str, Any] = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"

            response = await self.client.chat.completions.create(**kwargs)
            choice = response.choices[0]

            result: dict[str, Any] = {
                "role": "assistant",
                "content": choice.message.content or "",
                "tool_calls": [],
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0,
                },
            }

            if choice.message.tool_calls:
                result["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in choice.message.tool_calls
                ]

            return result

        try:
            return await retry_async(_call, max_retries=3, backoff_base=1.0)
        except Exception as e:
            logger.error("LLM call failed after retries: %s", e)
            raise LLMError(str(e), should_escalate=True)

    # ── Fast Classification Call ───────────────────────────────

    async def classify(self, system_prompt: str, user_text: str) -> dict[str, Any]:
        """Use the fast model (GPT-4o-mini) for intent classification.

        Returns parsed JSON from the model response.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ]
        result = await self.chat_completion(
            messages=messages,
            model=self.fast_model,
            temperature=0.1,
            max_tokens=256,
        )
        # Parse JSON from response
        content = result["content"].strip()
        # Handle markdown code blocks
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.warning("Could not parse classifier response as JSON: %s", content)
            return {"intent": "general", "confidence": 0.5, "mode": "general"}

    # ── Embeddings ─────────────────────────────────────────────

    async def embed_text(self, text: str) -> list[float]:
        """Generate an embedding vector for a text chunk."""
        try:
            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=text,
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error("Embedding failed: %s", e)
            raise LLMError(f"Embedding failed: {e}")

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts in one API call."""
        try:
            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=texts,
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error("Batch embedding failed: %s", e)
            raise LLMError(f"Batch embedding failed: {e}")

    # ── Token Counting ─────────────────────────────────────────

    def count_tokens(self, text: str) -> int:
        """Count tokens in a text string."""
        return len(self.tokenizer.encode(text))

    def count_messages_tokens(self, messages: list[dict[str, Any]]) -> int:
        """Approximate token count for a messages array."""
        total = 0
        for msg in messages:
            total += 4  # message overhead
            for key, value in msg.items():
                if isinstance(value, str):
                    total += self.count_tokens(value)
        total += 2  # reply priming
        return total

    # ── Prompt Assembly ────────────────────────────────────────

    def build_system_prompt(
        self,
        channel: str,
        mode: str,
        rag_context: str | None = None,
        identity: dict[str, Any] | None = None,
    ) -> str:
        """Assemble the full system prompt from config + dynamic context."""
        settings = get_settings()

        tone_overrides = {
            "instagram": "Use a casual, emoji-friendly tone. Keep responses concise and engaging.",
            "whatsapp": "Be clear and conversational. Use simple language.",
            "email": "Be polished and professional. Use proper formatting.",
            "simulator": "Be helpful and natural.",
        }

        mode_instructions = {
            "sales": (
                "You are in SALES mode. Your primary goals are:\n"
                "- Qualify leads using the BANT framework (Budget, Authority, Need, Timeline)\n"
                "- Build rapport before pitching products\n"
                "- Handle objections gracefully\n"
                "- Guide interested leads toward a purchase or demo booking\n"
                "- Use the qualify_lead tool to record qualification data"
            ),
            "customer_service": (
                "You are in CUSTOMER SERVICE mode. Your primary goals are:\n"
                "- Resolve customer issues quickly and empathetically\n"
                "- Look up orders, tracking info, and customer data using Shopify tools\n"
                "- Handle complaints with the empathy-first protocol\n"
                "- Escalate to human when you cannot resolve an issue"
            ),
            "general": (
                "Determine if this conversation is sales-related or customer-service-related "
                "and adjust your approach accordingly."
            ),
        }

        prompt_parts = [
            f"You are {settings.agent_name}, an AI assistant for {settings.client_name}.",
            settings.company_description,
            f"Your tone: {settings.agent_tone}",
            tone_overrides.get(channel, ""),
            "",
            mode_instructions.get(mode, mode_instructions["general"]),
            "",
            "CRITICAL RULES:",
            "- Never claim to be human unless directly and sincerely asked.",
            "- Never make up information. If unsure, say so and offer to connect with a team member.",
            "- Do not discuss competitors.",
            "- All pricing must come from Shopify product data — never quote from memory.",
            "- If the user is angry or upset, acknowledge their frustration before resolving.",
            "- If a conversation requires human intervention, use the escalate_to_human tool.",
            f"- Currency: {settings.shopify_currency}",
        ]

        if settings.custom_business_rules:
            prompt_parts.append("")
            prompt_parts.append("ADDITIONAL BUSINESS RULES:")
            for rule in settings.custom_business_rules.split("\n"):
                rule = rule.strip()
                if rule:
                    prompt_parts.append(f"- {rule}")

        if rag_context:
            prompt_parts.append("")
            prompt_parts.append("RELEVANT PRODUCT INFORMATION (from catalog):")
            prompt_parts.append(rag_context)

        if identity:
            prompt_parts.append("")
            prompt_parts.append("CUSTOMER CONTEXT:")
            if identity.get("name"):
                prompt_parts.append(f"- Name: {identity['name']}")
            if identity.get("email"):
                prompt_parts.append(f"- Email: {identity['email']}")
            if identity.get("shopify_customer_id"):
                prompt_parts.append("- Existing Shopify customer: Yes")

        return "\n".join(prompt_parts)

    def trim_history(
        self,
        history: list[dict[str, Any]],
        max_tokens: int = 8000,
    ) -> list[dict[str, Any]]:
        """Trim conversation history to fit within token budget.

        If history exceeds max_tokens, keep the last 5 messages and
        summarize the rest into a single context message.
        """
        total = self.count_messages_tokens(history)
        if total <= max_tokens:
            return history

        # Keep last 5 messages, summarize earlier ones
        if len(history) <= 5:
            return history

        recent = history[-5:]
        older = history[:-5]

        # Create a summary of older messages
        summary_parts = []
        for msg in older:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:200]
            summary_parts.append(f"[{role}]: {content}")

        summary = "EARLIER CONVERSATION SUMMARY:\n" + "\n".join(summary_parts)

        return [{"role": "system", "content": summary}] + recent
