#!/usr/bin/env python3
"""
Parallel Twitter Scraper — 3 worker, her biri ayrı Chrome portunda.
Tamamlanmış kullanıcıları atlar (DB'de tweet'i olanlar).
"""

import sqlite3
import os
import sys
import time
import random
import logging
import json
import multiprocessing
from datetime import datetime
from typing import List, Tuple

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [W%(process)d] %(levelname)s: %(message)s"
)
logger = logging.getLogger("BatchParallel")

DB_PATH = os.path.join(PROJECT_ROOT, "data", "meclis.db")
X_SESSION = os.path.join(PROJECT_ROOT, "x_session.json")

START_DATE = datetime(2026, 1, 1)
DAYS_BACK = (datetime.now() - START_DATE).days + 1
MAX_TWEETS_PER_USER = 1000

# Chrome ports per worker
CHROME_PORTS = [9223, 9224, 9225]
N_WORKERS = len(CHROME_PORTS)


def save_tweets(tweets: list, username: str) -> Tuple[int, int]:
    if not tweets:
        return 0, 0

    conn = sqlite3.connect(DB_PATH, timeout=30)
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


def get_remaining_users() -> List[Tuple]:
    conn = sqlite3.connect(DB_PATH)
    done = {r[0] for r in conn.execute("SELECT DISTINCT username FROM tweets").fetchall()}
    all_users = conn.execute(
        "SELECT id, username, name FROM councilors "
        "WHERE username IS NOT NULL AND username != '' ORDER BY id"
    ).fetchall()
    conn.close()
    return [r for r in all_users if r[1] not in done]


def worker_fn(worker_id: int, chrome_port: int, user_list: List[Tuple]):
    """Her worker kendi Chrome portunda çalışır."""
    log = logging.getLogger(f"Worker-{worker_id}")

    # CDPBrowser singleton reset per process (multiprocessing fork)
    from scrapers.cdp_browser import CDPBrowser
    CDPBrowser._instance = None

    from scrapers.twitter_scraper import TwitterCDPScraper

    log.info(f"Worker {worker_id} başlıyor — port {chrome_port}, {len(user_list)} kullanıcı")

    # Patch CDPBrowser to use our port
    scraper = TwitterCDPScraper.__new__(TwitterCDPScraper)
    scraper.mock = False
    scraper._cookies_injected = False
    CDPBrowser._instance = None
    scraper.browser = CDPBrowser(chrome_port=chrome_port)

    total_saved = total_updated = 0
    success = fail = skip = 0
    n = len(user_list)

    try:
        for i, (pid, username, name) in enumerate(user_list, 1):
            log.info(f"[{i}/{n}] @{username} ({name})")
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
                    success += 1
                    log.info(f"  ✅ {len(tweets)} tweet | {saved} yeni + {updated} güncellendi")
                else:
                    skip += 1
                    log.warning(f"  ⚠️ 0 tweet")

                if i < n:
                    time.sleep(random.uniform(3, 6))

            except KeyboardInterrupt:
                break
            except Exception as e:
                fail += 1
                log.error(f"  ❌ HATA: {e}")
                time.sleep(5)
    finally:
        try:
            scraper.close()
        except Exception:
            pass

    log.info(f"Worker {worker_id} bitti — {success} OK / {fail} fail / {skip} boş | {total_saved} yeni tweet")


def split_list(lst, n):
    """Listeyi n parçaya böl (round-robin distribution)."""
    buckets = [[] for _ in range(n)]
    for i, item in enumerate(lst):
        buckets[i % n].append(item)
    return buckets


def main():
    remaining = get_remaining_users()
    if not remaining:
        logger.info("Tüm kullanıcılar zaten scraped!")
        return

    logger.info(f"Kalan: {len(remaining)} kullanıcı → {N_WORKERS} worker'a dağıtılıyor")

    chunks = split_list(remaining, N_WORKERS)
    for i, chunk in enumerate(chunks):
        logger.info(f"  Worker {i}: {len(chunk)} kullanıcı")

    # Stagger worker starts slightly to avoid Chrome conflicts
    processes = []
    for i, (port, chunk) in enumerate(zip(CHROME_PORTS, chunks)):
        if not chunk:
            continue
        p = multiprocessing.Process(
            target=worker_fn,
            args=(i, port, chunk),
            name=f"Worker-{i}"
        )
        p.start()
        processes.append(p)
        logger.info(f"Worker {i} başlatıldı (PID {p.pid}, port {port})")
        time.sleep(8)  # Chrome başlangıç süresi için bekle

    logger.info("Tüm worker'lar çalışıyor, bitmesini bekliyorum...")
    for p in processes:
        p.join()

    logger.info("="*60)
    logger.info("TÜM WORKER'LAR TAMAMLANDI")
    logger.info("="*60)


if __name__ == "__main__":
    multiprocessing.set_start_method("spawn", force=True)
    main()
