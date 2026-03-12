"""
Rate Limiting Module - API Request Throttling
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from fastapi import Request
from fastapi.responses import JSONResponse


def get_client_ip(request: Request) -> str:
    """
    Get client IP address from request.

    Handles X-Forwarded-For header for proxy setups.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


# Create limiter instance
limiter = Limiter(key_func=get_client_ip)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """
    Custom handler for rate limit exceeded errors.

    Returns a JSON response with rate limit details.
    """
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "message": "Too many requests. Please try again later.",
            "detail": str(exc.detail),
            "retry_after": exc.detail.split("per")[0].strip() if exc.detail else "60 seconds"
        }
    )


# Rate limit constants for different endpoints
class RateLimits:
    """Rate limit configurations for different endpoint types"""

    # Heavy operations (LLM, scraping)
    HEAVY = "5/minute"

    # Standard read operations
    STANDARD = "30/minute"

    # Light operations (health checks, etc.)
    LIGHT = "60/minute"

    # Auth operations (login attempts)
    AUTH = "10/minute"

    # Write operations
    WRITE = "20/minute"

    # Batch operations
    BATCH = "3/minute"
