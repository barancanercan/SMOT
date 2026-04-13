#!/usr/bin/env python3
"""
Batch Parallel Scraper — Twitter + Instagram koordinatörü
1 Ocak 2026'dan itibaren tüm verileri toplar.

Kullanim:
    python scrapers/batch_parallel.py               # Twitter + Instagram (sira ile)
    python scrapers/batch_parallel.py --twitter     # Sadece Twitter
    python scrapers/batch_parallel.py --instagram   # Sadece Instagram
    python scrapers/batch_parallel.py --parallel    # Her ikisi ayni anda (2 Brave gerekir)

Gereksinimler:
    Twitter  : Brave port 9222'de + x_session.json
    Instagram: Brave port 9226'da + ig_session.json
    Cookie kaydetmek icin: python scrapers/login_session.py
"""

import argparse
import logging
import multiprocessing
import os
import sys
import time
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
)
logger = logging.getLogger("BatchParallel")

START_DATE = datetime(2026, 1, 1)
DAYS_BACK = (datetime.now() - START_DATE).days + 1


# ──────────────────────────────────────────────────────────────
# Twitter worker
# ──────────────────────────────────────────────────────────────

def run_twitter():
    """Twitter batch scraper'i calistir (port 9222)."""
    import sqlite3
    import random
    import json
    from scrapers.cdp_browser import CDPBrowser
    from scrapers.twitter_scraper import TwitterCDPScraper, parse_metric

    log = logging.getLogger("BatchTwitter")
    DB_PATH = os.path.join(PROJECT_ROOT, "data", "sam.db")
    X_SESSION = os.path.join(PROJECT_ROOT, "x_session.json")
    MAX_TWEETS = 1000

    CDPBrowser._instance = None

    def get_users():
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute(
            "SELECT id, username, name FROM councilors "
            "WHERE username IS NOT NULL AND username != '' ORDER BY id"
        ).fetchall()
        conn.close()
        return [(r[0], r[1], r[2]) for r in rows]

    def save_tweets(tweets: list, username: str):
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
                    conn.execute(
                        "UPDATE tweets SET likes=?, replies=?, retweets=?, views=?, bookmarks=? WHERE id=?",
                        (t.get("likes", 0), t.get("replies", 0), t.get("retweets", 0),
                         t.get("views", 0), t.get("bookmarks", 0), existing[0])
                    )
                    updated += 1
                else:
                    conn.execute("""
                        INSERT INTO tweets (
                            username, tweet_id, tweet_url, tweet_text, tweet_date,
                            is_retweet, retweet_from, likes, replies, retweets, views, bookmarks,
                            media_type, media_urls, media_count, hashtags, mentions,
                            language, quote_tweet_id
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        username, tweet_id, t.get("tweet_url", ""),
                        t.get("text", ""), t.get("timestamp", ""),
                        1 if t.get("is_retweet") else 0, t.get("retweet_from"),
                        t.get("likes", 0), t.get("replies", 0), t.get("retweets", 0),
                        t.get("views", 0), t.get("bookmarks", 0),
                        t.get("media_type", "none"),
                        json.dumps(t.get("media_urls", []), ensure_ascii=False),
                        t.get("media_count", 0),
                        json.dumps(t.get("hashtags", []), ensure_ascii=False),
                        json.dumps(t.get("mentions", []), ensure_ascii=False),
                        t.get("language", "tr"), t.get("quote_tweet_id"),
                    ))
                    saved += 1
            conn.commit()
        finally:
            conn.close()
        return saved, updated

    def save_profile(username: str, profile: dict):
        if not profile:
            return
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        try:
            conn.execute("""
                UPDATE councilors
                SET bio=?, followers_count=?, following_count=?, tweet_count_total=?,
                    twitter_updated_at=CURRENT_TIMESTAMP
                WHERE username=?
            """, (
                profile.get("bio", "") or "",
                parse_metric(profile.get("followers", "0")),
                parse_metric(profile.get("following", "0")),
                parse_metric(profile.get("tweetCount", "0")),
                username,
            ))
            conn.commit()
        except Exception as e:
            log.warning(f"Profile save: {e}")
        finally:
            conn.close()

    users = get_users()
    log.info("=" * 60)
    log.info(f"TWITTER BATCH (port 9222)")
    log.info(f"Kullanici: {len(users)} | {START_DATE.date()} → bugun ({DAYS_BACK} gun)")
    log.info("=" * 60)

    scraper = TwitterCDPScraper(mock=False)
    if os.path.isfile(X_SESSION):
        scraper.browser.inject_cookies(X_SESSION, ".x.com")
        log.info("X session yuklendi")

    total_saved = total_updated = total_tweets = 0
    success = fail = skip = 0
    start_time = time.time()

    try:
        for i, (pid, username, name) in enumerate(users, 1):
            log.info(f"\n[{i}/{len(users)}] @{username} ({name})")
            try:
                profile = scraper.scrape_profile(username)
                if profile:
                    save_profile(username, profile)
                    log.info(f"  Profil: {profile.get('followers','?')} takipci")

                tweets = scraper.scrape_tweets(
                    username=username,
                    max_tweets=MAX_TWEETS,
                    days_back=DAYS_BACK,
                )
                if tweets:
                    saved, updated = save_tweets(tweets, username)
                    total_saved += saved
                    total_updated += updated
                    total_tweets += len(tweets)
                    success += 1
                    dates = f"{tweets[-1].get('timestamp','?')[:10]} → {tweets[0].get('timestamp','?')[:10]}"
                    log.info(f"  OK: {len(tweets)} tweet | {saved} yeni + {updated} guncellendi | {dates}")
                else:
                    skip += 1
                    log.warning("  SKIP: 0 tweet")

                if i < len(users):
                    time.sleep(random.uniform(3, 6))

            except KeyboardInterrupt:
                log.info("Durduruldu (Ctrl+C)")
                break
            except Exception as e:
                fail += 1
                log.error(f"  HATA: {e}")
                time.sleep(5)
    finally:
        scraper.close()

    elapsed = int(time.time() - start_time)
    log.info("\n" + "=" * 60)
    log.info("TWITTER TAMAMLANDI")
    log.info(f"  Sure    : {elapsed // 60}dk {elapsed % 60}sn")
    log.info(f"  Basarili: {success}/{len(users)} | Bos: {skip} | Hata: {fail}")
    log.info(f"  Toplam  : {total_tweets} tweet | {total_saved} yeni | {total_updated} guncellendi")
    log.info("=" * 60)

    return {"success": success, "fail": fail, "skip": skip,
            "total_tweets": total_tweets, "saved": total_saved, "updated": total_updated}


# ──────────────────────────────────────────────────────────────
# Instagram worker
# ──────────────────────────────────────────────────────────────

def run_instagram():
    """Instagram batch scraper'i calistir (port 9226)."""
    from scrapers.cdp_browser import CDPBrowser
    from scrapers.batch_instagram import (
        scrape_user_posts, save_post_to_db, save_ig_profile,
        get_all_instagram_users, IG_CDP_PORT
    )

    log = logging.getLogger("BatchInstagram")
    IG_SESSION = os.path.join(PROJECT_ROOT, "ig_session.json")
    MAX_POSTS = 500

    CDPBrowser._instance = None
    browser = CDPBrowser(chrome_port=IG_CDP_PORT)

    log.info("=" * 60)
    log.info(f"INSTAGRAM BATCH (port {IG_CDP_PORT})")
    log.info(f"Tarih: {START_DATE.date()} → bugun ({DAYS_BACK} gun)")
    log.info("=" * 60)

    try:
        browser.ensure_running()
    except Exception as e:
        log.error(f"Instagram browser baglantisi kurulamadi: {e}")
        log.error(f"Brave'i su port ile baslat: {IG_CDP_PORT}")
        return {"success": 0, "fail": 0, "skip": 0, "total_posts": 0}

    if os.path.isfile(IG_SESSION):
        browser.inject_cookies(IG_SESSION, ".instagram.com")
        log.info("Instagram session yuklendi")

    users = get_all_instagram_users()
    log.info(f"Instagram kullanici: {len(users)}")

    total_posts = total_saved = 0
    success = fail = skip = 0
    import random
    start_time = time.time()

    try:
        for i, (pid, ig_user, name) in enumerate(users, 1):
            log.info(f"\n[{i}/{len(users)}] @{ig_user} ({name})")
            try:
                posts, profile = scrape_user_posts(browser, ig_user, MAX_POSTS, DAYS_BACK)

                if profile:
                    save_ig_profile(ig_user, profile)

                if posts:
                    new_count = sum(1 for p in posts if save_post_to_db(p, ig_user))
                    total_posts += len(posts)
                    total_saved += new_count
                    success += 1
                    total_likes = sum(p.get("likes", 0) for p in posts)
                    log.info(f"  OK: {len(posts)} post ({new_count} yeni) | {total_likes:,} like")
                else:
                    skip += 1
                    log.warning("  SKIP: 0 post")

                if i < len(users):
                    time.sleep(random.uniform(3, 6))

            except KeyboardInterrupt:
                log.info("Durduruldu (Ctrl+C)")
                break
            except Exception as e:
                fail += 1
                log.error(f"  HATA: {e}")
                time.sleep(5)
    finally:
        try:
            browser.close()
        except Exception:
            pass

    elapsed = int(time.time() - start_time)
    log.info("\n" + "=" * 60)
    log.info("INSTAGRAM TAMAMLANDI")
    log.info(f"  Sure    : {elapsed // 60}dk {elapsed % 60}sn")
    log.info(f"  Basarili: {success}/{len(users)} | Bos: {skip} | Hata: {fail}")
    log.info(f"  Toplam  : {total_posts} post | {total_saved} yeni")
    log.info("=" * 60)

    return {"success": success, "fail": fail, "skip": skip,
            "total_posts": total_posts, "saved": total_saved}


# ──────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="S.A.M Batch Scraper — Twitter + Instagram",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ornekler:
  python scrapers/batch_parallel.py              # Her ikisi (sira ile)
  python scrapers/batch_parallel.py --twitter    # Sadece Twitter
  python scrapers/batch_parallel.py --instagram  # Sadece Instagram
  python scrapers/batch_parallel.py --parallel   # Ayni anda (2 Brave gerekir)
        """
    )
    parser.add_argument("--twitter",   action="store_true", help="Sadece Twitter")
    parser.add_argument("--instagram", action="store_true", help="Sadece Instagram")
    parser.add_argument("--parallel",  action="store_true",
                        help="Twitter + Instagram ayni anda calistir (2 ayri Brave gerekir)")
    args = parser.parse_args()

    do_twitter   = args.twitter   or (not args.twitter and not args.instagram)
    do_instagram = args.instagram or (not args.twitter and not args.instagram)

    logger.info("=" * 60)
    logger.info("S.A.M BATCH SCRAPER v2.0")
    logger.info(f"Tarih araligi: {START_DATE.date()} → bugun ({DAYS_BACK} gun)")
    logger.info(f"Mod: {'PARALEL' if args.parallel and do_twitter and do_instagram else 'SIRAYLA'}")
    logger.info("=" * 60)

    overall_start = time.time()
    results = {}

    if args.parallel and do_twitter and do_instagram:
        # Her iki scraper farkli process'te paralel calistir
        logger.info("Paralel mod: 2 ayri Brave penceresi gereklidir!")
        logger.info("  Twitter  → port 9222")
        logger.info("  Instagram → port 9226")

        with multiprocessing.Pool(processes=2) as pool:
            tw_result = pool.apply_async(run_twitter)
            ig_result = pool.apply_async(run_instagram)

            try:
                results["twitter"]   = tw_result.get(timeout=7200)
                results["instagram"] = ig_result.get(timeout=7200)
            except Exception as e:
                logger.error(f"Paralel worker hatasi: {e}")
    else:
        # Sirayla calistir
        if do_twitter:
            logger.info("\nTWITTER BASLANIYOR...")
            results["twitter"] = run_twitter()

        if do_instagram:
            logger.info("\nINSTAGRAM BASLANIYOR...")
            results["instagram"] = run_instagram()

    # Final ozet
    elapsed = int(time.time() - overall_start)
    logger.info("\n" + "=" * 60)
    logger.info("TUM ISLEMLER TAMAMLANDI")
    logger.info(f"Toplam sure: {elapsed // 60}dk {elapsed % 60}sn")
    if "twitter" in results:
        r = results["twitter"]
        logger.info(f"Twitter  : {r.get('success',0)} basarili | {r.get('total_tweets',0)} tweet | {r.get('saved',0)} yeni")
    if "instagram" in results:
        r = results["instagram"]
        logger.info(f"Instagram: {r.get('success',0)} basarili | {r.get('total_posts',0)} post | {r.get('saved',0)} yeni")
    logger.info("=" * 60)


if __name__ == "__main__":
    multiprocessing.set_start_method("spawn", force=True)
    main()
