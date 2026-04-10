# AI Customer Service Agent

A production-ready AI agent that handles customer support and sales autonomously across multiple messaging platforms, built on top of Shopify's ecosystem.

> Built by **Neel Parikh**

## What it does

This project connects an LLM-powered agent to your Shopify store and lets it handle real customer conversations — order lookups, product questions, returns, and lead qualification — across WhatsApp, Email, and Instagram, without human intervention unless escalation is needed.

## Core Features

- **GPT-4o Agent** with tool-calling to perform live Shopify operations
- **Multi-channel support** — WhatsApp (buttons/lists), Email (HTML), Instagram DMs
- **RAG pipeline** — pgvector semantic search over your product catalog so the agent always has accurate product context
- **BANT lead scoring** — automatically qualifies inbound leads and routes hot ones
- **Escalation engine** — 7 trigger types including sentiment analysis, VIP detection, legal flags, and retry limits
- **Admin dashboard** — live WebSocket feed with full conversation debug view
- **Chat simulator** — test the agent in your browser without needing real API credentials

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python) |
| LLM | OpenAI GPT-4o |
| Database | PostgreSQL + pgvector |
| Cache / Queue | Redis |
| Channels | Twilio (WhatsApp), SendGrid (Email), Meta API (Instagram) |
| E-commerce | Shopify Admin API |
| Deployment | Railway + Docker |

## Getting Started

### Prerequisites

```bash
brew install postgresql@16 pgvector redis
brew services start postgresql@16
brew services start redis

createdb omnichannel_agent
psql omnichannel_agent -c "CREATE EXTENSION vector;"
```

### Install & Run

```bash
python3 -m venv .venv
source .venv/bin/activate

pip install -e ".[dev]"

python scripts/setup_wizard.py
python3 scripts/dev.py
```

### Local URLs

| Endpoint | Description |
|---|---|
| `http://localhost:8000/health` | Health check |
| `http://localhost:8000/admin/` | Admin dashboard |
| `http://localhost:8000/simulator` | Chat simulator |
| `http://localhost:8000/docs` | Swagger API docs |

## Deploying to Railway

1. Push this repo to GitHub
2. Create a new Railway project
3. Add **PostgreSQL** and **Redis** plugins
4. Link your GitHub repo
5. Set all variables from `.env.example` in the Railway dashboard
6. Point a custom domain via Settings → Networking

### Webhook URLs

| Platform | Webhook URL |
|---|---|
| WhatsApp (Twilio) | `https://api.yourdomain.com/webhooks/twilio/whatsapp` |
| Email (SendGrid) | `https://api.yourdomain.com/webhooks/email` |
| Instagram (Meta) | `https://api.yourdomain.com/webhooks/instagram` |
| Shopify | `https://api.yourdomain.com/webhooks/shopify` |

## Architecture
FastAPI Monolith
├── Webhook receivers      (Twilio, SendGrid, Meta, Shopify)
├── Orchestrator           (12-step processing pipeline)
├── LLM Service            (GPT-4o + Shopify tool definitions)
├── RAG Service            (pgvector similarity search)
├── Channel Adapters       (per-platform message formatting)
├── Sales Engine           (BANT scoring logic)
├── Escalation Service     (trigger detection + email alerts)
└── Admin Dashboard        (WebSocket live updates)

## License

MIT — feel free to use, modify, and build on this.
```
FastAPI Monolith
+-- Webhook receivers      (Twilio, SendGrid, Meta, Shopify)
+-- Orchestrator           (12-step processing pipeline)
+-- LLM Service            (GPT-4o + Shopify tool definitions)
+-- RAG Service            (pgvector similarity search)
+-- Channel Adapters       (per-platform message formatting)
+-- Sales Engine           (BANT scoring logic)
+-- Escalation Service     (trigger detection + email alerts)
+-- Admin Dashboard        (WebSocket live updates)
```

## License

MIT � feel free to use, modify, and build on this.
