"""
Tweets API Routes
"""
from typing import Optional, Literal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.deps import get_db
from app.core.models import Tweet

router = APIRouter()


@router.get("/{username}/top")
async def get_top_tweets(
    username: str,
    limit: int = 10,
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
            query = query.order_by((func.coalesce(Tweet.likes, 0) + func.coalesce(Tweet.retweets, 0)).desc())
        elif sort_by == "likes":
            query = query.order_by(Tweet.likes.desc())
        elif sort_by == "views":
            query = query.order_by(Tweet.views.desc())
        elif sort_by == "retweets":
            query = query.order_by(Tweet.retweets.desc())

        tweets = query.limit(limit).all()

        return {
            "username": username,
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
    except Exception as e:
        return {"username": username, "tweets": []}


@router.get("/{username}/stats")
async def get_tweet_stats(
    username: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get tweet statistics for a user.
    """
    query = db.query(
        func.count(Tweet.id).label("tweet_count"),
        func.sum(Tweet.likes).label("total_likes"),
        func.sum(Tweet.retweets).label("total_retweets"),
        func.sum(Tweet.replies).label("total_replies"),
        func.sum(Tweet.views).label("total_views"),
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
