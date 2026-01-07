#!/usr/bin/env python3
"""Database v3.1 - With Views Field"""

import sqlite3
from datetime import datetime
from typing import List, Dict

DB_PATH = "meclis.db"

def init_database():
    """Initialize database with updated schema"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Councilors table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS councilors (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            name TEXT,
            party TEXT,
            district TEXT,
            last_synced TIMESTAMP,
            sync_status TEXT DEFAULT 'pending'
        )
    """)

    # Tweets table (with views field)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tweets (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            tweet_id TEXT UNIQUE NOT NULL,
            tweet_text TEXT NOT NULL,
            tweet_date TEXT NOT NULL,
            is_retweet BOOLEAN DEFAULT 0,
            retweet_from TEXT,
            likes INTEGER DEFAULT 0,
            replies INTEGER DEFAULT 0,
            retweets INTEGER DEFAULT 0,
            views INTEGER DEFAULT 0,
            engagement_score REAL DEFAULT 0.0,
            is_deleted BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (username) REFERENCES councilors(username),
            UNIQUE(username, tweet_id)
        )
    """)

    # Sync log table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sync_log (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            sync_type TEXT,
            tweets_collected INTEGER,
            duplicates_skipped INTEGER,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (username) REFERENCES councilors(username)
        )
    """)

    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tweets_username ON tweets(username)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tweets_date ON tweets(tweet_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tweets_id ON tweets(tweet_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tweets_rt ON tweets(is_retweet)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tweets_views ON tweets(views)")

    conn.commit()
    conn.close()
    print(f"✅ Database v3.1 initialized: {DB_PATH}")

def get_connection():
    """Get DB connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def load_councilors(councilors: List[Dict]) -> int:
    """Load councilor metadata"""
    conn = get_connection()
    cursor = conn.cursor()
    
    count = 0
    for c in councilors:
        try:
            cursor.execute(
                """INSERT OR REPLACE INTO councilors 
                   (username, name, party, district) 
                   VALUES (?, ?, ?, ?)""",
                (c.get('username'), c.get('name'), c.get('party'), c.get('district'))
            )
            count += 1
        except:
            pass
    
    conn.commit()
    conn.close()
    return count

def save_tweets(username: str, tweets: List[Dict]) -> Dict:
    """Save tweets with deduplication"""
    if not tweets:
        return {"saved": 0, "duplicates": 0, "errors": 0}

    conn = get_connection()
    cursor = conn.cursor()
    
    saved = 0
    duplicates = 0
    errors = 0

    try:
        cursor.execute("BEGIN TRANSACTION")
        
        # Get existing tweet IDs
        cursor.execute(
            "SELECT tweet_id FROM tweets WHERE username = ? AND is_deleted = 0", 
            (username,)
        )
        existing_ids = set(row[0] for row in cursor.fetchall())

        for tweet in tweets:
            try:
                text = (tweet.get('text', '') or '').strip()
                if not text or len(text) < 5:
                    errors += 1
                    continue

                timestamp = tweet.get('timestamp')
                if not timestamp:
                    errors += 1
                    continue

                # Generate unique ID
                tweet_id = f"{username}_{hash(text + timestamp) % 10000000}"

                # Skip duplicates
                if tweet_id in existing_ids:
                    duplicates += 1
                    continue

                # Calculate score
                likes = int(tweet.get('likes', 0))
                replies = int(tweet.get('replies', 0))
                retweets = int(tweet.get('retweets', 0))
                score = (likes * 0.3) + (replies * 0.5) + (retweets * 0.2)

                # Insert with views
                cursor.execute(
                    """INSERT INTO tweets 
                       (username, tweet_id, tweet_text, tweet_date, is_retweet, 
                        retweet_from, likes, replies, retweets, views, engagement_score)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        username, tweet_id, text, timestamp,
                        int(tweet.get('is_retweet', False)),
                        tweet.get('retweet_from'),
                        likes, replies, retweets,
                        int(tweet.get('views', 0)),
                        score
                    )
                )
                saved += 1
                existing_ids.add(tweet_id)

            except Exception as e:
                errors += 1

        # Update sync timestamp
        cursor.execute(
            "UPDATE councilors SET last_synced = ? WHERE username = ?",
            (datetime.now().isoformat(), username)
        )

        # Log sync
        cursor.execute(
            """INSERT INTO sync_log (username, sync_type, tweets_collected, duplicates_skipped, status)
               VALUES (?, ?, ?, ?, ?)""",
            (username, 'full', saved, duplicates, 'success')
        )

        conn.commit()

    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")

    finally:
        conn.close()

    return {"saved": saved, "duplicates": duplicates, "errors": errors}

def get_tweets(username: str, limit: int = 100) -> List[Dict]:
    """Get tweets for user"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT tweet_id, tweet_text, tweet_date, is_retweet, retweet_from, 
                  likes, replies, retweets, views, engagement_score
           FROM tweets 
           WHERE username = ? AND is_deleted = 0
           ORDER BY tweet_date DESC
           LIMIT ?""",
        (username, limit)
    )
    results = cursor.fetchall()
    conn.close()

    tweets_list = []
    for row in results:
        tweets_list.append({
            "tweet_id": row[0],
            "text": row[1],
            "date": row[2],
            "is_retweet": bool(row[3]),
            "retweet_from": row[4],
            "likes": row[5],
            "replies": row[6],
            "retweets": row[7],
            "views": row[8],
            "engagement_score": row[9]
        })
    return tweets_list

def get_stats() -> Dict:
    """Get database stats"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM councilors")
    councilors = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tweets WHERE is_deleted = 0")
    tweets = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tweets WHERE is_retweet = 1 AND is_deleted = 0")
    retweets = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT username) FROM tweets WHERE is_deleted = 0")
    active = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(views) FROM tweets WHERE is_deleted = 0")
    total_views = cursor.fetchone()[0] or 0

    conn.close()

    return {
        "total_councilors": councilors,
        "total_tweets": tweets,
        "total_retweets": retweets,
        "original_tweets": tweets - retweets,
        "active_users": active,
        "total_views": total_views
    }

if __name__ == "__main__":
    init_database()
    stats = get_stats()
    print("\n📊 Database Stats:")
    for key, value in stats.items():
        print(f"   {key}: {value}")

