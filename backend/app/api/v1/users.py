"""
Users API Routes
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.deps import get_db
from app.core.models import Councilor, Tweet, ProfileHistory
from app.core.database import get_latest_profile, get_all_profile_history

router = APIRouter()


@router.get("/")
async def get_all_users(
    party: Optional[str] = None,
    district: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all council members.

    Optional filters:
    - party: Filter by party name
    - district: Filter by district
    """
    try:
        query = db.query(Councilor)

        if party:
            query = query.filter(Councilor.party.ilike(f"%{party}%"))
        if district:
            query = query.filter(Councilor.district.ilike(f"%{district}%"))

        councilors = query.order_by(Councilor.name).all()

        return [
            {
                "id": c.id,
                "username": c.username,
                "name": c.name,
                "party": c.party,
                "district": c.district,
            }
            for c in councilors
        ]
    except Exception as e:
        return []


@router.get("/{username}")
async def get_user(username: str, db: Session = Depends(get_db)):
    """
    Get detailed information for a specific user.
    """
    councilor = db.query(Councilor).filter(Councilor.username == username).first()

    if not councilor:
        raise HTTPException(status_code=404, detail=f"User {username} not found")

    # Get tweet count
    tweet_count = db.query(func.count(Tweet.id)).filter(Tweet.username == username).scalar()

    # Get latest profile
    profile = get_latest_profile(username)

    return {
        "id": councilor.id,
        "username": councilor.username,
        "name": councilor.name,
        "party": councilor.party,
        "district": councilor.district,
        "tweet_count": tweet_count,
        "profile": profile,
    }


@router.get("/{username}/profile")
async def get_user_profile(username: str, db: Session = Depends(get_db)):
    """
    Get latest profile information for a user.
    """
    profile = get_latest_profile(username)

    if not profile:
        raise HTTPException(status_code=404, detail=f"Profile for {username} not found")

    return profile


@router.get("/{username}/history")
async def get_user_profile_history(username: str, db: Session = Depends(get_db)):
    """
    Get profile history for a user (time series data).
    """
    history = get_all_profile_history(username)

    if not history:
        raise HTTPException(status_code=404, detail=f"No history for {username}")

    return history
