import asyncio
import logging
import os
import time
from typing import Optional

import httpx
from pydantic import BaseModel, ValidationError

from datadog_logger import log_datadog_event

logger = logging.getLogger(__name__)


DEFAULT_MANUAL_FINISH_URL = (
    "https://pick-binding-dashboard-api-208732756826.europe-west4.run.app/manual-finish"
)
CACHE_TTL_SECONDS = 5


class ManualFinishMetrics(BaseModel):
    geek: int
    fma: int
    total: int
    updated_at: Optional[str] = None


_cache: Optional[ManualFinishMetrics] = None
_cache_expiration: float = 0.0
_lock = asyncio.Lock()


async def get_manual_finish_metrics(force_refresh: bool = False) -> ManualFinishMetrics:
    """
    Fetch metrics from the manual-finish service with a lightweight TTL cache.
    Returns cached data when possible to keep the upstream endpoint healthy.
    """
    global _cache, _cache_expiration

    now = time.monotonic()
    if not force_refresh and _cache and _cache_expiration > now:
        return _cache

    async with _lock:
        if not force_refresh and _cache and _cache_expiration > time.monotonic():
            return _cache

        url = os.getenv("MANUAL_FINISH_URL", DEFAULT_MANUAL_FINISH_URL)
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            if _cache:
                logger.warning("manual-finish fetch failed (%s); serving cached data", exc)
                log_datadog_event(
                    status="warning",
                    message=f"manual-finish fetch failed; served cached data: {exc}",
                    event_type="manual_finish.fetch",
                    function_name="get_manual_finish_metrics",
                    extra={"url": url, "cache_age": CACHE_TTL_SECONDS},
                )
                return _cache
            log_datadog_event(
                status="error",
                message=f"manual-finish request failed: {exc}",
                event_type="manual_finish.fetch",
                function_name="get_manual_finish_metrics",
                extra={"url": url},
            )
            raise RuntimeError(f"manual-finish request failed: {exc}") from exc

        try:
            metrics = ManualFinishMetrics.model_validate(response.json())
        except (ValueError, ValidationError) as exc:
            log_datadog_event(
                status="error",
                message=f"manual-finish invalid payload: {exc}",
                event_type="manual_finish.fetch",
                function_name="get_manual_finish_metrics",
                extra={"url": url},
            )
            raise RuntimeError(f"manual-finish returned invalid payload: {exc}") from exc

        _cache = metrics
        _cache_expiration = time.monotonic() + CACHE_TTL_SECONDS
        log_datadog_event(
            status="ok",
            message="manual-finish metrics refreshed",
            event_type="manual_finish.fetch",
            function_name="get_manual_finish_metrics",
            extra={
                "url": url,
                "cache_ttl_seconds": CACHE_TTL_SECONDS,
                "geek": metrics.geek,
                "fma": metrics.fma,
                "total": metrics.total,
            },
        )
        return metrics
