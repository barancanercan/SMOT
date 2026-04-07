"""
LLM Metrics API Routes
Exposes observability data for monitoring
"""
from fastapi import APIRouter, Request

from app.core.rate_limit import RateLimits, limiter
from app.services.analysis.metrics import metrics_collector

router = APIRouter()


@router.get("/")
@limiter.limit(RateLimits.STANDARD)
async def get_llm_metrics_summary(request: Request):
    """
    Get aggregated LLM metrics summary.
    Useful for dashboards and monitoring.
    """
    stats = metrics_collector.get_aggregate_stats()
    return {
        "status": "ok",
        "metrics": stats
    }


@router.get("/recent")
@limiter.limit(RateLimits.STANDARD)
async def get_recent_llm_calls(request: Request, limit: int = 50):
    """
    Get recent LLM call metrics.
    Useful for debugging and detailed analysis.

    Args:
        limit: Number of recent calls to return (max 100)
    """
    if limit > 100:
        limit = 100

    recent = metrics_collector.get_recent_metrics(limit)
    return {
        "status": "ok",
        "count": len(recent),
        "calls": recent
    }


@router.get("/health")
async def get_llm_health(request: Request):
    """
    Quick health check for LLM system.
    Returns current success rate and latency.
    """
    stats = metrics_collector.get_aggregate_stats()

    # Determine health status
    if stats["total_calls"] == 0:
        health = "unknown"
        message = "No LLM calls recorded yet"
    elif stats["success_rate"] >= 0.95:
        health = "healthy"
        message = "LLM system operating normally"
    elif stats["success_rate"] >= 0.8:
        health = "degraded"
        message = "LLM system experiencing some failures"
    else:
        health = "unhealthy"
        message = "LLM system has high failure rate"

    return {
        "health": health,
        "message": message,
        "success_rate": round(stats["success_rate"] * 100, 1),
        "validation_rate": round(stats["validation_rate"] * 100, 1),
        "avg_latency_ms": round(stats["avg_latency_ms"], 0),
        "avg_confidence": round(stats["avg_confidence"], 2),
        "total_calls": stats["total_calls"]
    }
