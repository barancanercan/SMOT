#!/usr/bin/env python3
"""
📊 Database Schema v3.2
✅ Added: views column to tweets table
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional

DB_PATH = "meclis.db"


def init_database():
    """Initialize database with v3.2 schema (includes views)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Councilors table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS councilors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            name TEXT,
            party TEXT,
            district TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tweets table (v3.2 with views)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tweets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            tweet_text TEXT NOT NULL,
            tweet_date TEXT,
            is_retweet BOOLEAN DEFAULT 0,
            retweet_from TEXT,
            likes INTEGER DEFAULT 0,
            replies INTEGER DEFAULT 0,
            retweets INTEGER DEFAULT 0,
            views INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_deleted BOOLEAN DEFAULT 0,
            FOREIGN KEY (username) REFERENCES councilors(username)
        )
    """)

    # Create indexes for performance
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_tweets_username 
        ON tweets(username)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_tweets_date 
        ON tweets(tweet_date)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_tweets_is_retweet 
        ON tweets(is_retweet)
    """)

    conn.commit()
    conn.close()

    print("✅ Database v3.2 initialized with views support")


def save_tweet(
        username: str,
        tweet_text: str,
        tweet_date: Optional[str] = None,
        is_retweet: bool = False,
        retweet_from: Optional[str] = None,
        likes: int = 0,
        replies: int = 0,
        retweets: int = 0,
        views: int = 0,  # NEW
) -> bool:
    """Save single tweet to database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO tweets 
            (username, tweet_text, tweet_date, is_retweet, retweet_from, 
             likes, replies, retweets, views)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            username,
            tweet_text,
            tweet_date,
            is_retweet,
            retweet_from,
            likes,
            replies,
            retweets,
            views,  # NEW
        ))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Save error: {e}")
        return False


def save_tweets_batch(tweets: List[Dict], username: str) -> int:
    """Save multiple tweets in batch (with deduplication)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    saved_count = 0
    duplicate_count = 0

    for tweet in tweets:
        # Check if tweet already exists (by text + username)
        cursor.execute("""
            SELECT id FROM tweets 
            WHERE username = ? AND tweet_text = ?
        """, (username, tweet.get("text", "")))

        if cursor.fetchone():
            duplicate_count += 1
            continue

        # Insert new tweet
        try:
            cursor.execute("""
                INSERT INTO tweets 
                (username, tweet_text, tweet_date, is_retweet, retweet_from,
                 likes, replies, retweets, views)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                username,
                tweet.get("text", ""),
                tweet.get("timestamp"),
                tweet.get("is_retweet", False),
                tweet.get("retweet_from"),
                tweet.get("likes", 0),
                tweet.get("replies", 0),
                tweet.get("retweets", 0),
                tweet.get("views", 0),  # NEW
            ))
            saved_count += 1
        except Exception as e:
            print(f"  ⚠️  Insert error: {e}")

    conn.commit()
    conn.close()

    return saved_count, duplicate_count


def get_stats() -> Dict:
    """Get database statistics including views"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    stats = {}

    # Total councilors
    cursor.execute("SELECT COUNT(*) FROM councilors")
    stats["total_councilors"] = cursor.fetchone()[0]

    # Total tweets
    cursor.execute("SELECT COUNT(*) FROM tweets")
    stats["total_tweets"] = cursor.fetchone()[0]

    # Retweets
    cursor.execute("SELECT COUNT(*) FROM tweets WHERE is_retweet = 1")
    stats["total_retweets"] = cursor.fetchone()[0]

    # Original tweets
    stats["total_original"] = stats["total_tweets"] - stats["total_retweets"]

    # Active users (with tweets)
    cursor.execute("SELECT COUNT(DISTINCT username) FROM tweets")
    stats["active_users"] = cursor.fetchone()[0]

    # Total engagement
    cursor.execute("""
        SELECT 
            COALESCE(SUM(likes), 0) as total_likes,
            COALESCE(SUM(replies), 0) as total_replies,
            COALESCE(SUM(retweets), 0) as total_retweets,
            COALESCE(SUM(views), 0) as total_views
        FROM tweets
    """)
    row = cursor.fetchone()
    stats["total_likes"] = row[0]
    stats["total_replies"] = row[1]
    stats["total_retweets_count"] = row[2]
    stats["total_views"] = row[3]  # NEW

    conn.close()
    return stats


if __name__ == "__main__":
    print("🏛️ Initializing Meclis Database v3.2...")
    init_database()

    stats = get_stats()
    print("\n📊 Database Stats:")
    for key, value in stats.items():
        print(f"   {key}: {value}")