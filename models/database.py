#!/usr/bin/env python3
"""
Database initialization and management
Handles SQLite setup with proper schema
"""

import sqlite3
from pathlib import Path

DB_PATH = "meclis.db"


def init_database(db_path: str = DB_PATH) -> sqlite3.Connection:
    """
    Initialize SQLite database with improved schema v2.0
    Creates tables, indexes, and constraints
    """
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Enable modern SQLite features
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute("PRAGMA journal_mode = WAL")
    
    print("\n" + "="*70)
    print("📊 DATABASE INITIALIZATION v2.0")
    print("="*70 + "\n")
    
    try:
        # ========== TABLE 1: COUNCILORS ==========
        print("[1/3] Creating councilors table...", end=" ")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS councilors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                party TEXT,
                district TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_tweets_collected INTEGER DEFAULT 0,
                last_scrape TIMESTAMP,
                
                CHECK(username NOT NULL AND length(username) > 0),
                CHECK(name NOT NULL AND length(name) > 0)
            )
        """)
        print("✅")
        
        # ========== TABLE 2: TWEETS ==========
        print("[2/3] Creating tweets table...", end=" ")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tweets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                tweet_text TEXT NOT NULL,
                tweet_hash TEXT,
                tweet_date TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_retweet BOOLEAN DEFAULT 0,
                retweet_from TEXT,
                likes INTEGER DEFAULT 0,
                replies INTEGER DEFAULT 0,
                retweets INTEGER DEFAULT 0,
                sentiment_score REAL,
                analysis_json TEXT,
                
                FOREIGN KEY(username) REFERENCES councilors(username) 
                    ON DELETE CASCADE ON UPDATE CASCADE,
                UNIQUE(username, tweet_hash, tweet_date),
                CHECK(likes >= 0 AND replies >= 0 AND retweets >= 0),
                CHECK(sentiment_score IS NULL OR 
                      (sentiment_score >= -1 AND sentiment_score <= 1))
            )
        """)
        print("✅")
        
        # ========== TABLE 3: ANALYSIS_CACHE ==========
        print("[3/3] Creating analysis_cache table...", end=" ")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                question TEXT NOT NULL,
                answer TEXT,
                model_version TEXT DEFAULT 'qwen2.5:7b',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY(username) REFERENCES councilors(username) 
                    ON DELETE CASCADE,
                UNIQUE(username, question)
            )
        """)
        print("✅")
        
        # ========== CREATE INDEXES ==========
        print("\n[4/4] Creating indexes...", end=" ")
        indexes = [
            ("idx_councilors_username", "councilors", "username"),
            ("idx_councilors_party", "councilors", "party"),
            ("idx_councilors_last_scrape", "councilors", "last_scrape"),
            ("idx_tweets_username", "tweets", "username"),
            ("idx_tweets_date", "tweets", "tweet_date"),
            ("idx_tweets_hash", "tweets", "tweet_hash"),
            ("idx_tweets_created", "tweets", "created_at DESC"),
            ("idx_tweets_is_retweet", "tweets", "is_retweet"),
        ]
        
        for idx_name, table, column in indexes:
            cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table}({column})")
        
        print(f"✅ ({len(indexes)} indexes)")
        
        # ========== COMMIT & VERIFY ==========
        conn.commit()
        
        print("\n[✓] VERIFICATION")
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        table_count = cursor.fetchone()[0]
        print(f"   ✅ Tables: {table_count}")
        
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index'")
        index_count = cursor.fetchone()[0]
        print(f"   ✅ Indexes: {index_count}")
        
        cursor.execute("PRAGMA foreign_keys")
        fk_status = "ON" if cursor.fetchone()[0] == 1 else "OFF"
        print(f"   ✅ Foreign Keys: {fk_status}")
        
        print("\n" + "="*70)
        print(f"✅ Database ready: {DB_PATH}")
        print("="*70 + "\n")
        
        return conn
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        conn.rollback()
        conn.close()
        raise


if __name__ == "__main__":
    init_database()
