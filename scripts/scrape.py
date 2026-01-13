#!/usr/bin/env python3
"""
Tum kullanicilar icin 3 aylik tweet toplama
Arkaplanda calistirilabilir

Kullanim:
  python run_full_scrape.py              # Bastan basla
  python run_full_scrape.py --start 31   # 31. kullanicidan devam et
  python run_full_scrape.py --resume     # Basarisiz olanlari tekrar dene
"""

import os
import sys
import argparse
import sqlite3
from datetime import datetime

# Add src to python path for standalone execution
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from meclis_istihbarat.core.config import DB_PATH
from meclis_istihbarat.core.database import save_tweets_batch, init_database
from meclis_istihbarat.scrapers.x_scraper import XTwitterScraper
from meclis_istihbarat.utils.logger import get_logger

logger = get_logger("FullScrape")


def get_all_usernames():
    """Veritabanindan tum kullanicilari al"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM councilors ORDER BY username")
    usernames = [row[0] for row in cursor.fetchall()]
    conn.close()
    return usernames


def get_failed_usernames():
    """Son 24 saatte tweet'i olmayan kullanicilari bul (muhtemelen basarisiz)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Hic tweet'i olmayan veya son 24 saatte scrape edilmemis kullanicilar
    cursor.execute("""
        SELECT c.username FROM councilors c
        LEFT JOIN (
            SELECT username, MAX(created_at) as last_scrape
            FROM tweets
            GROUP BY username
        ) t ON LOWER(c.username) = LOWER(t.username)
        WHERE t.last_scrape IS NULL
           OR t.last_scrape < datetime('now', '-1 day')
        ORDER BY c.username
    """)
    usernames = [row[0] for row in cursor.fetchall()]
    conn.close()
    return usernames


def main():
    parser = argparse.ArgumentParser(description='Tweet scraper')
    parser.add_argument('--start', type=int, default=1,
                        help='Kacinci kullanicidan baslayacak (1-based index)')
    parser.add_argument('--resume', action='store_true',
                        help='Sadece basarisiz/eksik kullanicilari scrape et')
    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info(f"FULL SCRAPE - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    logger.info("=" * 70)

    # Init database
    init_database()

    # Get usernames based on mode
    if args.resume:
        usernames = get_failed_usernames()
        logger.info(f"Eksik/basarisiz kullanici: {len(usernames)}")
    else:
        usernames = get_all_usernames()
        # Apply start offset
        if args.start > 1:
            usernames = usernames[args.start - 1:]
            logger.info(f"Toplam kullanici: {len(usernames)} ({args.start}. kullanicidan devam)")
        else:
            logger.info(f"Toplam kullanici: {len(usernames)}")

    if not usernames:
        logger.error("Kullanici bulunamadi!")
        return

    # Initialize scraper (will wait for manual login)
    logger.info("Scraper baslatiliyor...")
    scraper = XTwitterScraper(headless=False, require_manual_login=True)

    if not scraper.driver:
        logger.error("Scraper baslatilamadi!")
        return

    if not scraper.logged_in:
        logger.error("Login yapilamadi!")
        scraper.close()
        return

    # Scrape all users
    total_usernames = len(usernames)
    start_index = args.start if not args.resume else 1
    logger.info(f"{total_usernames} kullanici icin tweet toplanacak (3 ay)")
    logger.info("=" * 70)

    total_tweets = 0
    successful_users = 0
    consecutive_errors = 0
    MAX_CONSECUTIVE_ERRORS = 3

    try:
        for i, username in enumerate(usernames, start_index):
            logger.info(f"[{i}/{start_index + total_usernames - 1}] Processing @{username}")

            try:
                tweets = scraper.scrape_tweets(username, max_tweets=500, days_back=90)
                consecutive_errors = 0  # Reset on success

                if tweets:
                    # Save to database
                    saved, duplicates = save_tweets_batch(tweets, username)
                    total_tweets += saved
                    successful_users += 1
                    if duplicates > 0:
                        logger.info(f"Saved {saved} new, {duplicates} duplicates")
                    else:
                        logger.info(f"Saved {saved} tweets")
            except Exception as e:
                error_msg = str(e)
                if "invalid session id" in error_msg or "session" in error_msg.lower():
                    consecutive_errors += 1
                    logger.warning(f"Session error ({consecutive_errors}/{MAX_CONSECUTIVE_ERRORS})")

                    if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                        logger.warning("Browser session crashed, restarting...")
                        try:
                            scraper.close()
                        except Exception:
                            pass
                        scraper = XTwitterScraper(headless=False, require_manual_login=True)
                        if not scraper.driver or not scraper.logged_in:
                            logger.error("Browser restart failed!")
                            break
                        consecutive_errors = 0
                        logger.info("Browser restarted, continuing...")
                        # Retry current user
                        try:
                            tweets = scraper.scrape_tweets(username, max_tweets=500, days_back=90)
                            if tweets:
                                saved, duplicates = save_tweets_batch(tweets, username)
                                total_tweets += saved
                                successful_users += 1
                                logger.info(f"Saved {saved} new, {duplicates} duplicates")
                        except Exception as retry_e:
                            logger.error(f"Retry failed: {retry_e}")
                else:
                    logger.error(f"Error: {error_msg[:50]}")

    except KeyboardInterrupt:
        logger.warning("Stopped by user")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        try:
            scraper.close()
        except Exception:
            pass

    # Summary
    logger.info("=" * 70)
    logger.info("RESULTS")
    logger.info("=" * 70)
    logger.info(f"Successful users: {successful_users}/{len(usernames)}")
    logger.info(f"Total tweets: {total_tweets}")
    logger.info(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
