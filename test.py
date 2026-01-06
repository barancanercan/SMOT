#!/usr/bin/env python3
"""
🧪 TEST APP - Module 1: Scraping & Storage
CSV → Scrape X → Database → Display Table

Bu uygulama SADECE veri toplama ve gösterime odaklanır.
"""

import sys
import sqlite3
import pandas as pd
from pathlib import Path
from typing import List, Tuple
from tabulate import tabulate

# Import scraper
try:
    from x_scraper import XTwitterScraper
except ImportError:
    print("❌ x_scraper.py bulunamadı")
    sys.exit(1)

# ============================================================================
# CONFIG
# ============================================================================

DB_PATH = "test_meclis.db"
DATA_CSV = "data/data.csv"


# ============================================================================
# DATABASE FUNCTIONS
# ============================================================================

def init_database():
    """Initialize test database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

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

    # Indexes for better query performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tweets_username ON tweets(username)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tweets_date ON tweets(tweet_date)")

    conn.commit()
    conn.close()
    print("✅ Database initialized")


def save_councilor(username: str, name: str, party: str, district: str):
    """Save councilor metadata"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT OR REPLACE INTO councilors (username, name, party, district) VALUES (?, ?, ?, ?)",
        (username, name, party, district)
    )

    conn.commit()
    conn.close()


