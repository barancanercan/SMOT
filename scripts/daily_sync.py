#!/usr/bin/env python3
"""
MİS Daily Sync — Her gün 00:00'da son 24 saatlik veriyi çeker ve GitHub'a pushlar.
Twitter + Instagram günlük güncelleme + git push
"""

import sqlite3
import os
import sys
import time
import random
import logging
import json
import subprocess
from datetime import datetime, timedelta, timezone

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from scrapers.twitter_scraper import TwitterCDPScraper
from scrapers.cdp_browser import CDPBrowser
from scrapers.batch_instagram import scrape_user_posts

# --- Config ---
DB_PATH      = os.path.join(PROJECT_ROOT, "data", "meclis.db")
X_SESSION    = os.path.join(PROJECT_ROOT, "x_session.json")
IG_SESSION   = os.path.join(PROJECT_ROOT, "ig_session.json")
LOG_DIR      = os.path.join(PROJECT_ROOT, "data", "logs")
DAYS_BACK    = 2   # 2 günlük overlap — kaçırılan tweet'leri yakala
IG_CDP_PORT  = 9226
TW_CDP_PORT  = 9222

os.makedirs(LOG_DIR, exist_ok=True)

log_file = os.path.join(LOG_DIR, f"daily_sync_{datetime.now().strftime('%Y%m%d_%H%M')}.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger("DailySync")


def save_tweets(tweets: list, username: str) -> tuple:
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
            existing = conn.execute("SELECT id FROM tweets WHERE tweet_id=?", (tweet_id,)).fetchone()
            if existing:
                conn.execute("""UPDATE tweets SET likes=?,replies=?,retweets=?,views=?,bookmarks=? WHERE id=?""",
                    (t.get("likes",0), t.get("replies",0), t.get("retweets",0),
                     t.get("views",0), t.get("bookmarks",0), existing[0]))
                updated += 1
            else:
                conn.execute("""INSERT INTO tweets
                    (username,tweet_id,tweet_url,tweet_text,tweet_date,is_retweet,retweet_from,
                     likes,replies,retweets,views,bookmarks,media_type,media_urls,media_count,
                     hashtags,mentions,language,quote_tweet_id)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (username, tweet_id, t.get("tweet_url",""), t.get("text",""),
                     t.get("timestamp",""), 1 if t.get("is_retweet") else 0, t.get("retweet_from"),
                     t.get("likes",0), t.get("replies",0), t.get("retweets",0),
                     t.get("views",0), t.get("bookmarks",0), t.get("media_type","none"),
                     json.dumps(t.get("media_urls",[]),ensure_ascii=False), t.get("media_count",0),
                     json.dumps(t.get("hashtags",[]),ensure_ascii=False),
                     json.dumps(t.get("mentions",[]),ensure_ascii=False),
                     t.get("language","tr"), t.get("quote_tweet_id")))
                saved += 1
        conn.commit()
    finally:
        conn.close()
    return saved, updated


def save_ig_post(post: dict, ig_username: str) -> bool:
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        post_url = post.get("post_url","")
        existing = conn.execute("SELECT id FROM instagram_posts WHERE post_url=?", (post_url,)).fetchone()
        if existing:
            conn.execute("UPDATE instagram_posts SET likes=?,comments=?,video_views=? WHERE id=?",
                (post.get("likes",0), post.get("comments",0), post.get("video_views",0), existing[0]))
            conn.commit()
            return False
        else:
            conn.execute("""INSERT INTO instagram_posts
                (username,caption,post_date,post_url,likes,comments,is_video,video_views,
                 hashtags,mentions,post_type,shortcode,created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)""",
                (ig_username, post.get("caption",""), post.get("post_date",""), post_url,
                 post.get("likes",0), post.get("comments",0), 1 if post.get("is_video") else 0,
                 post.get("video_views",0), json.dumps(post.get("hashtags",[]),ensure_ascii=False),
                 json.dumps(post.get("mentions",[]),ensure_ascii=False),
                 post.get("post_type","photo"), post.get("shortcode","")))
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"DB error: {e}")
        return False
    finally:
        conn.close()


def sync_twitter():
    logger.info("=== TWITTER SYNC BAŞLIYOR ===")
    conn = sqlite3.connect(DB_PATH)
    users = conn.execute(
        "SELECT username, name FROM councilors WHERE username IS NOT NULL AND username != '' ORDER BY id"
    ).fetchall()
    conn.close()
    logger.info(f"{len(users)} kullanıcı")

    CDPBrowser._instance = None
    scraper = TwitterCDPScraper(mock=False)
    total_saved = total_updated = 0
    success = fail = skip = 0

    try:
        for i, (username, name) in enumerate(users, 1):
            logger.info(f"[{i}/{len(users)}] @{username} ({name})")
            try:
                tweets = scraper.scrape_tweets(username=username, max_tweets=200, days_back=DAYS_BACK)
                if tweets:
                    saved, updated = save_tweets(tweets, username)
                    total_saved += saved
                    total_updated += updated
                    success += 1
                    logger.info(f"  ✅ {len(tweets)} tweet | {saved} yeni + {updated} güncellendi")
                else:
                    skip += 1
                    logger.warning(f"  ⚠️ 0 tweet")
                if i < len(users):
                    time.sleep(random.uniform(2, 4))
            except KeyboardInterrupt:
                break
            except Exception as e:
                fail += 1
                logger.error(f"  ❌ {e}")
                time.sleep(5)
    finally:
        scraper.close()

    logger.info(f"Twitter bitti — {success} OK / {fail} fail / {skip} boş | {total_saved} yeni / {total_updated} güncellendi")
    return total_saved, total_updated


def sync_instagram():
    logger.info("=== INSTAGRAM SYNC BAŞLIYOR ===")
    conn = sqlite3.connect(DB_PATH)
    users = conn.execute(
        "SELECT instagram_username, name FROM councilors "
        "WHERE instagram_username IS NOT NULL AND instagram_username != '' ORDER BY id"
    ).fetchall()
    conn.close()
    logger.info(f"{len(users)} kullanıcı")

    CDPBrowser._instance = None
    browser = CDPBrowser(chrome_port=IG_CDP_PORT)
    try:
        browser.ensure_running()
    except Exception as e:
        logger.error(f"Instagram CDP bağlanamadı: {e}")
        return 0, 0

    if os.path.isfile(IG_SESSION):
        browser.inject_cookies(IG_SESSION, ".instagram.com")

    total_new = total_updated = 0
    success = fail = skip = 0

    try:
        for i, (ig_user, name) in enumerate(users, 1):
            logger.info(f"[{i}/{len(users)}] @{ig_user} ({name})")
            try:
                posts = scrape_user_posts(browser, ig_user, 50, DAYS_BACK)
                if posts:
                    new_count = sum(1 for p in posts if save_ig_post(p, ig_user))
                    total_new += new_count
                    total_updated += len(posts) - new_count
                    success += 1
                    logger.info(f"  ✅ {len(posts)} post | {new_count} yeni")
                else:
                    skip += 1
                    logger.info(f"  — 0 post (son {DAYS_BACK} günde paylaşım yok)")
                if i < len(users):
                    time.sleep(random.uniform(2, 4))
            except KeyboardInterrupt:
                break
            except Exception as e:
                fail += 1
                logger.error(f"  ❌ {e}")
                time.sleep(5)
    finally:
        browser.close()

    logger.info(f"Instagram bitti — {success} OK / {fail} fail / {skip} boş | {total_new} yeni")
    return total_new, total_updated


def git_push(new_tw, upd_tw, new_ig):
    logger.info("=== GIT PUSH ===")
    date_str = datetime.now().strftime("%Y-%m-%d")
    commit_msg = f"daily sync {date_str}: +{new_tw} tweet ({upd_tw} güncellendi), +{new_ig} ig post"

    cmds = [
        ["git", "-C", PROJECT_ROOT, "add", "data/meclis.db"],
        ["git", "-C", PROJECT_ROOT, "commit", "-m", commit_msg],
        ["git", "-C", PROJECT_ROOT, "push"],
    ]
    for cmd in cmds:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.warning(f"  {' '.join(cmd[2:])}: {result.stderr.strip()}")
        else:
            logger.info(f"  ✅ {' '.join(cmd[2:])}")


def main():
    start = datetime.now()
    logger.info(f"{'='*60}")
    logger.info(f"MİS DAILY SYNC — {start.strftime('%Y-%m-%d %H:%M')}")
    logger.info(f"Son {DAYS_BACK} gün verisi güncelleniyor")
    logger.info(f"{'='*60}")

    new_tw, upd_tw = sync_twitter()
    new_ig, _ = sync_instagram()
    git_push(new_tw, upd_tw, new_ig)

    elapsed = (datetime.now() - start).seconds // 60
    logger.info(f"{'='*60}")
    logger.info(f"TAMAMLANDI — {elapsed} dakika")
    logger.info(f"Twitter: +{new_tw} yeni, {upd_tw} güncellendi")
    logger.info(f"Instagram: +{new_ig} yeni")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    main()
