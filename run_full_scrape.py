#!/usr/bin/env python3
"""
Tum kullanicilar icin 3 aylik tweet toplama
Arkaplanda calistirilabilir

Kullanim:
  python run_full_scrape.py              # Bastan basla
  python run_full_scrape.py --start 31   # 31. kullanicidan devam et
  python run_full_scrape.py --resume     # Basarisiz olanlari tekrar dene
"""

import argparse
import sqlite3
import sys
from datetime import datetime

from config import DB_PATH
from database import save_tweets_batch, init_database
from x_scraper import XTwitterScraper


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

    print("=" * 70)
    print(f"🚀 FULL SCRAPE - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 70)

    # Init database
    init_database()

    # Get usernames based on mode
    if args.resume:
        usernames = get_failed_usernames()
        print(f"\n📋 Eksik/basarisiz kullanici: {len(usernames)}")
    else:
        usernames = get_all_usernames()
        # Apply start offset
        if args.start > 1:
            usernames = usernames[args.start - 1:]
            print(f"\n📋 Toplam kullanici: {len(usernames)} ({args.start}. kullanicidan devam)")
        else:
            print(f"\n📋 Toplam kullanici: {len(usernames)}")

    if not usernames:
        print("❌ Kullanici bulunamadi!")
        return

    # Initialize scraper (will wait for manual login)
    print("\n🔐 Scraper baslatiliyor...")
    scraper = XTwitterScraper(headless=False, require_manual_login=True)

    if not scraper.driver:
        print("❌ Scraper baslatilamadi!")
        return

    if not scraper.logged_in:
        print("❌ Login yapilamadi!")
        scraper.close()
        return

    # Scrape all users
    total_usernames = len(usernames)
    start_index = args.start if not args.resume else 1
    print(f"\n🐦 {total_usernames} kullanici icin tweet toplanacak (3 ay)")
    print("=" * 70)

    total_tweets = 0
    successful_users = 0
    consecutive_errors = 0
    MAX_CONSECUTIVE_ERRORS = 3

    try:
        for i, username in enumerate(usernames, start_index):
            print(f"\n[{i:2d}/{start_index + total_usernames - 1}] ", end="")

            try:
                tweets = scraper.scrape_tweets(username, max_tweets=500, days_back=90)
                consecutive_errors = 0  # Reset on success

                if tweets:
                    # Save to database
                    saved, duplicates = save_tweets_batch(tweets, username)
                    total_tweets += saved
                    successful_users += 1
                    if duplicates > 0:
                        print(f"         💾 {saved} yeni, {duplicates} tekrar")
                    else:
                        print(f"         💾 {saved} tweet kaydedildi")
            except Exception as e:
                error_msg = str(e)
                if "invalid session id" in error_msg or "session" in error_msg.lower():
                    consecutive_errors += 1
                    print(f"         ⚠️  Session hatasi ({consecutive_errors}/{MAX_CONSECUTIVE_ERRORS})")

                    if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                        print("\n\n🔄 Browser session çöktü, yeniden başlatılıyor...")
                        try:
                            scraper.close()
                        except:
                            pass
                        scraper = XTwitterScraper(headless=False, require_manual_login=True)
                        if not scraper.driver or not scraper.logged_in:
                            print("❌ Browser yeniden başlatılamadı!")
                            break
                        consecutive_errors = 0
                        print("✅ Browser yeniden başlatıldı, devam ediliyor...")
                        # Retry current user
                        try:
                            tweets = scraper.scrape_tweets(username, max_tweets=500, days_back=90)
                            if tweets:
                                saved, duplicates = save_tweets_batch(tweets, username)
                                total_tweets += saved
                                successful_users += 1
                                print(f"         💾 {saved} yeni, {duplicates} tekrar")
                        except Exception as retry_e:
                            print(f"         ❌ Retry failed: {retry_e}")
                else:
                    print(f"         ❌ Error: {error_msg[:50]}")

    except KeyboardInterrupt:
        print("\n\n⚠️  Kullanici tarafindan durduruldu")
    except Exception as e:
        print(f"\n❌ Hata: {e}")
    finally:
        try:
            scraper.close()
        except:
            pass

    # Summary
    print("\n" + "=" * 70)
    print("📊 SONUC")
    print("=" * 70)
    print(f"   Basarili kullanici: {successful_users}/{len(usernames)}")
    print(f"   Toplam tweet: {total_tweets}")
    print(f"   Bitis: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 70)


if __name__ == "__main__":
    main()
