"""
Core Module - Database, Models, Configuration
"""
from .config import CSV_PATH, DAYS_BACK, DB_PATH, MAX_TWEETS_PER_USER, settings
from .database import (
    clear_expired_cache,
    clear_report_cache,
    get_all_profile_history,
    get_latest_profile,
    get_profile_change,
    get_report_cache,
    get_stats,
    init_database,
    save_profile_snapshot,
    save_report_cache,
    save_tweet,
    save_tweets_batch,
)
from .db_config import SessionLocal, engine, init_db, session_scope
from .models import (
    Base,
    ChatMessage,
    ChatSession,
    Councilor,
    InstagramPost,
    InstagramProfile,
    ProfileHistory,
    ReportCache,
    Tweet,
)

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
