#!/usr/bin/env python3
"""
Batch Twitter Scraper — Tüm meclis üyelerinin tweet'lerini çeker.
1 Ocak 2026'dan itibaren tüm verileri toplar.
"""

import sqlite3
import os
import sys
import time
import random
import logging
import json
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from scrapers.twitter_scraper import TwitterCDPScraper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
)
logger = logging.getLogger("BatchTwitter")

DB_PATH = os.path.join(PROJECT_ROOT, "data", "smot.db")
X_SESSION = os.path.join(PROJECT_ROOT, "x_session.json")

START_DATE = datetime(2026, 1, 1)
DAYS_BACK = (datetime.now() - START_DATE).days + 1
MAX_TWEETS_PER_USER = 1000


def save_tweets(tweets: list, username: str) -> tuple:
    """Tweet'leri kaydet. (saved, updated) döndür."""
    if not tweets:
        return 0, 0

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")

    saved = updated = 0
    try:
        for t in tweets:
            tweet_id = t.get("tweet_id")
            if not tweet_id:
                continue

            existing = conn.execute(
                "SELECT id FROM tweets WHERE tweet_id = ?", (tweet_id,)
            ).fetchone()

            if existing:
                conn.execute("""
                    UPDATE tweets
                    SET likes=?, replies=?, retweets=?, views=?, bookmarks=?
                    WHERE id=?
                """, (
                    t.get("likes", 0), t.get("replies", 0),
                    t.get("retweets", 0), t.get("views", 0),
                    t.get("bookmarks", 0), existing[0]
                ))
                updated += 1
            else:
                conn.execute("""
                    INSERT INTO tweets (
                        username, tweet_id, tweet_url,
                        tweet_text, tweet_date,
                        is_retweet, retweet_from,
                        likes, replies, retweets, views, bookmarks,
                        media_type, media_urls, media_count,
                        hashtags, mentions,
                        language, quote_tweet_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    username,
                    tweet_id,
                    t.get("tweet_url", ""),
                    t.get("text", ""),
                    t.get("timestamp", ""),
                    1 if t.get("is_retweet") else 0,
                    t.get("retweet_from"),
                    t.get("likes", 0),
                    t.get("replies", 0),
                    t.get("retweets", 0),
                    t.get("views", 0),
                    t.get("bookmarks", 0),
                    t.get("media_type", "none"),
                    json.dumps(t.get("media_urls", []), ensure_ascii=False),
                    t.get("media_count", 0),
                    json.dumps(t.get("hashtags", []), ensure_ascii=False),
                    json.dumps(t.get("mentions", []), ensure_ascii=False),
                    t.get("language", "tr"),
                    t.get("quote_tweet_id"),
                ))
                saved += 1

        conn.commit()
    finally:
        conn.close()

    return saved, updated


def get_all_users() -> list:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT id, username, name FROM councilors "
        "WHERE username IS NOT NULL AND username != '' ORDER BY id"
    ).fetchall()
    conn.close()
    return [(r[0], r[1], r[2]) for r in rows]


def main():
    users = get_all_users()
    logger.info(f"{'='*60}")
    logger.info(f"BATCH TWITTER SCRAPER")
    logger.info(f"Profil: {len(users)} | Tarih: {START_DATE.date()} → bugün ({DAYS_BACK} gün)")
    logger.info(f"{'='*60}")

    scraper = TwitterCDPScraper(mock=False)
    total_saved = total_updated = total_tweets = 0
    success = fail = skip = 0

    try:
        for i, (pid, username, name) in enumerate(users, 1):
            logger.info(f"\n[{i}/{len(users)}] @{username} ({name})")
            try:
                tweets = scraper.scrape_tweets(
                    username=username,
                    max_tweets=MAX_TWEETS_PER_USER,
                    days_back=DAYS_BACK,
                )
                if tweets:
                    saved, updated = save_tweets(tweets, username)
                    total_saved += saved
                    total_updated += updated
                    total_tweets += len(tweets)
                    success += 1
                    logger.info(
                        f"  ✅ {len(tweets)} tweet | {saved} yeni + {updated} güncellendi"
                        f" | {tweets[-1].get('timestamp','?')[:10]} → {tweets[0].get('timestamp','?')[:10]}"
                    )
                else:
                    skip += 1
                    logger.warning(f"  ⚠️ 0 tweet (profil yok veya boş)")

                if i < len(users):
                    time.sleep(random.uniform(3, 6))

            except KeyboardInterrupt:
                logger.info("\nDurduruldu (Ctrl+C)")
                break
            except Exception as e:
                fail += 1
                logger.error(f"  ❌ HATA: {e}")
                time.sleep(5)
    finally:
        scraper.close()

    logger.info(f"\n{'='*60}")
    logger.info(f"TAMAMLANDI")
    logger.info(f"  Başarılı: {success}/{len(users)} | Boş: {skip} | Hata: {fail}")
    logger.info(f"  Toplam: {total_tweets} tweet | {total_saved} yeni | {total_updated} güncellendi")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    main()
