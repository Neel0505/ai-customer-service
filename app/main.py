"""FastAPI application entrypoint — lifespan, middleware, and route registration."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import get_settings
from app.dependencies import close_redis, engine, init_redis
from app.models.base import Base

logger = logging.getLogger("omnichannel_agent")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle — init DB tables, Redis, etc."""
    settings = get_settings()
    logger.info("Starting Omnichannel Agent for %s...", settings.client_name)

    # Create tables if they don't exist (Alembic preferred for prod)
    async with engine.begin() as conn:
        # Import all models so they are registered with Base
        from app.models import contact, conversation, escalation, lead, message, product_embedding  # noqa: F401

        await conn.run_sync(Base.metadata.create_all)

    # Enable pgvector extension
    async with engine.begin() as conn:
        await conn.execute(
            __import__("sqlalchemy").text("CREATE EXTENSION IF NOT EXISTS vector")
        )

    # Init Redis
    await init_redis()
    logger.info("Database and Redis connected.")

    yield

    # Shutdown
    await close_redis()
    await engine.dispose()
    logger.info("Shutdown complete.")


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()

    app = FastAPI(
        title=f"{settings.client_name} — AI Omnichannel Agent",
        description="AI-powered customer service and sales agent",
        version="0.1.0",
        lifespan=lifespan,
    )

    # ── Middleware ──────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Global exception handler ───────────────────────────────
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled error: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    # ── Routes ─────────────────────────────────────────────────
    from app.routes.webhooks import twilio as twilio_routes
    from app.routes.webhooks import email as email_routes
    from app.routes.webhooks import instagram as ig_routes
    from app.routes.webhooks import shopify as shopify_routes
    from app.routes import admin as admin_routes
    from app.routes import simulator as sim_routes

    app.include_router(twilio_routes.router, prefix="/webhooks/twilio", tags=["Twilio WhatsApp"])
    app.include_router(email_routes.router, prefix="/webhooks", tags=["Email"])
    app.include_router(ig_routes.router, prefix="/webhooks", tags=["Instagram"])
    app.include_router(shopify_routes.router, prefix="/webhooks", tags=["Shopify"])
    app.include_router(admin_routes.router, prefix="/admin", tags=["Admin"])
    app.include_router(sim_routes.router, tags=["Simulator"])

    # ── Health check ───────────────────────────────────────────
    @app.get("/health", tags=["Health"])
    async def health_check():
        return {
            "status": "ok",
            "client": settings.client_name,
            "agent": settings.agent_name,
        }

    return app


# Create the app instance for uvicorn
app = create_app()
