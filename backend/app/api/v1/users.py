"""
Users API Routes
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.deps import get_db
from app.api.schemas import PaginatedResponse, UserListItem, UserDetail
from app.core.models import Councilor, Tweet, ProfileHistory
from app.core.database import get_latest_profile, get_all_profile_history
from app.core.rate_limit import limiter, RateLimits

router = APIRouter()


@router.get("/")
@limiter.limit(RateLimits.STANDARD)
async def get_all_users(
    request: Request,
    party: Optional[str] = None,
    district: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Get all council members with pagination.

    Optional filters:
    - party: Filter by party name
    - district: Filter by district
    - search: Search by name or username
    """
    try:
        query = db.query(Councilor)

        # Apply filters
        if party:
            query = query.filter(Councilor.party.ilike(f"%{party}%"))
        if district:
            query = query.filter(Councilor.district.ilike(f"%{district}%"))
        if search:
            query = query.filter(
                (Councilor.name.ilike(f"%{search}%")) |
                (Councilor.username.ilike(f"%{search}%"))
            )

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        councilors = query.order_by(Councilor.name).offset(offset).limit(page_size).all()

        # Get tweet counts for each user
        usernames = [c.username for c in councilors]
        tweet_counts = {}
        if usernames:
            counts = db.query(
                Tweet.username,
                func.count(Tweet.id).label("count")
            ).filter(
                Tweet.username.in_(usernames)
            ).group_by(Tweet.username).all()
            tweet_counts = {c.username: c.count for c in counts}

        items = [
            {
                "id": c.id,
                "username": c.username,
                "name": c.name,
                "party": c.party,
                "district": c.district,
                "tweet_count": tweet_counts.get(c.username, 0),
            }
            for c in councilors
        ]

        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        }
    except Exception as e:
        return {
            "items": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0,
            "has_next": False,
            "has_prev": False,
        }


@router.get("/list")
@limiter.limit(RateLimits.STANDARD)
async def get_users_simple_list(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Get simple list of all users (for dropdowns, etc.)
    No pagination - returns all users.
    """
    try:
        councilors = db.query(
            Councilor.username,
            Councilor.name,
            Councilor.party
        ).order_by(Councilor.name).all()

        return [
            {
                "username": c.username,
                "name": c.name,
                "party": c.party,
            }
            for c in councilors
        ]
    except Exception:
        return []


@router.get("/{username}")
@limiter.limit(RateLimits.STANDARD)
async def get_user(
    request: Request,
    username: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed information for a specific user.
    """
    councilor = db.query(Councilor).filter(Councilor.username == username).first()

    if not councilor:
        raise HTTPException(status_code=404, detail=f"User {username} not found")

    # Get tweet count
    tweet_count = db.query(func.count(Tweet.id)).filter(Tweet.username == username).scalar()

    # Get tweet stats
    stats = db.query(
        func.coalesce(func.sum(Tweet.likes), 0).label("total_likes"),
        func.coalesce(func.sum(Tweet.retweets), 0).label("total_retweets"),
        func.coalesce(func.sum(Tweet.replies), 0).label("total_replies"),
        func.coalesce(func.sum(Tweet.views), 0).label("total_views"),
    ).filter(
        Tweet.username == username,
        Tweet.is_retweet == False
    ).first()

    # Get latest profile
    profile = get_latest_profile(username)

    return {
        "id": councilor.id,
        "username": councilor.username,
        "name": councilor.name,
        "party": councilor.party,
        "district": councilor.district,
        "tweet_count": tweet_count,
        "total_likes": stats.total_likes if stats else 0,
        "total_retweets": stats.total_retweets if stats else 0,
        "total_replies": stats.total_replies if stats else 0,
        "total_views": stats.total_views if stats else 0,
        "profile": profile,
    }


@router.get("/{username}/profile")
@limiter.limit(RateLimits.STANDARD)
async def get_user_profile(
    request: Request,
    username: str,
    db: Session = Depends(get_db)
):
    """
    Get latest profile information for a user.
    """
    profile = get_latest_profile(username)

    if not profile:
        raise HTTPException(status_code=404, detail=f"Profile for {username} not found")

    return profile


@router.get("/{username}/history")
@limiter.limit(RateLimits.STANDARD)
async def get_user_profile_history(
    request: Request,
    username: str,
    db: Session = Depends(get_db)
):
    """
    Get profile history for a user (time series data for charts).
    """
    history = get_all_profile_history(username)

    if not history:
        raise HTTPException(status_code=404, detail=f"No history for {username}")

    return {
        "username": username,
        "history": history,
        "count": len(history),
    }
