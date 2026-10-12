import logging
import os
from typing import Optional
from fastapi import Header, HTTPException, Request

logger = logging.getLogger(__name__)


async def verify_api_key(
    request: Request,
    x_api_key: Optional[str] = Header(None, alias="x-api-key"),
) -> Optional[str]:
    """
    Validates the 'x-api-key' header.
    Maintains 100% backwards compatibility when REQUIRE_AUTH is false.
    """
    # Always allow CORS preflight requests
    if request.method == "OPTIONS":
        return None

    expected_key = os.getenv("DASHBOARD_API_KEY")
    require_auth = os.getenv("REQUIRE_AUTH", "false").lower() in ("true", "1", "yes")

    # If an API key is provided, validate it
    if x_api_key:
        if expected_key and x_api_key != expected_key:
            logger.warning("Invalid x-api-key received for %s", request.url.path)
            raise HTTPException(status_code=401, detail="Invalid x-api-key header")
        return x_api_key

    # If no key is provided, check if auth is strictly enforced
    if require_auth:
        logger.warning("Missing x-api-key header for %s (REQUIRE_AUTH=true)", request.url.path)
        raise HTTPException(status_code=401, detail="Missing required x-api-key header")

    # Backwards-compatibility mode: permit request without header
    return None
