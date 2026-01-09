#!/usr/bin/env python3
"""
Database Schema v4.0 - Profile History Support
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from config import DB_PATH


def init_database():
    """Initialize database with v4.0 schema"""
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

    # Tweets table
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

    # Profile history table (NEW - v4.0)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS profile_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            followers_count INTEGER DEFAULT 0,
            following_count INTEGER DEFAULT 0,
            tweet_count INTEGER DEFAULT 0,
            listed_count INTEGER DEFAULT 0,
            scrape_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (username) REFERENCES councilors(username),
            UNIQUE(username, scrape_date)
        )
    """)

    # Report cache table (NEW - v4.1)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS report_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            report_type TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            UNIQUE(username, report_type)
        )
    """)

    # Indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tweets_username ON tweets(username)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tweets_date ON tweets(tweet_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tweets_is_retweet ON tweets(is_retweet)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_profile_username ON profile_history(username)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_profile_date ON profile_history(scrape_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_report_cache ON report_cache(username, report_type)")

    conn.commit()
    conn.close()

    print("Database v4.1 initialized")


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


# =============================================================================
# Profile History Functions (v4.0)
# =============================================================================

def save_profile_snapshot(
    username: str,
    followers_count: int,
    following_count: int,
    tweet_count: int = 0,
    listed_count: int = 0,
    scrape_date: Optional[str] = None
) -> bool:
    """Save profile snapshot for a user"""
    if scrape_date is None:
        scrape_date = datetime.now().strftime("%Y-%m-%d")

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO profile_history
            (username, followers_count, following_count, tweet_count, listed_count, scrape_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (username, followers_count, following_count, tweet_count, listed_count, scrape_date))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Profile save error: {e}")
        return False


def get_latest_profile(username: str) -> Optional[Dict]:
    """Get most recent profile snapshot for a user"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT followers_count, following_count, tweet_count, listed_count, scrape_date
        FROM profile_history
        WHERE username = ?
        ORDER BY scrape_date DESC
        LIMIT 1
    """, (username,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "followers": row[0],
            "following": row[1],
            "tweets": row[2],
            "listed": row[3],
            "date": row[4]
        }
    return None


def get_profile_change(username: str, date1: str, date2: str) -> Optional[Dict]:
    """Get profile change between two dates"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get profile at date1 (or closest before)
    cursor.execute("""
        SELECT followers_count, following_count, tweet_count, scrape_date
        FROM profile_history
        WHERE username = ? AND scrape_date <= ?
        ORDER BY scrape_date DESC
        LIMIT 1
    """, (username, date1))
    row1 = cursor.fetchone()

    # Get profile at date2 (or closest before)
    cursor.execute("""
        SELECT followers_count, following_count, tweet_count, scrape_date
        FROM profile_history
        WHERE username = ? AND scrape_date <= ?
        ORDER BY scrape_date DESC
        LIMIT 1
    """, (username, date2))
    row2 = cursor.fetchone()

    conn.close()

    if row1 and row2:
        return {
            "followers_change": row2[0] - row1[0],
            "following_change": row2[1] - row1[1],
            "tweets_change": row2[2] - row1[2],
            "date1": row1[3],
            "date2": row2[3],
            "followers_start": row1[0],
            "followers_end": row2[0]
        }
    return None


def get_all_profile_history(username: str) -> List[Dict]:
    """Get all profile history for a user"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT followers_count, following_count, tweet_count, listed_count, scrape_date
        FROM profile_history
        WHERE username = ?
        ORDER BY scrape_date ASC
    """, (username,))

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "followers": row[0],
            "following": row[1],
            "tweets": row[2],
            "listed": row[3],
            "date": row[4]
        }
        for row in rows
    ]


# =============================================================================
# Report Cache Functions (v4.1)
# =============================================================================

def save_report_cache(username: str, report_type: str, content: str, expire_hours: int = 168) -> bool:
    """
    Raporu cache'e kaydet

    Args:
        username: Kullanici adi
        report_type: Rapor tipi ('full', 'topics', 'party', 'opposition')
        content: Rapor icerigi (markdown)
        expire_hours: Gecerlilik suresi (default 168 = 1 hafta)
    """
    from datetime import timedelta

    expires_at = datetime.now() + timedelta(hours=expire_hours)

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO report_cache
            (username, report_type, content, created_at, expires_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)
        """, (username, report_type, content, expires_at.strftime("%Y-%m-%d %H:%M:%S")))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Cache save error: {e}")
        return False


def get_report_cache(username: str, report_type: str) -> Optional[Dict]:
    """
    Cache'den rapor al (gecerlilik kontrolu ile)

    Returns:
        {'content': str, 'created_at': str} veya None (cache miss/expired)
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT content, created_at, expires_at
        FROM report_cache
        WHERE username = ? AND report_type = ?
        AND expires_at > CURRENT_TIMESTAMP
    """, (username, report_type))

    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            'content': row[0],
            'created_at': row[1],
            'expires_at': row[2]
        }
    return None


def clear_report_cache(username: str = None, report_type: str = None):
    """Cache temizle (kullanici ve/veya tip bazli)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if username and report_type:
        cursor.execute("DELETE FROM report_cache WHERE username = ? AND report_type = ?",
                       (username, report_type))
    elif username:
        cursor.execute("DELETE FROM report_cache WHERE username = ?", (username,))
    elif report_type:
        cursor.execute("DELETE FROM report_cache WHERE report_type = ?", (report_type,))
    else:
        cursor.execute("DELETE FROM report_cache")

    deleted = cursor.rowcount
    conn.commit()
    conn.close()

    return deleted


def clear_expired_cache():
    """Suresi dolmus cache'leri temizle"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM report_cache WHERE expires_at <= CURRENT_TIMESTAMP")
    deleted = cursor.rowcount

    conn.commit()
    conn.close()

    return deleted


if __name__ == "__main__":
    print("Initializing Meclis Database v4.1...")
    init_database()

    stats = get_stats()
    print("\nDatabase Stats:")
    for key, value in stats.items():
        print(f"   {key}: {value}")