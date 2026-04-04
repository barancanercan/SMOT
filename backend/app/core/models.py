"""
SQLAlchemy ORM Models - Database Schema v5.0
Replaces raw SQL with type-safe ORM models

v5.0 additions:
- ChatSession: Persistent chat sessions
- ChatMessage: Chat message history
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Date, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship
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
    tweet_id = Column(String(50), index=True)  # X/Twitter tweet ID
    tweet_text = Column(Text, nullable=False)
    tweet_date = Column(String(50), index=True)
    is_retweet = Column(Boolean, default=False, index=True)
    retweet_from = Column(String(100), index=True)  # Who was retweeted
    likes = Column(Integer, default=0)
    replies = Column(Integer, default=0)
    retweets = Column(Integer, default=0)
    views = Column(Integer, default=0)
    quotes = Column(Integer, default=0)  # Quote tweet count
    bookmarks = Column(Integer, default=0)  # Bookmark count
    tweet_url = Column(String(500))  # Direct URL to tweet
    media_type = Column(String(50))  # photo, video, gif, poll, none
    language = Column(String(10))  # Tweet language (tr, en, etc.)
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


# =============================================================================
# Chat Session Models (v5.0)
# =============================================================================

class ChatSession(Base):
    """
    Chat session for persistent conversation history.

    Each session represents a single chat conversation that can be:
    - Resumed after page refresh
    - Switched between multiple sessions
    - Filtered by platform and party
    """
    __tablename__ = 'chat_sessions'

    id = Column(String(36), primary_key=True)  # UUID
    title = Column(String(200))  # Auto-generated from first message
    platform = Column(String(20), default="twitter")  # twitter, instagram, both
    party_filter = Column(String(100), nullable=True)  # Optional party filter
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationship to messages
    messages = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at"
    )

    def __repr__(self):
        return f"<ChatSession(id='{self.id}', title='{self.title}')>"


class ChatMessage(Base):
    """
    Individual message in a chat session.

    Stores both user queries and assistant responses with metadata.
    """
    __tablename__ = 'chat_messages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), ForeignKey('chat_sessions.id', ondelete='CASCADE'), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    message_metadata = Column(JSON, nullable=True)  # Store filters, summary, execution time, etc.
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationship back to session
    session = relationship("ChatSession", back_populates="messages")

    def __repr__(self):
        return f"<ChatMessage(id={self.id}, role='{self.role}', session='{self.session_id}')>"
