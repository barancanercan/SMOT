#!/usr/bin/env python3
"""
Database Operations v5.0 - SQLAlchemy ORM
Migrated from raw SQL to ORM for better maintainability
"""

from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from sqlalchemy import func, and_

from meclis_istihbarat.utils.logger import get_logger
from meclis_istihbarat.utils.retry_config import retry_on_db_error
from meclis_istihbarat.core.db_config import session_scope, init_db as create_tables
from meclis_istihbarat.core.models import Councilor, Tweet, ProfileHistory, ReportCache

logger = get_logger("Database")


def init_database():
    """Initialize database with SQLAlchemy ORM"""
    create_tables()
    logger.info("Database initialized with ORM")


@retry_on_db_error
def save_tweet(
        username: str,
        tweet_text: str,
        tweet_date: Optional[str] = None,
        is_retweet: bool = False,
        retweet_from: Optional[str] = None,
        likes: int = 0,
        replies: int = 0,
        retweets: int = 0,
        views: int = 0,
) -> bool:
    """Save single tweet to database using ORM"""
    try:
        with session_scope() as session:
            tweet = Tweet(
                username=username,
                tweet_text=tweet_text,
                tweet_date=tweet_date,
                is_retweet=is_retweet,
                retweet_from=retweet_from,
                likes=likes,
                replies=replies,
                retweets=retweets,
                views=views
            )
            session.add(tweet)
        return True
    except Exception as e:
        logger.error(f"Save error: {e}")
        return False


@retry_on_db_error
def save_tweets_batch(tweets: List[Dict], username: str) -> Tuple[int, int]:
    """Save multiple tweets in batch (with deduplication) using ORM"""
    saved_count = 0
    duplicate_count = 0

    try:
        with session_scope() as session:
            for tweet_data in tweets:
                # Check if tweet already exists
                existing = session.query(Tweet).filter(
                    and_(
                        Tweet.username == username,
                        Tweet.tweet_text == tweet_data.get("text", "")
                    )
                ).first()

                if existing:
                    duplicate_count += 1
                    continue

                # Insert new tweet
                try:
                    tweet = Tweet(
                        username=username,
                        tweet_text=tweet_data.get("text", ""),
                        tweet_date=tweet_data.get("timestamp"),
                        is_retweet=tweet_data.get("is_retweet", False),
                        retweet_from=tweet_data.get("retweet_from"),
                        likes=tweet_data.get("likes", 0),
                        replies=tweet_data.get("replies", 0),
                        retweets=tweet_data.get("retweets", 0),
                        views=tweet_data.get("views", 0)
                    )
                    session.add(tweet)
                    saved_count += 1
                except Exception as e:
                    logger.error(f"Insert error: {e}")

    except Exception as e:
        logger.error(f"Batch save error: {e}")

    return saved_count, duplicate_count


def get_stats() -> Dict:
    """Get database statistics using ORM"""
    stats = {}

    try:
        with session_scope() as session:
            # Total councilors
            stats["total_councilors"] = session.query(func.count(Councilor.id)).scalar()

            # Total tweets
            stats["total_tweets"] = session.query(func.count(Tweet.id)).scalar()

            # Retweets
            stats["total_retweets"] = session.query(func.count(Tweet.id)).filter(
                Tweet.is_retweet
            ).scalar()

            # Original tweets
            stats["total_original"] = stats["total_tweets"] - stats["total_retweets"]

            # Active users (with tweets)
            stats["active_users"] = session.query(func.count(func.distinct(Tweet.username))).scalar()

            # Total engagement
            engagement = session.query(
                func.coalesce(func.sum(Tweet.likes), 0).label('total_likes'),
                func.coalesce(func.sum(Tweet.replies), 0).label('total_replies'),
                func.coalesce(func.sum(Tweet.retweets), 0).label('total_retweets_count'),
                func.coalesce(func.sum(Tweet.views), 0).label('total_views')
            ).first()

            stats["total_likes"] = engagement.total_likes
            stats["total_replies"] = engagement.total_replies
            stats["total_retweets_count"] = engagement.total_retweets_count
            stats["total_views"] = engagement.total_views

    except Exception as e:
        logger.error(f"Stats error: {e}")

    return stats


# =============================================================================
# Profile History Functions (ORM)
# =============================================================================

@retry_on_db_error
def save_profile_snapshot(
    username: str,
    followers_count: int,
    following_count: int,
    tweet_count: int = 0,
    listed_count: int = 0,
    scrape_date: Optional[str] = None
) -> bool:
    """Save profile snapshot using ORM"""
    if scrape_date is None:
        scrape_date = datetime.now().strftime("%Y-%m-%d")

    try:
        with session_scope() as session:
            # Check if snapshot already exists
            existing = session.query(ProfileHistory).filter(
                and_(
                    ProfileHistory.username == username,
                    ProfileHistory.scrape_date == scrape_date
                )
            ).first()

            if existing:
                # Update existing
                existing.followers_count = followers_count
                existing.following_count = following_count
                existing.tweet_count = tweet_count
                existing.listed_count = listed_count
            else:
                # Create new
                profile = ProfileHistory(
                    username=username,
                    followers_count=followers_count,
                    following_count=following_count,
                    tweet_count=tweet_count,
                    listed_count=listed_count,
                    scrape_date=scrape_date
                )
                session.add(profile)
        
        return True
    except Exception as e:
        logger.error(f"Profile save error: {e}")
        return False


