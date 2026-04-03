"""
Core Module - Database, Models, Configuration
"""
from .config import settings, DB_PATH, CSV_PATH, MAX_TWEETS_PER_USER, DAYS_BACK
from .models import Base, Councilor, Tweet, ProfileHistory, ReportCache, InstagramPost, InstagramProfile, ChatSession, ChatMessage
from .database import (
    init_database,
    save_tweet,
    save_tweets_batch,
    get_stats,
    save_profile_snapshot,
    get_latest_profile,
    get_profile_change,
    get_all_profile_history,
    save_report_cache,
    get_report_cache,
    clear_report_cache,
    clear_expired_cache,
)
from .db_config import engine, SessionLocal, session_scope, init_db

__all__ = [
    # Config
    "settings",
    "DB_PATH",
    "CSV_PATH",
    "MAX_TWEETS_PER_USER",
    "DAYS_BACK",
    # Models
    "Base",
    "Councilor",
    "Tweet",
    "ProfileHistory",
    "ReportCache",
    "InstagramPost",
    "InstagramProfile",
    "ChatSession",
    "ChatMessage",
    # Database
    "init_database",
    "save_tweet",
    "save_tweets_batch",
    "get_stats",
    "save_profile_snapshot",
    "get_latest_profile",
    "get_profile_change",
    "get_all_profile_history",
    "save_report_cache",
    "get_report_cache",
    "clear_report_cache",
    "clear_expired_cache",
    # DB Config
    "engine",
    "SessionLocal",
    "session_scope",
    "init_db",
]
