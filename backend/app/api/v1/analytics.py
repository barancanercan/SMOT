"""
Analytics API Routes
"""
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.deps import get_db
from app.core.models import Councilor, Tweet, ProfileHistory
from app.core.constants import normalize_party_name

router = APIRouter()


@router.get("/followers")
async def get_followers_ranking(
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Get followers ranking for all council members.
    """
    try:
        # Get all councilors
        councilors = db.query(Councilor).all()
        councilor_map = {c.username: c for c in councilors}

        # Get latest profile for each user
        subquery = db.query(
            ProfileHistory.username,
            func.max(ProfileHistory.scrape_date).label("max_date")
        ).group_by(ProfileHistory.username).subquery()

        profiles = db.query(ProfileHistory).join(
            subquery,
            (ProfileHistory.username == subquery.c.username) &
            (ProfileHistory.scrape_date == subquery.c.max_date)
        ).order_by(ProfileHistory.followers_count.desc()).limit(limit).all()

        result = []
        for p in profiles:
            c = councilor_map.get(p.username)
            result.append({
                "username": p.username,
                "name": c.name if c else p.username,
                "party": normalize_party_name(c.party) if c else "",
                "district": c.district if c else "",
                "followers_count": p.followers_count or 0,
                "following_count": p.following_count or 0,
            })
        return result
    except Exception as e:
        return []


@router.get("/parties")
async def get_party_statistics(db: Session = Depends(get_db)):
    """
    Get statistics grouped by party.
    """
    try:
        # Get all councilors
        councilors = db.query(Councilor).all()

        # Normalize party names and aggregate
        party_map = {}
        for c in councilors:
            normalized = normalize_party_name(c.party)
            if normalized not in party_map:
                party_map[normalized] = {
                    "party": normalized,
                    "member_count": 0,
                    "total_followers": 0
                }
            party_map[normalized]["member_count"] += 1

        return sorted(list(party_map.values()), key=lambda x: x["member_count"], reverse=True)
    except Exception as e:
        return []


@router.get("/engagement")
async def get_engagement_ranking(
    limit: int = 15,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get engagement ranking for all users.
    """
    try:
        # Get councilor map
        councilors = db.query(Councilor).all()
        councilor_map = {c.username: c for c in councilors}

        query = db.query(
            Tweet.username,
            func.count(Tweet.id).label("tweet_count"),
            func.coalesce(func.sum(Tweet.likes), 0).label("total_likes"),
            func.coalesce(func.sum(Tweet.retweets), 0).label("total_retweets"),
            func.coalesce(func.sum(Tweet.replies), 0).label("total_replies"),
            func.coalesce(func.sum(Tweet.views), 0).label("total_views"),
        ).filter(Tweet.is_retweet == False)

        if start_date:
            query = query.filter(Tweet.tweet_date >= start_date)
        if end_date:
            query = query.filter(Tweet.tweet_date <= end_date)

        results = query.group_by(Tweet.username).order_by(
            (func.coalesce(func.sum(Tweet.likes), 0) + func.coalesce(func.sum(Tweet.retweets), 0)).desc()
        ).limit(limit).all()

        return [
            {
                "username": r.username,
                "name": councilor_map.get(r.username).name if councilor_map.get(r.username) else r.username,
                "party": normalize_party_name(councilor_map.get(r.username).party) if councilor_map.get(r.username) else "",
                "tweet_count": r.tweet_count,
                "total_likes": r.total_likes or 0,
                "total_retweets": r.total_retweets or 0,
                "total_replies": r.total_replies or 0,
                "total_views": r.total_views or 0,
                "total_engagement": (r.total_likes or 0) + (r.total_retweets or 0) + (r.total_replies or 0),
            }
            for r in results
        ]
    except Exception as e:
        return []


@router.get("/districts")
async def get_district_statistics(db: Session = Depends(get_db)):
    """
    Get statistics grouped by district.
    """
    try:
        results = db.query(
            Councilor.district,
            func.count(Councilor.id).label("member_count")
        ).group_by(Councilor.district).order_by(func.count(Councilor.id).desc()).all()

        return [
            {
                "district": r.district or "Bilinmiyor",
                "member_count": r.member_count,
            }
            for r in results
        ]
    except Exception as e:
        return []
