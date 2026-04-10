"""Shopify webhook routes — product sync (create/update/delete)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Request, Response

from app.config import get_settings
from app.dependencies import get_db
from app.services.shopify_ingestion import ShopifyIngestionService
from app.utils.signature_verify import verify_shopify_signature

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/shopify")
async def shopify_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db=Depends(get_db),
):
    """Receive Shopify product webhooks (product/create, product/update, product/delete)."""
    settings = get_settings()

    body = await request.body()
    signature = request.headers.get("X-Shopify-Hmac-Sha256", "")

    if not verify_shopify_signature(body, signature, settings.shopify_webhook_secret):
        logger.warning("Invalid Shopify webhook signature")
        return Response(status_code=401)

    topic = request.headers.get("X-Shopify-Topic", "")
    payload = await request.json()

    if topic in ("products/create", "products/update"):
        background_tasks.add_task(_upsert_product, payload, db)
    elif topic == "products/delete":
        background_tasks.add_task(_delete_product, payload, db)
    else:
        logger.info("Ignoring Shopify topic: %s", topic)

    return {"status": "ok"}


async def _upsert_product(payload, db):
    try:
        ingestion = ShopifyIngestionService(db)
        await ingestion.upsert_product(payload)
        logger.info("Upserted Shopify product %s", payload.get("id"))
    except Exception as e:
        logger.exception("Shopify product upsert failed: %s", e)


async def _delete_product(payload, db):
    try:
        ingestion = ShopifyIngestionService(db)
        await ingestion.delete_product(str(payload.get("id", "")))
        logger.info("Deleted Shopify product %s", payload.get("id"))
    except Exception as e:
        logger.exception("Shopify product delete failed: %s", e)
