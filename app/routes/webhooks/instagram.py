"""Instagram webhook routes — verification challenge + inbound DMs."""

from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request, Response

from app.channels.instagram import InstagramAdapter
from app.config import get_settings
from app.dependencies import get_db, get_redis
from app.services.orchestrator import Orchestrator

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/instagram")
async def instagram_verify(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """Meta webhook verification challenge for Instagram."""
    settings = get_settings()
    if hub_mode == "subscribe" and hub_token == settings.instagram_webhook_verify_token:
        logger.info("Instagram webhook verified")
        return Response(content=hub_challenge, media_type="text/plain")
    return Response(status_code=403)


@router.post("/instagram")
async def instagram_inbound(
    request: Request,
    background_tasks: BackgroundTasks,
    db=Depends(get_db),
    redis=Depends(get_redis),
):
    """Receive Instagram DMs. Returns 200 immediately, processes async."""
    settings = get_settings()
    if not settings.instagram_enabled:
        return {"status": "disabled"}

    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")

    adapter = InstagramAdapter()
    if not adapter.verify_signature(body, signature):
        logger.warning("Invalid Instagram webhook signature")
        return Response(status_code=401)

    payload = await request.json()
    nlp_message = await adapter.parse_inbound(payload)

    if nlp_message:
        # Ignore echo messages (our own replies)
        if nlp_message.user_id != settings.instagram_page_id:
            background_tasks.add_task(_process_instagram, nlp_message, adapter, db, redis)

    return {"status": "ok"}


async def _process_instagram(nlp_message, adapter, db, redis):
    """Background task: process message through orchestrator and send response."""
    try:
        orchestrator = Orchestrator(db, redis)
        response = await orchestrator.process_message(nlp_message)
        await adapter.send_message(response)
    except Exception as e:
        logger.exception("Instagram processing error: %s", e)
