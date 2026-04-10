"""Email webhook route — SendGrid Inbound Parse."""

from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Form, Request

from app.channels.email_channel import EmailAdapter
from app.config import get_settings
from app.dependencies import get_db, get_redis
from app.services.orchestrator import Orchestrator

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/email")
async def email_inbound(
    request: Request,
    background_tasks: BackgroundTasks,
    db=Depends(get_db),
    redis=Depends(get_redis),
):
    """Receive emails via SendGrid Inbound Parse (multipart form POST)."""
    settings = get_settings()
    if not settings.email_enabled:
        return {"status": "disabled"}

    # SendGrid Inbound Parse sends as multipart form
    form_data = await request.form()
    payload = {k: v for k, v in form_data.items()}

    adapter = EmailAdapter()

    # Filter spam and OOO
    text = str(payload.get("text", ""))
    subject = str(payload.get("subject", ""))
    if adapter.is_out_of_office(text):
        logger.info("Skipping OOO reply from %s", payload.get("from"))
        return {"status": "skipped_ooo"}
    if adapter.is_spam(text, subject):
        logger.info("Skipping spam from %s", payload.get("from"))
        return {"status": "skipped_spam"}

    nlp_message = await adapter.parse_inbound(payload)

    if nlp_message:
        background_tasks.add_task(_process_email, nlp_message, adapter, db, redis)

    return {"status": "ok"}


async def _process_email(nlp_message, adapter, db, redis):
    """Background task: process email through orchestrator and send reply."""
    try:
        orchestrator = Orchestrator(db, redis)
        response = await orchestrator.process_message(nlp_message)
        # Add email metadata for threading
        response.metadata["subject"] = f"Re: {nlp_message.subject or 'Your inquiry'}"
        response.metadata["in_reply_to"] = nlp_message.email_thread_id
        await adapter.send_message(response)
    except Exception as e:
        logger.exception("Email processing error: %s", e)
