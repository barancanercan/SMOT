#!/usr/bin/env python3
"""
🐦 Scraper Worker v3.3 - Aggressive Collection
✅ max_tweets: 500 (increased from 100)
✅ Time-based aggressive scraping
"""

import csv
import sqlite3
from x_scraper import XTwitterScraper

DB_PATH = "meclis.db"
CSV_PATH = "data/data.csv"


def load_councilors():
    """Load councilors from CSV"""
    councilors = []
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            link = row.get("link", "")
            if "x.com/" in link:
                username = link.split("x.com/")[-1].strip("/").replace("@", "")
                councilors.append({
                    "username": username,
                    "name": row.get("Meclis Üyesi", ""),
                    "party": row.get("Parti", ""),
                    "district": row.get("İlçe", "")
                })
    return councilors


def save_councilors(councilors):
    """Save councilors to database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for c in councilors:
        cursor.execute("""
            INSERT OR REPLACE INTO councilors (username, name, party, district)
            VALUES (?, ?, ?, ?)
        """, (c["username"], c["name"], c["party"], c["district"]))

    conn.commit()
    conn.close()


def save_tweets(username: str, tweets: list):
    """Save tweets to database with views support"""
    if not tweets:
        print("⚠️  No tweets")
        return 0, 0

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    saved_count = 0
    duplicate_count = 0

    for tweet in tweets:
        # Check for duplicate
        cursor.execute("""
            SELECT id FROM tweets 
            WHERE username = ? AND tweet_text = ?
        """, (username, tweet.get("text", "")))

        if cursor.fetchone():
            duplicate_count += 1
            continue

        # Insert with views
        try:
            cursor.execute("""
                INSERT INTO tweets 
                (username, tweet_text, tweet_date, is_retweet, retweet_from,
                 likes, replies, retweets, views)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                username,
                tweet.get("text", "")[:500],
                tweet.get("timestamp"),
                tweet.get("is_retweet", False),
                tweet.get("retweet_from"),
                tweet.get("likes", 0),
                tweet.get("replies", 0),
                tweet.get("retweets", 0),
                tweet.get("views", 0),
            ))
            saved_count += 1
        except Exception as e:
            print(f"  ⚠️  Insert error: {e}")

    conn.commit()
    conn.close()

    print(f"✅ {saved_count} saved", end="")
    if duplicate_count > 0:
        print(f", {duplicate_count} dup", end="")
    print()

    return saved_count, duplicate_count


def get_stats():
    """Get database statistics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    stats = {}

    cursor.execute("SELECT COUNT(*) FROM councilors")
    stats["total_councilors"] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tweets")
    stats["total_tweets"] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tweets WHERE is_retweet = 1")
    stats["total_retweets"] = cursor.fetchone()[0]

    stats["total_original"] = stats["total_tweets"] - stats["total_retweets"]

    cursor.execute("SELECT COUNT(DISTINCT username) FROM tweets")
    stats["active_users"] = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(views), 0) FROM tweets")
    stats["total_views"] = cursor.fetchone()[0]

    conn.close()
    return stats


def main():
    """Main scraper workflow"""
    print("\n" + "=" * 70)
    print("🐦 SCRAPER WORKER v3.3 - Aggressive Collection")
    print("=" * 70 + "\n")

    # Load councilors
    councilors = load_councilors()
    print(f"✅ Loaded {len(councilors)} councilors")

    save_councilors(councilors)
    print(f"✅ {len(councilors)} councilors saved to DB\n")

    usernames = [c["username"] for c in councilors]

    # Scrape tweets with HIGHER limit
    scraper = XTwitterScraper(headless=False, require_manual_login=True)

    if not scraper.driver:
        print("❌ Scraper failed to initialize")
        return

    print("=" * 70)
    print(f"🐦 SCRAPER WORKER v3.3 - {len(usernames)} users")
    print(f"   Max tweets/user: 500 (INCREASED)")
    print(f"   Time window: 90 days")
    print(f"   Strategy: AGGRESSIVE TIME-BASED")
    print("=" * 70 + "\n")

    total_scraped = 0
    total_saved = 0
    total_duplicates = 0
    user_stats = []

    for i, username in enumerate(usernames, 1):
        print(f"[{i:2d}/{len(usernames)}] @{username:20s}", end=" ")

        # INCREASED: 100 → 500 max tweets
        tweets = scraper.scrape_tweets(username, max_tweets=500, days_back=90)

        if tweets:
            total_scraped += len(tweets)
            saved, dup = save_tweets(username, tweets)
            total_saved += saved
            total_duplicates += dup

            user_stats.append({
                "username": username,
                "scraped": len(tweets),
                "saved": saved,
                "duplicates": dup
            })
        else:
            user_stats.append({
                "username": username,
                "status": "no_tweets"
            })

    scraper.close()

    # Summary
    print("\n" + "=" * 70)
    print("📊 SCRAPING SUMMARY")
    print("=" * 70 + "\n")

    print(f"📈 Totals:")
    print(f"   Scraped: {total_scraped}")
    print(f"   Saved: {total_saved}")
    print(f"   Duplicates: {total_duplicates}\n")

    print(f"👤 By User:")
    for stat in user_stats:
        if "status" in stat:
            print(f"   ⚠️  @{stat['username']:20s} → {stat['status']}")
        else:
            print(f"   ✅ @{stat['username']:20s} → {stat['saved']} saved, {stat['duplicates']} dup")

    # Database stats
    db_stats = get_stats()
    print(f"\n💾 Database Stats:")
    print(f"   Total Councilors: {db_stats['total_councilors']}")
    print(f"   Total Tweets: {db_stats['total_tweets']}")
    print(f"   Retweets: {db_stats['total_retweets']}")
    print(f"   Original: {db_stats['total_original']}")
    print(f"   Active Users: {db_stats['active_users']}")
    print(f"   Total Views: {db_stats['total_views']:,}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()