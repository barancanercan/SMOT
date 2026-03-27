"""
SQLAlchemy ORM Models - Database Schema v4.1
Replaces raw SQL with type-safe ORM models
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Date
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Councilor(Base):
    """Council member/representative"""
    __tablename__ = 'councilors'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)  # Twitter username
    name = Column(String(200))
    party = Column(String(100))
    district = Column(String(100))
    # Twitter profile details
    bio = Column(Text)
    location = Column(String(200))
    website = Column(String(500))
    verified = Column(Boolean, default=False)
    profile_image_url = Column(String(500))
    join_date = Column(String(50))  # Twitter join date
    profile_updated_at = Column(DateTime)  # Last profile scrape
    # Instagram
    instagram_username = Column(String(100), index=True)  # Instagram username (may differ from Twitter)
    instagram_updated_at = Column(DateTime)  # Last Instagram scrape
    created_at = Column(DateTime, default=func.now(), nullable=True)

    def __repr__(self):
        return f"<Councilor(username='{self.username}', party='{self.party}')>"


class Tweet(Base):
    """Tweet/post from a councilor"""
    __tablename__ = 'tweets'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False, index=True)
    tweet_text = Column(Text, nullable=False)
    tweet_date = Column(String(50), index=True)
    is_retweet = Column(Boolean, default=False, index=True)
    retweet_from = Column(String(100))
    likes = Column(Integer, default=0)
    replies = Column(Integer, default=0)
    retweets = Column(Integer, default=0)
    views = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now(), nullable=True)
    is_deleted = Column(Boolean, default=False)

    def __repr__(self):
        return f"<Tweet(id={self.id}, username='{self.username}')>"


class ProfileHistory(Base):
    """Historical snapshots of profile metrics"""
    __tablename__ = 'profile_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False, index=True)
    followers_count = Column(Integer, default=0)
    following_count = Column(Integer, default=0)
    tweet_count = Column(Integer, default=0)
    listed_count = Column(Integer, default=0)
    scrape_date = Column(Date, nullable=False, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=True)

    def __repr__(self):
        return f"<ProfileHistory(username='{self.username}', date={self.scrape_date})>"


class ReportCache(Base):
    """Cached analysis reports"""
    __tablename__ = 'report_cache'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False, index=True)
    report_type = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=True)
    expires_at = Column(DateTime)

    def __repr__(self):
        return f"<ReportCache(username='{self.username}', type='{self.report_type}')>"


class InstagramPost(Base):
    """Instagram post from a councilor"""
    __tablename__ = 'instagram_posts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False, index=True)
    caption = Column(Text)
    post_date = Column(String(50), index=True)
    post_url = Column(String(500), unique=True)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    is_video = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now(), nullable=True)

    def __repr__(self):
        return f"<InstagramPost(id={self.id}, username='{self.username}')>"


class InstagramProfile(Base):
    """Historical snapshots of Instagram profile metrics"""
    __tablename__ = 'instagram_profiles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False, index=True)
    full_name = Column(String(200))
    bio = Column(Text)
    followers_count = Column(Integer, default=0)
    following_count = Column(Integer, default=0)
    posts_count = Column(Integer, default=0)
    scrape_date = Column(Date, nullable=False, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=True)

    def __repr__(self):
        return f"<InstagramProfile(username='{self.username}', date={self.scrape_date})>"
