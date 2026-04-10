#!/usr/bin/env python3
"""Standalone Shopify product ingestion script."""

from __future__ import annotations

import asyncio
import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


async def main():
    from app.dependencies import async_session_factory, init_redis, close_redis, engine
    from app.models.base import Base

    # Import all models
    from app.models import contact, conversation, escalation, lead, message, product_embedding  # noqa: F401

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await init_redis()

    async with async_session_factory() as db:
        from app.services.shopify_ingestion import ShopifyIngestionService
        ingestion = ShopifyIngestionService(db)
        count = await ingestion.ingest_all_products()
        print(f"\n✅ Successfully ingested {count} products into pgvector.\n")

    await close_redis()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
