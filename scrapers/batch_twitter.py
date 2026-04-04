#!/usr/bin/env python3
"""
Batch Twitter Scraper - Tum meclis uyelerinin tweet'lerini ceker.
1 Ocak 2026'dan itibaren tum verileri toplar.

Kullanim:
    python -m scrapers.batch_twitter
"""

import sqlite3
import os
import sys
import time
import random
import logging
from datetime import datetime

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from scrapers.twitter_scraper import TwitterCDPScraper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
)
logger = logging.getLogger("BatchTwitter")

DB_PATH = os.path.join(PROJECT_ROOT, "data", "meclis.db")

# 1 Ocak 2026'dan bugun = kac gun
START_DATE = datetime(2026, 1, 1)
DAYS_BACK = (datetime.now() - START_DATE).days + 1
MAX_TWEETS_PER_USER = 1000


def save_tweets_to_meclis_db(tweets: list, username: str) -> int:
    """Tweet'leri meclis.db'nin mevcut tweets tablosuna kaydet"""
    if not tweets:
        return 0

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=OFF")

        saved = 0
        for t in tweets:
            tweet_id = t.get("tweet_id")
            if not tweet_id:
                continue

            # Dedup by tweet_id
            existing = conn.execute(
                "SELECT id FROM tweets WHERE tweet_id = ?", (tweet_id,)
            ).fetchone()

            if existing:
                # Update engagement
                conn.execute("""
                    UPDATE tweets SET likes=?, replies=?, retweets=?, views=?
                    WHERE id=?
                """, (
                    t.get("likes", 0), t.get("replies", 0),
                    t.get("retweets", 0), t.get("views", 0), existing[0]
                ))
            else:
                conn.execute("""
                    INSERT INTO tweets
                    (username, tweet_text, tweet_date, is_retweet, retweet_from,
                     likes, replies, retweets, views, tweet_id, tweet_url,
                     quotes, bookmarks, media_type, language, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    username,
                    t.get("text", ""),
                    t.get("timestamp", ""),
                    1 if t.get("is_retweet") else 0,
                    t.get("retweet_from"),
                    t.get("likes", 0),
                    t.get("replies", 0),
                    t.get("retweets", 0),
                    t.get("views", 0),
                    tweet_id,
                    t.get("tweet_url", ""),
                    0,  # quotes
                    0,  # bookmarks
                    t.get("media_type", "none"),
                    t.get("language", "tr"),
                ))
                saved += 1

        conn.commit()
        return saved
    finally:
        conn.close()


def get_all_twitter_users() -> list:
    """DB'den tum Twitter kullanicilarini cek"""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT id, username, name FROM councilors "
        "WHERE username IS NOT NULL AND username != '' ORDER BY id"
    ).fetchall()
    conn.close()
    return [(r[0], r[1], r[2]) for r in rows]


def main():
    users = get_all_twitter_users()
    logger.info(f"{'='*60}")
    logger.info(f"BATCH TWITTER SCRAPER")
    logger.info(f"Profil sayisi: {len(users)}")
    logger.info(f"Tarih araligi: {START_DATE.strftime('%Y-%m-%d')} -> bugun ({DAYS_BACK} gun)")
    logger.info(f"Max tweet/kullanici: {MAX_TWEETS_PER_USER}")
    logger.info(f"{'='*60}")

    scraper = TwitterCDPScraper(mock=False)
    total_tweets = 0
    success_count = 0
    fail_count = 0
    skip_count = 0

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
                    saved = save_tweets_to_meclis_db(tweets, username=username)
                    total_tweets += len(tweets)
                    success_count += 1
                    logger.info(
                        f"  OK: {len(tweets)} tweet ({saved} yeni) | "
                        f"{tweets[-1].get('timestamp', '?')[:10]} -> {tweets[0].get('timestamp', '?')[:10]}"
                    )
                else:
                    skip_count += 1
                    logger.warning(f"  SKIP: 0 tweet (profil bulunamadi veya bos)")

                # Kullanicilar arasi bekleme (bot detection onleme)
                if i < len(users):
                    delay = random.uniform(3, 6)
                    time.sleep(delay)

            except KeyboardInterrupt:
                logger.info("\nKullanici tarafindan durduruldu (Ctrl+C)")
                break
            except Exception as e:
                fail_count += 1
                logger.error(f"  HATA: {str(e)[:80]}")
                time.sleep(5)  # Hata sonrasi ekstra bekleme

    finally:
        scraper.close()

    # Ozet
    logger.info(f"\n{'='*60}")
    logger.info(f"BATCH TAMAMLANDI")
    logger.info(f"  Basarili: {success_count}/{len(users)}")
    logger.info(f"  Bos/Skip: {skip_count}")
    logger.info(f"  Hata: {fail_count}")
    logger.info(f"  Toplam tweet: {total_tweets:,}")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    main()
