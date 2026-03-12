"""
Dashboard API Routes
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.database import get_stats
from app.services.reporting.metrics import get_user_engagement_stats

router = APIRouter()


@router.get("/overview")
async def get_dashboard_overview(db: Session = Depends(get_db)):
    """
    Get system-wide dashboard statistics.

    Returns total tweets, councilors, engagement metrics, etc.
    """
    try:
        stats = get_stats()
        return {
            "total_tweets": stats.get("total_tweets", 0),
            "total_original": stats.get("total_original", 0),
            "total_retweets": stats.get("total_retweets", 0),
            "total_councilors": stats.get("total_councilors", 0),
            "total_profiles": stats.get("total_profiles", 0),
            "active_users": stats.get("active_users", 0),
            "total_likes": stats.get("total_likes", 0),
            "total_views": stats.get("total_views", 0),
            "total_replies": stats.get("total_replies", 0),
        }
    except Exception as e:
        return {
            "total_tweets": 0,
            "total_original": 0,
            "total_retweets": 0,
            "total_councilors": 0,
            "total_profiles": 0,
            "active_users": 0,
            "total_likes": 0,
            "total_views": 0,
            "total_replies": 0,
        }


@router.get("/user/{username}")
async def get_user_dashboard(
    username: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get dashboard metrics for a specific user.

    Returns tweet count, engagement stats, top tweets, etc.
    """
    stats = get_user_engagement_stats(username, start_date, end_date)

    if not stats:
        raise HTTPException(status_code=404, detail=f"User {username} not found")

    return stats