def get_latest_profile(username: str) -> Optional[Dict]:
    """Get most recent profile snapshot using ORM"""
    try:
        with session_scope() as session:
            profile = session.query(ProfileHistory).filter(
                ProfileHistory.username == username
            ).order_by(ProfileHistory.scrape_date.desc()).first()

            if profile:
                return {
                    "followers": profile.followers_count,
                    "following": profile.following_count,
                    "tweets": profile.tweet_count,
                    "listed": profile.listed_count,
                    "date": str(profile.scrape_date)
                }
    except Exception as e:
        logger.error(f"Get latest profile error: {e}")
    
    return None


def get_profile_change(username: str, date1: str, date2: str) -> Optional[Dict]:
    """Get profile change between two dates using ORM"""
    try:
        with session_scope() as session:
            # Get profile at date1 (or closest before)
            profile1 = session.query(ProfileHistory).filter(
                and_(
                    ProfileHistory.username == username,
                    ProfileHistory.scrape_date <= date1
                )
            ).order_by(ProfileHistory.scrape_date.desc()).first()

            # Get profile at date2 (or closest before)
            profile2 = session.query(ProfileHistory).filter(
                and_(
                    ProfileHistory.username == username,
                    ProfileHistory.scrape_date <= date2
                )
            ).order_by(ProfileHistory.scrape_date.desc()).first()

            if profile1 and profile2:
                return {
                    "followers_change": profile2.followers_count - profile1.followers_count,
                    "following_change": profile2.following_count - profile1.following_count,
                    "tweets_change": profile2.tweet_count - profile1.tweet_count,
                    "date1": str(profile1.scrape_date),
                    "date2": str(profile2.scrape_date),
                    "followers_start": profile1.followers_count,
                    "followers_end": profile2.followers_count
                }
    except Exception as e:
        logger.error(f"Get profile change error: {e}")

    return None


def get_all_profile_history(username: str) -> List[Dict]:
    """Get all profile history for a user using ORM"""
    try:
        with session_scope() as session:
            profiles = session.query(ProfileHistory).filter(
                ProfileHistory.username == username
            ).order_by(ProfileHistory.scrape_date.asc()).all()

            return [
                {
                    "followers": p.followers_count,
                    "following": p.following_count,
                    "tweets": p.tweet_count,
                    "listed": p.listed_count,
                    "date": str(p.scrape_date)
                }
                for p in profiles
            ]
    except Exception as e:
        logger.error(f"Get all profile history error: {e}")

    return []


# =============================================================================
# Report Cache Functions (ORM)
# =============================================================================

def save_report_cache(username: str, report_type: str, content: str, expire_hours: int = 168) -> bool:
    """Save report to cache using ORM"""
    expires_at = datetime.now() + timedelta(hours=expire_hours)

    try:
        with session_scope() as session:
            # Check if cache exists
            existing = session.query(ReportCache).filter(
                and_(
                    ReportCache.username == username,
                    ReportCache.report_type == report_type
                )
            ).first()

            if existing:
                # Update existing
                existing.content = content
                existing.created_at = datetime.now()
                existing.expires_at = expires_at
            else:
                # Create new
                cache = ReportCache(
                    username=username,
                    report_type=report_type,
                    content=content,
                    expires_at=expires_at
                )
                session.add(cache)
        
        return True
    except Exception as e:
        logger.error(f"Cache save error: {e}")
        return False


def get_report_cache(username: str, report_type: str) -> Optional[Dict]:
    """Get report from cache (with expiry check) using ORM"""
    try:
        with session_scope() as session:
            cache = session.query(ReportCache).filter(
                and_(
                    ReportCache.username == username,
                    ReportCache.report_type == report_type,
                    ReportCache.expires_at > datetime.now()
                )
            ).first()

            if cache:
                return {
                    'content': cache.content,
                    'created_at': str(cache.created_at),
                    'expires_at': str(cache.expires_at)
                }
    except Exception as e:
        logger.error(f"Get cache error: {e}")

    return None


def clear_report_cache(username: Optional[str] = None, report_type: Optional[str] = None) -> int:
    """Clear cache (user and/or type based) using ORM"""
    try:
        with session_scope() as session:
            query = session.query(ReportCache)

            if username and report_type:
                query = query.filter(
                    and_(
                        ReportCache.username == username,
                        ReportCache.report_type == report_type
                    )
                )
            elif username:
                query = query.filter(ReportCache.username == username)
            elif report_type:
                query = query.filter(ReportCache.report_type == report_type)

            deleted = query.delete()
            return deleted
    except Exception as e:
        logger.error(f"Clear cache error: {e}")
        return 0


def clear_expired_cache() -> int:
    """Clear expired caches using ORM"""
    try:
        with session_scope() as session:
            deleted = session.query(ReportCache).filter(
                ReportCache.expires_at <= datetime.now()
            ).delete()
            return deleted
    except Exception as e:
        logger.error(f"Clear expired cache error: {e}")
        return 0


if __name__ == "__main__":
    logger.info("Initializing Meclis Database v5.0 (SQLAlchemy ORM)...")
    init_database()

    stats = get_stats()
    logger.info("Database Stats:")
    for key, value in stats.items():
        logger.info(f"   {key}: {value}")