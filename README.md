# 🤖 AI Omnichannel Customer Service & Sales Agent

AI-powered customer service and sales agent integrated with **Shopify**, supporting **WhatsApp**, **Email**, and **Instagram** channels.

## Features

- **Autonomous AI Agent** — GPT-4o powered, with tool calling for Shopify operations
- **3 Channels** — WhatsApp (interactive buttons/lists), Email (branded HTML), Instagram DMs
- **Shopify Integration** — Orders, products, returns, inventory, customers, draft orders
- **RAG Knowledge Base** — pgvector semantic search over product catalog
- **BANT Lead Scoring** — Automatic lead qualification and escalation
- **Smart Escalation** — 7 trigger types (sentiment, score, retries, legal, VIP, etc.)
- **Admin Dashboard** — Real-time WebSocket updates, full debug conversation viewer
- **Simulator** — Browser-based chat UI for testing without real APIs

## Quick Start (Local Development)

### Prerequisites

```bash
# Install Postgres + pgvector + Redis via Homebrew
brew install postgresql@16 pgvector redis

# Start services
brew services start postgresql@16
brew services start redis

# Create database and enable pgvector
createdb omnichannel_agent
psql omnichannel_agent -c "CREATE EXTENSION vector;"
```

### Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Run the setup wizard (creates .env, runs migrations, ingests products)
python scripts/setup_wizard.py

# Start the dev server (spins up uvicorn AND ngrok tunnel automatically)
python3 scripts/dev.py
```

### Access

| URL | Description |
|-----|-------------|
| `http://localhost:8000/health` | Health check |
| `http://localhost:8000/admin/` | Admin dashboard (basic auth) |
| `http://localhost:8000/simulator` | Chat simulator (basic auth) |
| `http://localhost:8000/docs` | API docs (Swagger) |

## Deploy to Railway

1. Push your repo to GitHub
2. Create a new project on [Railway](https://railway.app)
3. Add **PostgreSQL** and **Redis** services
4. Connect your GitHub repo
5. Set all env vars from `.env` in Railway dashboard
6. **Custom Domain**: Settings → Networking → Custom Domain → add `api.clientname.com` → update DNS CNAME

### Webhook Registration

After deployment, register these URLs with the respective platforms:

| Platform | URL |
|----------|-----|
| WhatsApp (Twilio) | `https://api.clientname.com/webhooks/twilio/whatsapp` |
| Email (SendGrid) | `https://api.clientname.com/webhooks/email` |
| Instagram (Meta) | `https://api.clientname.com/webhooks/instagram` |
| Shopify | `https://api.clientname.com/webhooks/shopify` |

## Architecture

```
FastAPI Monolith
├── Webhooks (Twilio WhatsApp, Email, Instagram, Shopify)
├── Orchestrator (12-step pipeline)
├── LLM Service (OpenAI GPT-4o + tools)
├── RAG Service (pgvector semantic search)
├── Channel Adapters (Twilio WhatsApp, Email, Instagram, Simulator)
├── Sales Engine (BANT lead scoring)
├── Escalation Service (7 triggers + email alerts)
└── Admin Dashboard (WebSocket live updates)
```

## License

Private — All rights reserved.