def save_tweets_for_user(username: str, tweets: List[dict]) -> int:
    """Save tweets for a user - returns count"""
    if not tweets:
        return 0

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Delete old tweets for this user
    cursor.execute("DELETE FROM tweets WHERE username = ?", (username,))

    count = 0
    for tweet in tweets:
        try:
            text = tweet.get('text', '')[:500]
            if not text or len(text) < 5:
                continue

            cursor.execute(
                """INSERT INTO tweets 
                   (username, tweet_text, tweet_date, is_retweet, retweet_from, likes, replies, retweets)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    username,
                    text,
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
            print(f"    ⚠️  Tweet error: {str(e)[:30]}")

    conn.commit()
    conn.close()
    return count


def get_all_data() -> pd.DataFrame:
    """Get all tweets as DataFrame for display"""
    conn = sqlite3.connect(DB_PATH)

    query = """
        SELECT 
            c.username,
            c.name,
            c.party,
            COUNT(t.id) as tweet_count,
            SUM(CASE WHEN t.is_retweet = 1 THEN 1 ELSE 0 END) as retweet_count,
            COUNT(t.id) - SUM(CASE WHEN t.is_retweet = 1 THEN 1 ELSE 0 END) as original_count
        FROM councilors c
        LEFT JOIN tweets t ON c.username = t.username
        GROUP BY c.username
        ORDER BY tweet_count DESC
    """

    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_tweets_detail(username: str) -> pd.DataFrame:
    """Get tweet details for a specific user"""
    conn = sqlite3.connect(DB_PATH)

    query = """
        SELECT 
            tweet_text as Tweet,
            tweet_date as Date,
            likes as Likes,
            replies as Replies,
            retweets as Retweets,
            CASE WHEN is_retweet = 1 THEN retweet_from ELSE 'Original' END as Type
        FROM tweets
        WHERE username = ?
        ORDER BY tweet_date DESC
        LIMIT 20
    """

    df = pd.read_sql_query(query, conn, params=(username,))
    conn.close()
    return df


# ============================================================================
# CSV PARSING
# ============================================================================

def parse_csv(csv_path: str) -> List[dict]:
    """Parse CSV and extract councilor data"""
    print("\n[STEP 1] CSV Parsing")
    print("=" * 70)

    try:
        df = pd.read_csv(csv_path)
        print(f"✅ CSV opened: {csv_path}")
        print(f"   Rows: {len(df)}")
        print(f"   Columns: {list(df.columns)}\n")

        councilors = []
        for _, row in df.iterrows():
            link = str(row.get("link", "")).strip()
            if link and "x.com/" in link:
                username = link.split("x.com/")[-1].strip("/").replace("@", "")

                councilors.append({
                    "username": username,
                    "name": str(row.get("Meclis Üyesi", "Unknown")).strip(),
                    "party": str(row.get("Parti", "Unknown")).strip(),
                    "district": str(row.get("İlçe", "Unknown")).strip()
                })

        print(f"✅ Found {len(councilors)} councilors:")
        for i, c in enumerate(councilors[:5], 1):
            print(f"   {i}. @{c['username']:20s} ({c['name']})")
        if len(councilors) > 5:
            print(f"   ... +{len(councilors) - 5} more\n")

        return councilors

    except Exception as e:
        print(f"❌ CSV Error: {e}\n")
        return []


# ============================================================================
# SCRAPING
# ============================================================================

def scrape_tweets(councilors: List[dict], max_tweets: int = 50) -> dict:
    """Scrape tweets for all councilors"""
    print("\n[STEP 2] X Scraping")
    print("=" * 70)

    if not councilors:
        return {}

    results = {}
    try:
        # Initialize scraper WITH manual login
        scraper = XTwitterScraper(headless=False, require_login=True)

        if not scraper.logged_in:
            print("❌ Login failed or skipped\n")
            return {}

        usernames = [c["username"] for c in councilors]
        scraped = scraper.scrape_multiple(usernames, max_tweets=max_tweets, days_back=90)
        scraper.close()

        # Map back to full councilor data
        for councilor in councilors:
            username = councilor["username"]
            if username in scraped:
                results[username] = {
                    "tweets": scraped[username],
                    "metadata": councilor
                }

        return results

    except Exception as e:
        print(f"❌ Scraping Error: {e}\n")
        return {}


# ============================================================================
# DATABASE STORAGE
# ============================================================================

def store_to_database(scrape_results: dict) -> int:
    """Store scraped tweets to database"""
    print("\n[STEP 3] Database Storage")
    print("=" * 70)

    total_tweets = 0
    total_users = len(scrape_results)

    for username, data in scrape_results.items():
        tweets = data.get("tweets", [])
        metadata = data.get("metadata", {})

        # Save councilor
        save_councilor(
            username,
            metadata.get("name", "Unknown"),
            metadata.get("party", ""),
            metadata.get("district", "")
        )

        # Save tweets
        count = save_tweets_for_user(username, tweets)
        total_tweets += count
        print(f"✅ @{username:20s} → {count:3d} tweets saved")

    print(f"\n✅ Total: {total_tweets} tweets from {total_users} users\n")
    return total_tweets


# ============================================================================
# DISPLAY
# ============================================================================

def display_statistics():
    """Display statistics table"""
    print("\n[STEP 4] Statistics")
    print("=" * 70)

    df = get_all_data()

    if df.empty:
        print("❌ No data in database\n")
        return

    print("\n📊 ANKARA COUNCIL MEMBERS - TWEET STATISTICS\n")
    print(tabulate(df, headers="keys", tablefmt="grid", showindex=False))

    # Summary stats
    total_tweets = df['tweet_count'].sum()
    total_users = len(df)
    active_users = (df['tweet_count'] > 0).sum()

    print(f"\n📈 SUMMARY:")
    print(f"   Total users: {total_users}")
    print(f"   Active users: {active_users}")
    print(f"   Total tweets: {int(total_tweets)}")
    print(f"   Retweets: {int(df['retweet_count'].sum())}")
    print(f"   Original tweets: {int(df['original_count'].sum())}\n")


def display_user_tweets(username: str):
    """Display detailed tweets for a user"""
    print(f"\n[DETAIL] Tweets for @{username}")
    print("=" * 70)

    df = get_tweets_detail(username)

    if df.empty:
        print(f"❌ No tweets found for @{username}\n")
        return

    print(f"\n📝 LATEST TWEETS (@{username})\n")
    # Shorten text for display
    df['Tweet'] = df['Tweet'].str[:80] + '...'
    print(tabulate(df, headers="keys", tablefmt="grid", showindex=False))
    print()


# ============================================================================
# MAIN PIPELINE
# ============================================================================

def main():
    print("\n" + "=" * 70)
    print("🧪 TEST APP - Module 1: Scraping & Storage")
    print("=" * 70)

    print("\n⚠️  BEFORE YOU START:")
    print("   Lütfen X.com'da bir hesaba girmek için hazır ol")
    print("   Sistem aşağıdaki adımlarda login sayfası açacak:")
    print("   1. Tarayıcı otomatik açılacak")
    print("   2. X.com/login'e gidecek")
    print("   3. Sen email/username + password gireceksin")
    print("   4. System otomatik giriş kontrol edecek\n")

    input("   ✅ Hazırsan Enter'e bas...\n")

    # Step 1: Initialize database
    init_database()

    # Step 2: Parse CSV
    councilors = parse_csv(DATA_CSV)
    if not councilors:
        print("❌ No councilors found in CSV")
        return

    # Step 3: Scrape tweets
    results = scrape_tweets(councilors, max_tweets=50)
    if not results:
        print("⚠️  No tweets scraped")
        return

    # Step 4: Store to database
    store_to_database(results)

    # Step 5: Display
    display_statistics()

    # Step 6: Show sample user
    if results:
        first_user = list(results.keys())[0]
        display_user_tweets(first_user)

    print("=" * 70)
    print("✅ TEST COMPLETE")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()