"""
Users API Routes
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.deps import get_db
from app.api.schemas import PaginatedResponse, UserListItem, UserDetail
from app.core.models import Councilor, Tweet, ProfileHistory, ReportCache
from app.core.database import get_latest_profile, get_all_profile_history
from app.core.rate_limit import limiter, RateLimits
from app.core.constants import normalize_party_name

router = APIRouter()


# Request models
class CreateUserRequest(BaseModel):
    username: str
    name: str
    party: str
    district: Optional[str] = None


class BulkCreateRequest(BaseModel):
    users: List[CreateUserRequest]


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
                "party": normalize_party_name(c.party),
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
        import logging
        logging.getLogger("Users").error(f"Error listing users: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


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
                "party": normalize_party_name(c.party),
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
        "party": normalize_party_name(councilor.party),
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


@router.post("/")
@limiter.limit(RateLimits.WRITE)
async def create_user(
    request: Request,
    body: CreateUserRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new council member.

    Rate limit: 20 requests per minute
    """
    # Check if username already exists
    existing = db.query(Councilor).filter(Councilor.username == body.username).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Kullanici zaten mevcut: @{body.username}")

    # Normalize party name
    normalized_party = normalize_party_name(body.party)

    # Create new councilor
    councilor = Councilor(
        username=body.username,
        name=body.name,
        party=normalized_party,
        district=body.district
    )

    try:
        db.add(councilor)
        db.commit()
        db.refresh(councilor)

        return {
            "success": True,
            "user": {
                "id": councilor.id,
                "username": councilor.username,
                "name": councilor.name,
                "party": councilor.party,
                "district": councilor.district,
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Kullanici olusturulamadi: {str(e)}")


@router.post("/bulk")
@limiter.limit(RateLimits.BATCH)
async def create_users_bulk(
    request: Request,
    body: BulkCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Create multiple council members at once.

    Skips duplicates and returns summary.

    Rate limit: 3 requests per minute
    """
    if not body.users:
        raise HTTPException(status_code=400, detail="Kullanici listesi bos")

    if len(body.users) > 100:
        raise HTTPException(status_code=400, detail="Maksimum 100 kullanici eklenebilir")

    created = 0
    skipped = 0
    errors = []

    for user_data in body.users:
        try:
            # Check if exists
            existing = db.query(Councilor).filter(Councilor.username == user_data.username).first()
            if existing:
                skipped += 1
                continue

            # Normalize party
            normalized_party = normalize_party_name(user_data.party)

            # Create councilor
            councilor = Councilor(
                username=user_data.username,
                name=user_data.name,
                party=normalized_party,
                district=user_data.district
            )
            db.add(councilor)
            created += 1

        except Exception as e:
            errors.append(f"@{user_data.username}: {str(e)}")

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Toplu ekleme basarisiz: {str(e)}")

    return {
        "created": created,
        "skipped": skipped,
        "errors": errors,
        "total": len(body.users),
    }


@router.delete("/{username}")
@limiter.limit(RateLimits.WRITE)
async def delete_user(
    request: Request,
    username: str,
    db: Session = Depends(get_db)
):
    """
    Delete a council member and all related data (cascade delete).

    Deletes:
    - Councilor record
    - All tweets
    - Profile history
    - Cached reports

    Rate limit: 20 requests per minute
    """
    # Find user
    councilor = db.query(Councilor).filter(Councilor.username == username).first()
    if not councilor:
        raise HTTPException(status_code=404, detail=f"Kullanici bulunamadi: @{username}")

    try:
        # Delete related data (cascade)
        tweets_deleted = db.query(Tweet).filter(Tweet.username == username).delete()
        profiles_deleted = db.query(ProfileHistory).filter(ProfileHistory.username == username).delete()
        cache_deleted = db.query(ReportCache).filter(ReportCache.username == username).delete()

        # Delete councilor
        db.delete(councilor)
        db.commit()

        return {
            "success": True,
            "deleted": username,
            "details": {
                "tweets_deleted": tweets_deleted,
                "profiles_deleted": profiles_deleted,
                "cache_deleted": cache_deleted,
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Silme islemi basarisiz: {str(e)}")
