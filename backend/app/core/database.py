#!/usr/bin/env python3
"""
Database Operations v5.0 - SQLAlchemy ORM
Migrated from raw SQL to ORM for better maintainability
"""

from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from sqlalchemy import func, and_

from app.utils.logger import get_logger
from app.utils.retry_config import retry_on_db_error
from app.core.db_config import session_scope, init_db as create_tables
from app.core.models import Councilor, Tweet, ProfileHistory, ReportCache, InstagramPost, InstagramProfile

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

                # Insert new tweet with all metadata
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
                        views=tweet_data.get("views", 0),
                        tweet_id=tweet_data.get("tweet_id"),
                        tweet_url=tweet_data.get("tweet_url"),
                        quotes=tweet_data.get("quotes", 0),
                        bookmarks=tweet_data.get("bookmarks", 0),
                        media_type=tweet_data.get("media_type"),
                        language=tweet_data.get("language"),
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

            # Total profile records
            stats["total_profiles"] = session.query(func.count(ProfileHistory.id)).scalar()

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
    from datetime import date as date_type

    # Convert string to date object
    if scrape_date is None:
        date_obj = datetime.now().date()
    elif isinstance(scrape_date, str):
        date_obj = datetime.strptime(scrape_date, "%Y-%m-%d").date()
    else:
        date_obj = scrape_date

    try:
        with session_scope() as session:
            # Check if snapshot already exists
            existing = session.query(ProfileHistory).filter(
                and_(
                    ProfileHistory.username == username,
                    ProfileHistory.scrape_date == date_obj
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
                    scrape_date=date_obj
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
# Councilor Profile Update Functions (ORM)
# =============================================================================

@retry_on_db_error
def update_councilor_profile(
    username: str,
    bio: str = "",
    location: str = "",
    website: str = "",
    verified: bool = False,
    profile_image_url: str = "",
    join_date: str = ""
) -> bool:
    """Update councilor's detailed profile information"""
    try:
        with session_scope() as session:
            councilor = session.query(Councilor).filter(
                Councilor.username == username
            ).first()

            if councilor:
                councilor.bio = bio
                councilor.location = location
                councilor.website = website
                councilor.verified = verified
                councilor.profile_image_url = profile_image_url
                councilor.join_date = join_date
                councilor.profile_updated_at = datetime.now()
                return True
            else:
                logger.warning(f"Councilor not found: {username}")
                return False
    except Exception as e:
        logger.error(f"Update councilor profile error: {e}")
        return False


def get_councilor_profile(username: str) -> Optional[Dict]:
    """Get councilor's full profile including Twitter details"""
    try:
        with session_scope() as session:
            councilor = session.query(Councilor).filter(
                Councilor.username == username
            ).first()

            if councilor:
                return {
                    "username": councilor.username,
                    "name": councilor.name,
                    "party": councilor.party,
                    "district": councilor.district,
                    "bio": councilor.bio,
                    "location": councilor.location,
                    "website": councilor.website,
                    "verified": councilor.verified,
                    "profile_image_url": councilor.profile_image_url,
                    "join_date": councilor.join_date,
                    "profile_updated_at": str(councilor.profile_updated_at) if councilor.profile_updated_at else None
                }
    except Exception as e:
        logger.error(f"Get councilor profile error: {e}")

    return None


def get_councilors_without_profile() -> List[str]:
    """Get usernames of councilors without profile details"""
    try:
        with session_scope() as session:
            councilors = session.query(Councilor.username).filter(
                Councilor.profile_updated_at == None
            ).all()
            return [c.username for c in councilors]
    except Exception as e:
        logger.error(f"Get councilors without profile error: {e}")
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


# =============================================================================
# Instagram Functions (ORM)
# =============================================================================

@retry_on_db_error
def save_instagram_post(
    username: str,
    caption: str,
    post_url: str,
    post_date: Optional[str] = None,
    likes: int = 0,
    comments: int = 0,
    is_video: bool = False,
) -> bool:
    """Save single Instagram post to database"""
    try:
        with session_scope() as session:
            # Check if post already exists (by URL)
            existing = session.query(InstagramPost).filter(
                InstagramPost.post_url == post_url
            ).first()

            if existing:
                # Update metrics
                existing.likes = likes
                existing.comments = comments
                return True

            post = InstagramPost(
                username=username,
                caption=caption,
                post_date=post_date,
                post_url=post_url,
                likes=likes,
                comments=comments,
                is_video=is_video
            )
            session.add(post)
        return True
    except Exception as e:
        logger.error(f"Instagram post save error: {e}")
        return False


@retry_on_db_error
def save_instagram_posts_batch(posts: List[Dict], username: str) -> Tuple[int, int]:
    """Save multiple Instagram posts in batch"""
    saved_count = 0
    duplicate_count = 0

    try:
        with session_scope() as session:
            for post_data in posts:
                post_url = post_data.get("post_url", "")

                # Check if post already exists
                existing = session.query(InstagramPost).filter(
                    InstagramPost.post_url == post_url
                ).first()

                if existing:
                    # Update metrics
                    existing.likes = post_data.get("likes", 0)
                    existing.comments = post_data.get("comments", 0)
                    duplicate_count += 1
                    continue

                # Insert new post
                try:
                    post = InstagramPost(
                        username=username,
                        caption=post_data.get("caption", ""),
                        post_date=post_data.get("post_date"),
                        post_url=post_url,
                        likes=post_data.get("likes", 0),
                        comments=post_data.get("comments", 0),
                        is_video=post_data.get("is_video", False)
                    )
                    session.add(post)
                    saved_count += 1
                except Exception as e:
                    logger.error(f"Instagram post insert error: {e}")

    except Exception as e:
        logger.error(f"Instagram batch save error: {e}")

    return saved_count, duplicate_count


@retry_on_db_error
def save_instagram_profile(
    username: str,
    followers_count: int,
    following_count: int,
    posts_count: int = 0,
    full_name: str = "",
    bio: str = "",
    scrape_date: Optional[str] = None
) -> bool:
    """Save Instagram profile snapshot"""
    # Convert string to date object
    if scrape_date is None:
        date_obj = datetime.now().date()
    elif isinstance(scrape_date, str):
        date_obj = datetime.strptime(scrape_date, "%Y-%m-%d").date()
    else:
        date_obj = scrape_date

    try:
        with session_scope() as session:
            # Check if snapshot already exists
            existing = session.query(InstagramProfile).filter(
                and_(
                    InstagramProfile.username == username,
                    InstagramProfile.scrape_date == date_obj
                )
            ).first()

            if existing:
                # Update existing
                existing.followers_count = followers_count
                existing.following_count = following_count
                existing.posts_count = posts_count
                existing.full_name = full_name
                existing.bio = bio
            else:
                # Create new
                profile = InstagramProfile(
                    username=username,
                    full_name=full_name,
                    bio=bio,
                    followers_count=followers_count,
                    following_count=following_count,
                    posts_count=posts_count,
                    scrape_date=date_obj
                )
                session.add(profile)

        return True
    except Exception as e:
        logger.error(f"Instagram profile save error: {e}")
        return False


def get_instagram_posts(username: str, limit: int = 50) -> List[Dict]:
    """Get Instagram posts for a user"""
    try:
        with session_scope() as session:
            posts = session.query(InstagramPost).filter(
                InstagramPost.username == username
            ).order_by(InstagramPost.post_date.desc()).limit(limit).all()

            return [
                {
                    "id": p.id,
                    "username": p.username,
                    "caption": p.caption,
                    "post_date": p.post_date,
                    "post_url": p.post_url,
                    "likes": p.likes,
                    "comments": p.comments,
                    "is_video": p.is_video
                }
                for p in posts
            ]
    except Exception as e:
        logger.error(f"Get Instagram posts error: {e}")
        return []


def get_latest_instagram_profile(username: str) -> Optional[Dict]:
    """Get most recent Instagram profile snapshot"""
    try:
        with session_scope() as session:
            profile = session.query(InstagramProfile).filter(
                InstagramProfile.username == username
            ).order_by(InstagramProfile.scrape_date.desc()).first()

            if profile:
                return {
                    "username": profile.username,
                    "full_name": profile.full_name,
                    "bio": profile.bio,
                    "followers": profile.followers_count,
                    "following": profile.following_count,
                    "posts_count": profile.posts_count,
                    "date": str(profile.scrape_date)
                }
    except Exception as e:
        logger.error(f"Get Instagram profile error: {e}")

    return None


# =============================================================================
# Multi-Platform Query Functions
# =============================================================================

def get_instagram_stats() -> Dict:
    """Get Instagram-specific statistics"""
    stats = {}

    try:
        with session_scope() as session:
            # Total Instagram posts
            stats["total_posts"] = session.query(func.count(InstagramPost.id)).scalar() or 0

            # Total Instagram profiles
            stats["total_instagram_profiles"] = session.query(
                func.count(func.distinct(InstagramProfile.username))
            ).scalar() or 0

            # Active Instagram users (with posts)
            stats["instagram_active_users"] = session.query(
                func.count(func.distinct(InstagramPost.username))
            ).scalar() or 0

            # Total engagement
            engagement = session.query(
                func.coalesce(func.sum(InstagramPost.likes), 0).label('total_likes'),
                func.coalesce(func.sum(InstagramPost.comments), 0).label('total_comments')
            ).first()

            stats["total_instagram_likes"] = engagement.total_likes if engagement else 0
            stats["total_comments"] = engagement.total_comments if engagement else 0

            # Video vs photo count
            stats["total_videos"] = session.query(func.count(InstagramPost.id)).filter(
                InstagramPost.is_video == True
            ).scalar() or 0

            stats["total_photos"] = stats["total_posts"] - stats["total_videos"]

    except Exception as e:
        logger.error(f"Instagram stats error: {e}")

    return stats


def get_content_by_platform(username: str, platform: str, limit: int = 50) -> List[Dict]:
    """
    Get content (tweets or Instagram posts) based on platform.

    Args:
        username: User's username
        platform: 'twitter', 'instagram', or 'both'
        limit: Maximum number of items to return

    Returns:
        List of content items
    """
    content = []

    try:
        with session_scope() as session:
            if platform in ["twitter", "both"]:
                # Get tweets
                tweets = session.query(Tweet).filter(
                    Tweet.username == username,
                    Tweet.is_retweet == False
                ).order_by(Tweet.tweet_date.desc()).limit(limit).all()

                for t in tweets:
                    content.append({
                        "platform": "twitter",
                        "id": t.id,
                        "text": t.tweet_text,
                        "date": t.tweet_date,
                        "likes": t.likes or 0,
                        "retweets": t.retweets or 0,
                        "replies": t.replies or 0,
                        "views": t.views or 0,
                        "engagement": (t.likes or 0) + (t.retweets or 0) + (t.replies or 0)
                    })

            if platform in ["instagram", "both"]:
                # Get Instagram posts
                posts = session.query(InstagramPost).filter(
                    InstagramPost.username == username
                ).order_by(InstagramPost.post_date.desc()).limit(limit).all()

                for p in posts:
                    content.append({
                        "platform": "instagram",
                        "id": p.id,
                        "text": p.caption or "",
                        "date": p.post_date,
                        "likes": p.likes or 0,
                        "comments": p.comments or 0,
                        "is_video": p.is_video,
                        "post_url": p.post_url,
                        "engagement": (p.likes or 0) + (p.comments or 0)
                    })

            # Sort by date if both platforms
            if platform == "both":
                content.sort(key=lambda x: x.get("date", "") or "", reverse=True)
                content = content[:limit]

    except Exception as e:
        logger.error(f"Get content by platform error: {e}")

    return content


def get_profile_by_platform(username: str, platform: str) -> Optional[Dict]:
    """
    Get profile information based on platform.

    Args:
        username: User's username
        platform: 'twitter', 'instagram', or 'both'

    Returns:
        Profile dictionary with platform-specific data
    """
    profile = {"username": username}

    try:
        with session_scope() as session:
            if platform in ["twitter", "both"]:
                # Get Twitter profile
                twitter_profile = session.query(ProfileHistory).filter(
                    ProfileHistory.username == username
                ).order_by(ProfileHistory.scrape_date.desc()).first()

                if twitter_profile:
                    profile["twitter"] = {
                        "followers": twitter_profile.followers_count,
                        "following": twitter_profile.following_count,
                        "tweets": twitter_profile.tweet_count,
                        "listed": twitter_profile.listed_count,
                        "date": str(twitter_profile.scrape_date)
                    }

            if platform in ["instagram", "both"]:
                # Get Instagram profile
                ig_profile = session.query(InstagramProfile).filter(
                    InstagramProfile.username == username
                ).order_by(InstagramProfile.scrape_date.desc()).first()

                if ig_profile:
                    profile["instagram"] = {
                        "followers": ig_profile.followers_count,
                        "following": ig_profile.following_count,
                        "posts_count": ig_profile.posts_count,
                        "full_name": ig_profile.full_name,
                        "bio": ig_profile.bio,
                        "date": str(ig_profile.scrape_date)
                    }

    except Exception as e:
        logger.error(f"Get profile by platform error: {e}")
        return None

    return profile if len(profile) > 1 else None


def get_engagement_by_platform(username: str, platform: str) -> Dict:
    """
    Get engagement metrics based on platform.

    Args:
        username: User's username
        platform: 'twitter', 'instagram', or 'both'

    Returns:
        Engagement metrics dictionary
    """
    metrics = {
        "username": username,
        "platform": platform,
        "twitter": None,
        "instagram": None,
        "combined": None
    }

    try:
        with session_scope() as session:
            if platform in ["twitter", "both"]:
                # Twitter engagement
                twitter_stats = session.query(
                    func.count(Tweet.id).label("tweet_count"),
                    func.coalesce(func.sum(Tweet.likes), 0).label("total_likes"),
                    func.coalesce(func.sum(Tweet.retweets), 0).label("total_retweets"),
                    func.coalesce(func.sum(Tweet.replies), 0).label("total_replies"),
                    func.coalesce(func.sum(Tweet.views), 0).label("total_views"),
                ).filter(
                    Tweet.username == username,
                    Tweet.is_retweet == False
                ).first()

                if twitter_stats:
                    metrics["twitter"] = {
                        "content_count": twitter_stats.tweet_count,
                        "total_likes": twitter_stats.total_likes,
                        "total_retweets": twitter_stats.total_retweets,
                        "total_replies": twitter_stats.total_replies,
                        "total_views": twitter_stats.total_views,
                        "total_engagement": twitter_stats.total_likes + twitter_stats.total_retweets + twitter_stats.total_replies
                    }

            if platform in ["instagram", "both"]:
                # Instagram engagement
                ig_stats = session.query(
                    func.count(InstagramPost.id).label("post_count"),
                    func.coalesce(func.sum(InstagramPost.likes), 0).label("total_likes"),
                    func.coalesce(func.sum(InstagramPost.comments), 0).label("total_comments"),
                ).filter(
                    InstagramPost.username == username
                ).first()

                if ig_stats:
                    metrics["instagram"] = {
                        "content_count": ig_stats.post_count,
                        "total_likes": ig_stats.total_likes,
                        "total_comments": ig_stats.total_comments,
                        "total_engagement": ig_stats.total_likes + ig_stats.total_comments
                    }

            # Combined metrics
            if platform == "both" and metrics["twitter"] and metrics["instagram"]:
                metrics["combined"] = {
                    "total_content": (metrics["twitter"]["content_count"] or 0) + (metrics["instagram"]["content_count"] or 0),
                    "total_likes": (metrics["twitter"]["total_likes"] or 0) + (metrics["instagram"]["total_likes"] or 0),
                    "total_engagement": (metrics["twitter"]["total_engagement"] or 0) + (metrics["instagram"]["total_engagement"] or 0)
                }

    except Exception as e:
        logger.error(f"Get engagement by platform error: {e}")

    return metrics


def get_instagram_followers_ranking(limit: int = 20) -> List[Dict]:
    """Get Instagram followers ranking"""
    try:
        with session_scope() as session:
            # Get councilors
            councilors = session.query(Councilor).all()
            councilor_map = {c.instagram_username: c for c in councilors if c.instagram_username}
            councilor_map.update({c.username: c for c in councilors})

            # Get latest profile for each user
            subquery = session.query(
                InstagramProfile.username,
                func.max(InstagramProfile.scrape_date).label("max_date")
            ).group_by(InstagramProfile.username).subquery()

            profiles = session.query(InstagramProfile).join(
                subquery,
                (InstagramProfile.username == subquery.c.username) &
                (InstagramProfile.scrape_date == subquery.c.max_date)
            ).order_by(InstagramProfile.followers_count.desc()).limit(limit).all()

            result = []
            for p in profiles:
                c = councilor_map.get(p.username)
                result.append({
                    "username": p.username,
                    "name": c.name if c else p.full_name or p.username,
                    "party": c.party if c else "",
                    "district": c.district if c else "",
                    "followers_count": p.followers_count or 0,
                    "following_count": p.following_count or 0,
                    "posts_count": p.posts_count or 0,
                    "platform": "instagram"
                })
            return result

    except Exception as e:
        logger.error(f"Instagram followers ranking error: {e}")
        return []


def get_instagram_engagement_ranking(limit: int = 15) -> List[Dict]:
    """Get Instagram engagement ranking"""
    try:
        with session_scope() as session:
            # Get councilors
            councilors = session.query(Councilor).all()
            councilor_map = {c.instagram_username: c for c in councilors if c.instagram_username}
            councilor_map.update({c.username: c for c in councilors})

            results = session.query(
                InstagramPost.username,
                func.count(InstagramPost.id).label("post_count"),
                func.coalesce(func.sum(InstagramPost.likes), 0).label("total_likes"),
                func.coalesce(func.sum(InstagramPost.comments), 0).label("total_comments"),
            ).group_by(InstagramPost.username).order_by(
                (func.coalesce(func.sum(InstagramPost.likes), 0) +
                 func.coalesce(func.sum(InstagramPost.comments), 0)).desc()
            ).limit(limit).all()

            ranking = []
            for r in results:
                c = councilor_map.get(r.username)
                ranking.append({
                    "username": r.username,
                    "name": c.name if c else r.username,
                    "party": c.party if c else "",
                    "post_count": r.post_count,
                    "total_likes": r.total_likes or 0,
                    "total_comments": r.total_comments or 0,
                    "total_engagement": (r.total_likes or 0) + (r.total_comments or 0),
                    "platform": "instagram"
                })
            return ranking

    except Exception as e:
        logger.error(f"Instagram engagement ranking error: {e}")
        return []


if __name__ == "__main__":
    logger.info("Initializing Meclis Database v5.0 (SQLAlchemy ORM)...")
    init_database()

    stats = get_stats()
    logger.info("Database Stats:")
    for key, value in stats.items():
        logger.info(f"   {key}: {value}")