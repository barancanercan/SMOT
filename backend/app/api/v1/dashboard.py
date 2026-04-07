"""
Dashboard API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.v1.schemas import Platform
from app.core.database import get_instagram_stats, get_stats
from app.services.reporting.metrics import get_user_engagement_stats

router = APIRouter()


@router.get("/overview")
async def get_dashboard_overview(
    platform: Platform = Query(Platform.TWITTER, description="Platform to get stats for"),
    db: Session = Depends(get_db)
):
    """
    Get system-wide dashboard statistics.

    Args:
        platform: 'twitter', 'instagram', or 'both'

    Returns total tweets/posts, councilors, engagement metrics, etc.
    """
    try:
        if platform == Platform.TWITTER:
            # Twitter-only stats
            stats = get_stats()
            return {
                "total_tweets": stats.get("total_tweets", 0),
                "total_original": stats.get("total_original", 0),
                "total_retweets": stats.get("total_retweets", 0),
                "total_retweets_count": stats.get("total_retweets_count", 0),
                "total_councilors": stats.get("total_councilors", 0),
                "total_profiles": stats.get("total_profiles", 0),
                "active_users": stats.get("active_users", 0),
                "total_likes": stats.get("total_likes", 0),
                "total_views": stats.get("total_views", 0),
                "total_replies": stats.get("total_replies", 0),
                "platform": "twitter"
            }

        elif platform == Platform.INSTAGRAM:
            # Instagram-only stats
            twitter_stats = get_stats()  # For councilor count
            ig_stats = get_instagram_stats()
            return {
                "total_posts": ig_stats.get("total_posts", 0),
                "total_photos": ig_stats.get("total_photos", 0),
                "total_videos": ig_stats.get("total_videos", 0),
                "total_councilors": twitter_stats.get("total_councilors", 0),
                "total_instagram_profiles": ig_stats.get("total_instagram_profiles", 0),
                "instagram_active_users": ig_stats.get("instagram_active_users", 0),
                "total_likes": ig_stats.get("total_instagram_likes", 0),
                "total_comments": ig_stats.get("total_comments", 0),
                "platform": "instagram"
            }

        else:  # BOTH
            # Combined stats
            twitter_stats = get_stats()
            ig_stats = get_instagram_stats()

            return {
                # Twitter stats
                "total_tweets": twitter_stats.get("total_tweets", 0),
                "total_original": twitter_stats.get("total_original", 0),
                "total_retweets": twitter_stats.get("total_retweets", 0),
                "total_retweets_count": twitter_stats.get("total_retweets_count", 0),
                "twitter_likes": twitter_stats.get("total_likes", 0),
                "twitter_views": twitter_stats.get("total_views", 0),
                "twitter_replies": twitter_stats.get("total_replies", 0),
                "twitter_active_users": twitter_stats.get("active_users", 0),
                # Instagram stats
                "total_posts": ig_stats.get("total_posts", 0),
                "total_photos": ig_stats.get("total_photos", 0),
                "total_videos": ig_stats.get("total_videos", 0),
                "instagram_likes": ig_stats.get("total_instagram_likes", 0),
                "total_comments": ig_stats.get("total_comments", 0),
                "instagram_active_users": ig_stats.get("instagram_active_users", 0),
                # Combined stats
                "total_councilors": twitter_stats.get("total_councilors", 0),
                "total_profiles": twitter_stats.get("total_profiles", 0) + ig_stats.get("total_instagram_profiles", 0),
                "total_content": twitter_stats.get("total_tweets", 0) + ig_stats.get("total_posts", 0),
                "total_likes": twitter_stats.get("total_likes", 0) + ig_stats.get("total_instagram_likes", 0),
                "total_engagement": (
                    twitter_stats.get("total_likes", 0) +
                    twitter_stats.get("total_replies", 0) +
                    twitter_stats.get("total_retweets_count", 0) +
                    ig_stats.get("total_instagram_likes", 0) +
                    ig_stats.get("total_comments", 0)
                ),
                "platform": "both"
            }

    except Exception as e:
        return {
            "total_tweets": 0,
            "total_original": 0,
            "total_retweets": 0,
            "total_retweets_count": 0,
            "total_councilors": 0,
            "total_profiles": 0,
            "active_users": 0,
            "total_likes": 0,
            "total_views": 0,
            "total_replies": 0,
            "platform": platform.value,
            "error": str(e)
        }


@router.get("/user/{username}")
async def get_user_dashboard(
    username: str,
    start_date: str | None = None,
    end_date: str | None = None,
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
