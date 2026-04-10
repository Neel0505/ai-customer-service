"""Global error handling — retry logic, fallback messages, and error classification."""

from __future__ import annotations

import asyncio
import logging
from functools import wraps
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

# Configurable fallback message
FALLBACK_MESSAGE = (
    "I'm sorry, I'm having a brief technical issue. "
    "A team member will follow up with you shortly. "
    "Thank you for your patience!"
)

T = TypeVar("T")


class AgentError(Exception):
    """Base exception for agent errors."""

    def __init__(self, message: str, should_escalate: bool = False):
        super().__init__(message)
        self.should_escalate = should_escalate


class LLMError(AgentError):
    """Error from LLM API call (OpenAI)."""
    pass


class ShopifyError(AgentError):
    """Error from Shopify API call."""
    pass


class ChannelSendError(AgentError):
    """Error sending message via channel adapter."""
    pass


async def retry_async(
    func: Callable,
    *args: Any,
    max_retries: int = 3,
    backoff_base: float = 1.0,
    **kwargs: Any,
) -> Any:
    """Retry an async function with exponential backoff.

    On failure after all retries, raises the last exception.
    """
    last_exception: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                wait_time = backoff_base * (2 ** attempt)
                logger.warning(
                    "Retry %d/%d for %s after %.1fs: %s",
                    attempt + 1,
                    max_retries,
                    func.__name__,
                    wait_time,
                    str(e),
                )
                await asyncio.sleep(wait_time)
            else:
                logger.error(
                    "All %d retries exhausted for %s: %s",
                    max_retries,
                    func.__name__,
                    str(e),
                )

    raise last_exception  # type: ignore


def with_retry(max_retries: int = 3, backoff_base: float = 1.0):
    """Decorator version of retry_async."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry_async(
                func, *args, max_retries=max_retries, backoff_base=backoff_base, **kwargs
            )
        return wrapper

    return decorator
