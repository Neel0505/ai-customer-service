"""Twilio WhatsApp webhook routes."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Request, Response
from fastapi.params import Form

from app.channels.twilio_whatsapp import TwilioWhatsAppAdapter
from app.config import get_settings
from app.dependencies import get_db, get_redis
from app.services.orchestrator import Orchestrator

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/whatsapp")
async def twilio_whatsapp_inbound(
    request: Request,
    background_tasks: BackgroundTasks,
    db=Depends(get_db),
    redis=Depends(get_redis),
):
    """Receive Twilio WhatsApp messages."""
    settings = get_settings()
    if not settings.whatsapp_enabled:
        return Response(content="WhatsApp disabled", status_code=200)

    # Twilio sends data as form URL-encoded
    form_data = await request.form()
    signature = request.headers.get("X-Twilio-Signature", "")
    
    # We must use the original URL exactly as Twilio requested it, which may be behind a reverse proxy (like ngrok)
    # Using request.url string representation is usually sufficient, but headers like X-Forwarded-Proto might be needed in production.
    url = str(request.url)
    
    # Check if we are running behind a proxy that changes https to http
    if "x-forwarded-proto" in request.headers:
        url = url.replace("http://", f"{request.headers['x-forwarded-proto']}://")

    # FastAPI Form returns a MultiDict, we convert to a plain dict for verification
    params = {}
    for key, value in form_data.multi_items():
        params[key] = value

    adapter = TwilioWhatsAppAdapter()
    if settings.twilio_auth_token and not adapter.verify_signature(url, params, signature):
        logger.warning(f"Invalid Twilio webhook signature on url: {url}")
        return Response(status_code=403, content="Invalid signature")

    nlp_message = await adapter.parse_inbound(params)

    if nlp_message:
        background_tasks.add_task(_process_twilio_whatsapp, nlp_message, adapter, db, redis)

    # Twilio expects empty TwiML or 200 OK. 200 plain text is generally acceptable.
    return Response(content="", media_type="text/xml")


async def _process_twilio_whatsapp(nlp_message, adapter, db, redis):
    """Background task: process message through orchestrator and send response."""
    try:
        orchestrator = Orchestrator(db, redis)
        response = await orchestrator.process_message(nlp_message)
        await adapter.send_message(response)
    except Exception as e:
        logger.exception("Twilio WhatsApp processing error: %s", e)
