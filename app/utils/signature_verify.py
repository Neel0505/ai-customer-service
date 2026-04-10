"""HMAC signature verification for Meta (WhatsApp/Instagram) and Shopify webhooks."""

from __future__ import annotations

import hashlib
import hmac
import logging

logger = logging.getLogger(__name__)


def verify_meta_signature(payload: bytes, signature: str, app_secret: str) -> bool:
    """Verify X-Hub-Signature-256 from Meta (WhatsApp / Instagram) webhooks.

    The signature header looks like: sha256=<hex_digest>
    """
    if not signature or not app_secret:
        logger.warning("Missing signature or app_secret for Meta webhook verification")
        return False

    try:
        expected = "sha256=" + hmac.new(
            app_secret.encode("utf-8"),
            payload,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
    except Exception:
        logger.exception("Meta signature verification failed")
        return False


def verify_shopify_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify X-Shopify-Hmac-Sha256 from Shopify webhooks.

    Shopify sends the HMAC as a base64-encoded string.
    """
    import base64

    if not signature or not secret:
        logger.warning("Missing signature or secret for Shopify webhook verification")
        return False

    try:
        computed = base64.b64encode(
            hmac.new(
                secret.encode("utf-8"),
                payload,
                hashlib.sha256,
            ).digest()
        ).decode("utf-8")
        return hmac.compare_digest(computed, signature)
    except Exception:
        logger.exception("Shopify signature verification failed")
        return False
