#!/usr/bin/env python3
"""
💾 Database Setup & Helpers
SQLite database initialize ve CRUD operations
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Optional

DB_PATH = "meclis.db"


def init_database():
    """Initialize SQLite database with schema"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create tables
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (username) REFERENCES councilors(username)
        )
    """)

    # Create indexes for better query performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tweets_username ON tweets(username)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tweets_date ON tweets(tweet_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tweets_retweet ON tweets(is_retweet)")

    conn.commit()
    conn.close()
    print(f"✅ Database initialized: {DB_PATH}")


def get_connection():
    """Get SQLite connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def load_councilors(councilors: List[Dict]) -> int:
    """Load councilor data into database"""
    conn = get_connection()
    cursor = conn.cursor()

    count = 0
    for councilor in councilors:
        try:
            cursor.execute(
                "INSERT OR REPLACE INTO councilors (username, name, party, district) VALUES (?, ?, ?, ?)",
                (
                    councilor.get('username'),
                    councilor.get('name'),
                    councilor.get('party'),
                    councilor.get('district')
                )
            )
            count += 1
        except Exception as e:
            print(f"⚠️  Error loading {councilor.get('username')}: {e}")

    conn.commit()
    conn.close()
    return count


def save_tweets(username: str, tweets: List[Dict]) -> int:
    """Save tweets for a councilor - with strict validation"""
    if not tweets:
        return 0

    conn = get_connection()
    cursor = conn.cursor()

    # Clear old tweets for this user
    cursor.execute("DELETE FROM tweets WHERE username = ?", (username,))

    count = 0
    for tweet in tweets:
        try:
            # ✅ FIX: Strict text validation
            text = (tweet.get('text', '') or '').strip()
            
            # Skip empty or short tweets
            if not text or len(text) < 5:
                continue
            
            # Ensure not None
            text = text[:500] if text else None
            if not text:
                continue

            cursor.execute(
                """INSERT INTO tweets 
                   (username, tweet_text, tweet_date, is_retweet, retweet_from, likes, replies, retweets)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    username,
                    text,  # Now guaranteed non-empty
                    tweet.get('timestamp'),
                    int(tweet.get('is_retweet', False)),
                    tweet.get('retweet_from'),
                    int(tweet.get('likes', 0)),
                    int(tweet.get('replies', 0)),
                    int(tweet.get('retweets', 0))
                )
            )
            count += 1
        except Exception as e:
            print(f"⚠️  Error saving tweet: {str(e)[:40]}")

    conn.commit()
    conn.close()
    return count


def get_tweets(username: str, limit: int = 50) -> List[Dict]:
    """Get tweets for a user"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT tweet_text, tweet_date, is_retweet, retweet_from, likes, replies, retweets
           FROM tweets 
           WHERE username = ? 
           ORDER BY tweet_date DESC
           LIMIT ?""",
        (username, limit)
    )
    results = cursor.fetchall()
    conn.close()

    tweets_list = []
    for row in results:
        tweets_list.append({
            "text": row[0],
            "date": row[1],
            "is_retweet": bool(row[2]),
            "retweet_from": row[3],
            "likes": row[4],
            "replies": row[5],
            "retweets": row[6]
        })
    return tweets_list


def get_councilors() -> List[Dict]:
    """Get all councilors"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username, name, party, district FROM councilors ORDER BY username")
    results = cursor.fetchall()
    conn.close()

    councilors_list = []
    for row in results:
        councilors_list.append({
            "username": row[0],
            "name": row[1],
            "party": row[2],
            "district": row[3]
        })
    return councilors_list


def get_stats() -> Dict:
    """Get database statistics"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM councilors")
    councilors_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tweets")
    tweets_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tweets WHERE is_retweet = 1")
    retweets_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT username) FROM tweets")
    active_users = cursor.fetchone()[0]

    conn.close()

    return {
        "total_councilors": councilors_count,
        "total_tweets": tweets_count,
        "total_retweets": retweets_count,
        "original_tweets": tweets_count - retweets_count,
        "active_users": active_users
    }


if __name__ == "__main__":
    init_database()
    stats = get_stats()
    print(f"\n📊 Database Stats:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
