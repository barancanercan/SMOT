"""
SQLAlchemy ORM Models - Database Schema v4.1
Replaces raw SQL with type-safe ORM models
"""
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Date, ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class Councilor(Base):
    """Council member/representative"""
    __tablename__ = 'councilors'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(200))
    party = Column(String(100))
    district = Column(String(100))
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    tweets = relationship("Tweet", back_populates="councilor", cascade="all, delete-orphan")
    profile_history = relationship("ProfileHistory", back_populates="councilor", cascade="all, delete-orphan")
    report_cache = relationship("ReportCache", back_populates="councilor", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Councilor(username='{self.username}', party='{self.party}')>"


class Tweet(Base):
    """Tweet/post from a councilor"""
    __tablename__ = 'tweets'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), ForeignKey('councilors.username'), nullable=False, index=True)
    tweet_text = Column(Text, nullable=False)
    tweet_date = Column(String(50), index=True)
    is_retweet = Column(Boolean, default=False, index=True)
    retweet_from = Column(String(100))
    likes = Column(Integer, default=0)
    replies = Column(Integer, default=0)
    retweets = Column(Integer, default=0)
    views = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    is_deleted = Column(Boolean, default=False)
    
    # Relationship
    councilor = relationship("Councilor", back_populates="tweets")
    
    def __repr__(self):
        return f"<Tweet(id={self.id}, username='{self.username}', text='{self.tweet_text[:30]}...')>"


class ProfileHistory(Base):
    """Historical snapshots of profile metrics"""
    __tablename__ = 'profile_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), ForeignKey('councilors.username'), nullable=False)
    followers_count = Column(Integer, default=0)
    following_count = Column(Integer, default=0)
    tweet_count = Column(Integer, default=0)
    listed_count = Column(Integer, default=0)
    scrape_date = Column(Date, nullable=False, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationship
    councilor = relationship("Councilor", back_populates="profile_history")
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('username', 'scrape_date', name='uq_profile_username_date'),
        Index('idx_profile_username', 'username'),
        Index('idx_profile_date', 'scrape_date'),
    )
    
    def __repr__(self):
        return f"<ProfileHistory(username='{self.username}', date={self.scrape_date}, followers={self.followers_count})>"


class ReportCache(Base):
    """Cached analysis reports"""
    __tablename__ = 'report_cache'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), ForeignKey('councilors.username'), nullable=False)
    report_type = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    expires_at = Column(DateTime)
    
    # Relationship
    councilor = relationship("Councilor", back_populates="report_cache")
    
    # Unique constraint and index
    __table_args__ = (
        UniqueConstraint('username', 'report_type', name='uq_cache_username_type'),
        Index('idx_report_cache', 'username', 'report_type'),
    )
    
    def __repr__(self):
        return f"<ReportCache(username='{self.username}', type='{self.report_type}')>"
