"""
Tweets API Routes
"""
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.models import Tweet
from app.core.rate_limit import RateLimits, limiter

router = APIRouter()


@router.get("/{username}")
@limiter.limit(RateLimits.STANDARD)
async def get_user_tweets(
    request: Request,
    username: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    include_retweets: bool = False,
    start_date: str | None = None,
    end_date: str | None = None,
    db: Session = Depends(get_db)
):
    """
    Get paginated tweets for a user.
    """
    try:
        query = db.query(Tweet).filter(Tweet.username == username)

        if not include_retweets:
            query = query.filter(Tweet.is_retweet == False)

        if start_date:
            query = query.filter(Tweet.tweet_date >= start_date)
        if end_date:
            query = query.filter(Tweet.tweet_date <= end_date)

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        tweets = query.order_by(Tweet.tweet_date.desc()).offset(offset).limit(page_size).all()

        items = [
            {
                "id": t.id,
                "username": t.username,
                "tweet_text": t.tweet_text,
                "tweet_date": t.tweet_date,
                "likes": t.likes or 0,
                "replies": t.replies or 0,
                "retweets": t.retweets or 0,
                "views": t.views or 0,
                "is_retweet": t.is_retweet,
                "engagement": (t.likes or 0) + (t.retweets or 0) + (t.replies or 0),
            }
            for t in tweets
        ]

        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

        return {
            "username": username,
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        }
    except Exception:
        return {
            "username": username,
            "items": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0,
            "has_next": False,
            "has_prev": False,
        }


@router.get("/{username}/top")
@limiter.limit(RateLimits.STANDARD)
async def get_top_tweets(
    request: Request,
    username: str,
    limit: int = Query(10, ge=1, le=50, description="Number of tweets"),
    sort_by: Literal["engagement", "likes", "views", "retweets"] = "engagement",
    db: Session = Depends(get_db)
):
    """
    Get top performing tweets for a user.
    """
    try:
        query = db.query(Tweet).filter(
            Tweet.username == username,
            Tweet.is_retweet == False
        )

        if sort_by == "engagement":
            query = query.order_by(
                (func.coalesce(Tweet.likes, 0) + func.coalesce(Tweet.retweets, 0) + func.coalesce(Tweet.replies, 0)).desc()
            )
        elif sort_by == "likes":
            query = query.order_by(Tweet.likes.desc())
        elif sort_by == "views":
            query = query.order_by(Tweet.views.desc())
        elif sort_by == "retweets":
            query = query.order_by(Tweet.retweets.desc())

        tweets = query.limit(limit).all()

        return {
            "username": username,
            "sort_by": sort_by,
            "tweets": [
                {
                    "id": t.id,
                    "username": t.username,
                    "tweet_text": t.tweet_text,
                    "tweet_date": t.tweet_date,
                    "likes": t.likes or 0,
                    "replies": t.replies or 0,
                    "retweets": t.retweets or 0,
                    "views": t.views or 0,
                    "engagement": (t.likes or 0) + (t.retweets or 0) + (t.replies or 0),
                }
                for t in tweets
            ]
        }
    except Exception:
        return {"username": username, "sort_by": sort_by, "tweets": []}


@router.get("/{username}/stats")
@limiter.limit(RateLimits.STANDARD)
async def get_tweet_stats(
    request: Request,
    username: str,
    start_date: str | None = None,
    end_date: str | None = None,
    db: Session = Depends(get_db)
):
    """
    Get tweet statistics for a user.
    """
    query = db.query(
        func.count(Tweet.id).label("tweet_count"),
        func.coalesce(func.sum(Tweet.likes), 0).label("total_likes"),
        func.coalesce(func.sum(Tweet.retweets), 0).label("total_retweets"),
        func.coalesce(func.sum(Tweet.replies), 0).label("total_replies"),
        func.coalesce(func.sum(Tweet.views), 0).label("total_views"),
    ).filter(
        Tweet.username == username,
        Tweet.is_retweet == False
    )

    if start_date:
        query = query.filter(Tweet.tweet_date >= start_date)
    if end_date:
        query = query.filter(Tweet.tweet_date <= end_date)

    result = query.first()

    if not result or result.tweet_count == 0:
        raise HTTPException(status_code=404, detail=f"No tweets found for {username}")

    tweet_count = result.tweet_count or 0
    total_likes = result.total_likes or 0
    total_retweets = result.total_retweets or 0
    total_replies = result.total_replies or 0
    total_views = result.total_views or 0
    total_engagement = total_likes + total_retweets + total_replies

    return {
        "username": username,
        "tweet_count": tweet_count,
        "total_likes": total_likes,
        "total_retweets": total_retweets,
        "total_replies": total_replies,
        "total_views": total_views,
        "total_engagement": total_engagement,
        "avg_likes_per_tweet": round(total_likes / tweet_count, 2) if tweet_count > 0 else 0,
        "avg_engagement_per_tweet": round(total_engagement / tweet_count, 2) if tweet_count > 0 else 0,
    }


@router.get("/{username}/daily")
@limiter.limit(RateLimits.STANDARD)
async def get_daily_tweet_stats(
    request: Request,
    username: str,
    days: int = Query(30, ge=7, le=90, description="Number of days"),
    db: Session = Depends(get_db)
):
    """
    Get daily tweet activity for charts.
    """
    try:
        # This query gets daily aggregates
        daily_stats = db.query(
            func.date(Tweet.tweet_date).label("date"),
            func.count(Tweet.id).label("tweet_count"),
            func.coalesce(func.sum(Tweet.likes), 0).label("likes"),
            func.coalesce(func.sum(Tweet.retweets), 0).label("retweets"),
        ).filter(
            Tweet.username == username,
            Tweet.is_retweet == False
        ).group_by(
            func.date(Tweet.tweet_date)
        ).order_by(
            func.date(Tweet.tweet_date).desc()
        ).limit(days).all()

        return {
            "username": username,
            "days": days,
            "data": [
                {
                    "date": str(s.date) if s.date else None,
                    "tweet_count": s.tweet_count,
                    "likes": s.likes,
                    "retweets": s.retweets,
                }
                for s in reversed(daily_stats)
            ]
        }
    except Exception:
        return {"username": username, "days": days, "data": []}
