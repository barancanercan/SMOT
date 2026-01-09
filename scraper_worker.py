#!/usr/bin/env python3
"""
Scraper Worker v3.3 - Aggressive Collection
"""

import csv
from config import DB_PATH, CSV_PATH, MAX_TWEETS_PER_USER, DAYS_BACK
from database import init_database, save_tweets_batch, get_stats
from x_scraper import XTwitterScraper
import sqlite3


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


def main():
    """Main scraper workflow"""
    print("\n" + "=" * 70)
    print("SCRAPER WORKER v3.3 - Aggressive Collection")
    print("=" * 70 + "\n")

    # Initialize database
    init_database()

    # Load councilors
    councilors = load_councilors()
    print(f"Loaded {len(councilors)} councilors")

    save_councilors(councilors)
    print(f"{len(councilors)} councilors saved to DB\n")

    usernames = [c["username"] for c in councilors]

    # Scrape tweets
    scraper = XTwitterScraper(headless=False, require_manual_login=True)

    if not scraper.driver:
        print("Scraper failed to initialize")
        return

    print("=" * 70)
    print(f"SCRAPING - {len(usernames)} users")
    print(f"   Max tweets/user: {MAX_TWEETS_PER_USER}")
    print(f"   Time window: {DAYS_BACK} days")
    print("=" * 70 + "\n")

    total_scraped = 0
    total_saved = 0
    total_duplicates = 0
    user_stats = []

    for i, username in enumerate(usernames, 1):
        print(f"[{i:2d}/{len(usernames)}] @{username:20s}", end=" ")

        tweets = scraper.scrape_tweets(username, max_tweets=MAX_TWEETS_PER_USER, days_back=DAYS_BACK)

        if tweets:
            total_scraped += len(tweets)
            saved, dup = save_tweets_batch(tweets, username)
            total_saved += saved
            total_duplicates += dup

            print(f"-> {saved} saved, {dup} dup")

            user_stats.append({
                "username": username,
                "scraped": len(tweets),
                "saved": saved,
                "duplicates": dup
            })
        else:
            print("-> no tweets")
            user_stats.append({
                "username": username,
                "status": "no_tweets"
            })

    scraper.close()

    # Summary
    print("\n" + "=" * 70)
    print("SCRAPING SUMMARY")
    print("=" * 70 + "\n")

    print(f"Totals:")
    print(f"   Scraped: {total_scraped}")
    print(f"   Saved: {total_saved}")
    print(f"   Duplicates: {total_duplicates}\n")

    # Database stats
    db_stats = get_stats()
    print(f"Database Stats:")
    print(f"   Total Councilors: {db_stats['total_councilors']}")
    print(f"   Total Tweets: {db_stats['total_tweets']}")
    print(f"   Retweets: {db_stats['total_retweets']}")
    print(f"   Original: {db_stats['total_original']}")
    print(f"   Active Users: {db_stats['active_users']}")
    print(f"   Total Views: {db_stats['total_views']:,}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()