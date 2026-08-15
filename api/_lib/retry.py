from __future__ import annotations
import asyncio
import logging
from typing import Callable, TypeVar

import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from api._lib.errors import ProviderRateLimitError

T = TypeVar("T")
log = logging.getLogger(__name__)


async def with_retry(
    fn: Callable,
    *args,
    max_attempts: int = 2,
    min_wait: float = 0.5,
    max_wait: float = 4.0,
    **kwargs,
):
    """Run *fn* with exponential backoff on transient / rate-limit failures."""
    async for attempt in AsyncRetrying(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=min_wait, max=max_wait),
        retry=retry_if_exception_type((httpx.TransportError, ProviderRateLimitError)),
        reraise=True,
    ):
        with attempt:
            return await fn(*args, **kwargs)


async def run_with_timeout(coro, timeout_ms: float):
    """Raise asyncio.TimeoutError if *coro* exceeds *timeout_ms*."""
    return await asyncio.wait_for(coro, timeout=timeout_ms / 1000)
