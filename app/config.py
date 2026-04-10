"""Application configuration — all environment variables parsed via Pydantic Settings."""

from __future__ import annotations

from enum import Enum
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentMode(str, Enum):
    CUSTOMER_SERVICE = "customer_service"
    SALES = "sales"
    BOTH = "both"


class Settings(BaseSettings):
    """Master configuration — loaded from .env file or environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Core Identity ──────────────────────────────────────────
    client_name: str = "Acme Corp"
    agent_name: str = "Alex"
    company_description: str = "We sell premium products online."
    agent_tone: str = "professional and friendly"
    agent_mode: AgentMode = AgentMode.BOTH
    custom_business_rules: str = ""

    # ── LLM (OpenRouter) ──────────────────────────────────────
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    llm_model: str = "openai/gpt-4o"
    llm_fast_model: str = "openai/gpt-4o-mini"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 1024
    embedding_model: str = "openai/text-embedding-3-small"

    # ── Shopify ────────────────────────────────────────────────
    shopify_store_domain: str = ""
    shopify_admin_api_token: str = ""
    shopify_api_version: str = "2025-01"
    shopify_webhook_secret: str = ""
    shopify_location_id: str = ""
    shopify_currency: str = "INR"
    shopify_return_policy_url: str = ""
    shopify_tracking_url_template: str = ""
    shopify_return_window_days: int = 7

    # ── Twilio WhatsApp ────────────────────────────────────────
    whatsapp_enabled: bool = False
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_number: str = ""

    # ── Email ──────────────────────────────────────────────────
    email_enabled: bool = False
    email_inbound_address: str = ""
    sendgrid_api_key: str = ""
    sendgrid_inbound_webhook_secret: str = ""
    email_from_address: str = ""
    email_from_name: str = "AI Assistant"
    email_brand_logo_url: str = ""
    email_brand_primary_color: str = "#2563EB"
    email_brand_company_name: str = ""

    # ── Instagram ──────────────────────────────────────────────
    instagram_enabled: bool = False
    instagram_access_token: str = ""
    instagram_page_id: str = ""
    instagram_app_secret: str = ""
    instagram_webhook_verify_token: str = ""

    # ── Escalation ─────────────────────────────────────────────
    escalation_email_to: str = ""
    escalation_email_from: str = ""
    escalation_lead_score_threshold: int = 70
    escalation_confidence_threshold: float = 0.4

    # ── Admin Dashboard ────────────────────────────────────────
    admin_username: str = "admin"
    admin_password: str = "changeme"

    # ── Simulator ──────────────────────────────────────────────
    simulator_enabled: bool = True

    # ── SLA ─────────────────────────────────────────────────────
    sla_first_response_seconds: int = 5
    sla_resolution_hours: int = 24
    sla_max_retries: int = 3
    sla_followup_hours: int = 24

    # ── Session ────────────────────────────────────────────────
    session_ttl_hours: int = 24

    # ── Database ───────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://agent:agent_dev@localhost:5432/omnichannel_agent"
    redis_url: str = "redis://localhost:6379/0"

    # ── Derived Properties ─────────────────────────────────────

    @property
    def shopify_base_url(self) -> str:
        return f"https://{self.shopify_store_domain}/admin/api/{self.shopify_api_version}"

    @property
    def session_ttl_seconds(self) -> int:
        return self.session_ttl_hours * 3600


@lru_cache
def get_settings() -> Settings:
    """Cached singleton for app settings."""
    return Settings()
