#!/usr/bin/env python3
"""Interactive CLI setup wizard — configure a new client deployment."""

from __future__ import annotations

import os
import sys


def ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    val = input(f"  {prompt}{suffix}: ").strip()
    return val or default


def ask_bool(prompt: str, default: bool = False) -> bool:
    suffix = " [Y/n]" if default else " [y/N]"
    val = input(f"  {prompt}{suffix}: ").strip().lower()
    if not val:
        return default
    return val in ("y", "yes")


def ask_multiline(prompt: str) -> str:
    print(f"  {prompt} (enter empty line to finish):")
    lines = []
    while True:
        line = input("    > ").strip()
        if not line:
            break
        lines.append(line)
    return "\\n".join(lines)


def main():
    print("\n" + "=" * 60)
    print("  🤖 AI Omnichannel Agent — Setup Wizard")
    print("=" * 60)
    print()

    env_vars: dict[str, str] = {}

    # ── Core Identity ──────────────────────────────────────
    print("📋 CORE IDENTITY")
    print("-" * 40)
    env_vars["CLIENT_NAME"] = ask("Client/Company name", "Acme Corp")
    env_vars["AGENT_NAME"] = ask("Agent name (the AI's name)", "Alex")
    env_vars["COMPANY_DESCRIPTION"] = ask("Company description", "We sell premium products online.")
    env_vars["AGENT_TONE"] = ask("Agent tone", "professional and friendly")
    env_vars["AGENT_MODE"] = ask("Agent mode (customer_service/sales/both)", "both")

    print()
    print("📜 CUSTOM BUSINESS RULES")
    print("-" * 40)
    rules = ask_multiline("Enter your business rules (one per line)")
    env_vars["CUSTOM_BUSINESS_RULES"] = rules
    print()

    # ── LLM ────────────────────────────────────────────────
    print("🧠 LLM CONFIGURATION (OpenRouter)")
    print("-" * 40)
    env_vars["OPENROUTER_API_KEY"] = ask("OpenRouter API key", "")
    env_vars["OPENROUTER_BASE_URL"] = ask("OpenRouter base URL", "https://openrouter.ai/api/v1")
    env_vars["LLM_MODEL"] = ask("Primary LLM model", "openai/gpt-4o")
    env_vars["LLM_FAST_MODEL"] = ask("Fast model (intent classifier)", "openai/gpt-4o-mini")
    env_vars["LLM_TEMPERATURE"] = ask("Temperature", "0.3")
    env_vars["LLM_MAX_TOKENS"] = ask("Max tokens per response", "1024")
    env_vars["EMBEDDING_MODEL"] = ask("Embedding model", "openai/text-embedding-3-small")
    print()

    # ── Shopify ────────────────────────────────────────────
    print("🛍️  SHOPIFY")
    print("-" * 40)
    env_vars["SHOPIFY_STORE_DOMAIN"] = ask("Shopify store domain (e.g. store.myshopify.com)")
    env_vars["SHOPIFY_ADMIN_API_TOKEN"] = ask("Shopify Admin API token (shpat_...)")
    env_vars["SHOPIFY_API_VERSION"] = ask("API version", "2025-01")
    env_vars["SHOPIFY_WEBHOOK_SECRET"] = ask("Webhook secret")
    env_vars["SHOPIFY_LOCATION_ID"] = ask("Location ID (for inventory)")
    env_vars["SHOPIFY_CURRENCY"] = ask("Currency", "INR")
    env_vars["SHOPIFY_RETURN_POLICY_URL"] = ask("Return policy URL", "")
    env_vars["SHOPIFY_TRACKING_URL_TEMPLATE"] = ask("Tracking URL template (use {tracking_number})", "")
    env_vars["SHOPIFY_RETURN_WINDOW_DAYS"] = ask("Return window (days)", "7")
    print()

    # ── Channels ───────────────────────────────────────────
    # WhatsApp
    if ask_bool("Enable WhatsApp?", True):
        print("📱 WHATSAPP")
        print("-" * 40)
        env_vars["WHATSAPP_ENABLED"] = "true"
        env_vars["TWILIO_ACCOUNT_SID"] = ask("Twilio Account SID")
        env_vars["TWILIO_AUTH_TOKEN"] = ask("Twilio Auth Token")
        env_vars["TWILIO_WHATSAPP_NUMBER"] = ask("Twilio WhatsApp Number (e.g. +14155238886)")
        print()
    else:
        env_vars["WHATSAPP_ENABLED"] = "false"

    # Email
    if ask_bool("Enable Email?", True):
        print("📧 EMAIL")
        print("-" * 40)
        env_vars["EMAIL_ENABLED"] = "true"
        env_vars["EMAIL_INBOUND_ADDRESS"] = ask("Inbound email address")
        env_vars["SENDGRID_API_KEY"] = ask("SendGrid API key")
        env_vars["EMAIL_FROM_ADDRESS"] = ask("From email address")
        env_vars["EMAIL_FROM_NAME"] = ask("From name", f"{env_vars['AGENT_NAME']} from {env_vars['CLIENT_NAME']}")
        env_vars["EMAIL_BRAND_LOGO_URL"] = ask("Brand logo URL (optional)", "")
        env_vars["EMAIL_BRAND_PRIMARY_COLOR"] = ask("Brand primary color", "#2563EB")
        env_vars["EMAIL_BRAND_COMPANY_NAME"] = ask("Brand company name", env_vars["CLIENT_NAME"])
        print()
    else:
        env_vars["EMAIL_ENABLED"] = "false"

    # Instagram
    if ask_bool("Enable Instagram?", True):
        print("📸 INSTAGRAM")
        print("-" * 40)
        env_vars["INSTAGRAM_ENABLED"] = "true"
        env_vars["INSTAGRAM_ACCESS_TOKEN"] = ask("Access token")
        env_vars["INSTAGRAM_PAGE_ID"] = ask("Page ID")
        env_vars["INSTAGRAM_APP_SECRET"] = ask("App secret")
        env_vars["INSTAGRAM_WEBHOOK_VERIFY_TOKEN"] = ask("Webhook verify token")
        print()
    else:
        env_vars["INSTAGRAM_ENABLED"] = "false"

    # ── Escalation ─────────────────────────────────────────
    print("🚨 ESCALATION")
    print("-" * 40)
    env_vars["ESCALATION_EMAIL_TO"] = ask("Escalation email address")
    env_vars["ESCALATION_EMAIL_FROM"] = ask("Escalation from address", "alerts@" + env_vars.get("SHOPIFY_STORE_DOMAIN", ""))
    print()

    # ── Admin Dashboard ────────────────────────────────────
    print("🔒 ADMIN DASHBOARD")
    print("-" * 40)
    env_vars["ADMIN_USERNAME"] = ask("Admin username", "admin")
    env_vars["ADMIN_PASSWORD"] = ask("Admin password")
    print()

    # ── SLA ─────────────────────────────────────────────────
    print("⏱️  SLA SETTINGS")
    print("-" * 40)
    env_vars["SLA_MAX_RETRIES"] = ask("Max retries before escalation", "3")
    env_vars["SESSION_TTL_HOURS"] = ask("Session timeout (hours)", "24")
    print()

    # ── Database ───────────────────────────────────────────
    print("🗄️  DATABASE")
    print("-" * 40)
    env_vars["DATABASE_URL"] = ask(
        "PostgreSQL URL",
        "postgresql+asyncpg://agent:agent_dev@localhost:5432/omnichannel_agent"
    )
    env_vars["REDIS_URL"] = ask("Redis URL", "redis://localhost:6379/0")
    print()

    # ── Simulator ──────────────────────────────────────────
    env_vars["SIMULATOR_ENABLED"] = "true"

    # ── Write .env file ────────────────────────────────────
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    with open(env_path, "w") as f:
        for key, value in env_vars.items():
            f.write(f'{key}="{value}"\n')

    print("=" * 60)
    print(f"  ✅ .env file written to: {env_path}")
    print("=" * 60)
    print()

    # ── Post-setup steps ───────────────────────────────────
    if ask_bool("Run database migrations? (alembic upgrade head)", True):
        print("  Running migrations...")
        os.system("alembic upgrade head")
        print("  ✅ Migrations complete")

    if ask_bool("Run Shopify product ingestion now?", True):
        print("  Running product ingestion...")
        os.system(f"{sys.executable} -m scripts.ingest_shopify")
        print("  ✅ Ingestion complete")

    # ── Print summary ──────────────────────────────────────
    base_url = ask("Your deployment URL (for webhook registration)", "http://localhost:8000")

    print()
    print("=" * 60)
    print("  🎉 Setup Complete!")
    print("=" * 60)
    print()
    print("  📌 Register these webhook URLs:")
    print()
    if env_vars.get("WHATSAPP_ENABLED") == "true":
        print(f"    WhatsApp:  {base_url}/webhooks/twilio/whatsapp")
    if env_vars.get("EMAIL_ENABLED") == "true":
        print(f"    Email:     {base_url}/webhooks/email")
    if env_vars.get("INSTAGRAM_ENABLED") == "true":
        print(f"    Instagram: {base_url}/webhooks/instagram")
    print(f"    Shopify:   {base_url}/webhooks/shopify")
    print()
    print("  🚀 Start the server:")
    print("    uvicorn app.main:app --reload --port 8000")
    print()
    print("  🌐 Access:")
    print(f"    Dashboard:  {base_url}/admin")
    print(f"    Simulator:  {base_url}/simulator")
    print(f"    Health:     {base_url}/health")
    print()


if __name__ == "__main__":
    main()
