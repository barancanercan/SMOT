#!/usr/bin/env python3
"""
Ulaşılamayan Instagram hesaplarını yeniden dener.
Brave CDP port 9226'da açık olmalı ve instagram.com'a giriş yapılmış olmalı.
"""
import os, sys, time, logging
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from scrapers.batch_instagram import (
    scrape_user_posts, save_post_to_db, save_ig_profile,
    CDPBrowser, IG_CDP_PORT, DB_PATH, parse_ig_metric
)
import sqlite3
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
log = logging.getLogger("RetryInstagram")

START_DATE = datetime(2026, 1, 1)
DAYS_BACK  = (datetime.now() - START_DATE).days + 1
MAX_POSTS  = 500

IG_SESSION = os.path.join(PROJECT_ROOT, "ig_session.json")


def get_missing_users():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("""
        SELECT c.instagram_username, c.name
        FROM councilors c
        WHERE c.instagram_username IS NOT NULL AND c.instagram_username != ''
        AND NOT EXISTS (
            SELECT 1 FROM instagram_posts ip WHERE ip.username = c.instagram_username
        )
        ORDER BY c.instagram_username
    """).fetchall()
    conn.close()
    return [(r[0], r[1]) for r in rows]


def main():
    users = get_missing_users()
    log.info(f"Yeniden denenecek: {len(users)} kullanıcı")
    for u, n in users:
        log.info(f"  @{u} — {n}")

    if not users:
        log.info("Tüm kullanıcıların postu var, işlem gerekmiyor.")
        return

    CDPBrowser._instance = None
    browser = CDPBrowser(chrome_port=IG_CDP_PORT)

    try:
        browser.ensure_running()
    except Exception as e:
        log.error(f"Brave bağlantısı kurulamadı (port {IG_CDP_PORT}): {e}")
        return

    if os.path.isfile(IG_SESSION):
        browser.inject_cookies(IG_SESSION, ".instagram.com")
        log.info("Session yüklendi")

    success = skip = fail = 0
    total_new = 0

    for i, (ig_user, name) in enumerate(users, 1):
        log.info(f"\n[{i}/{len(users)}] @{ig_user} ({name})")
        try:
            posts, profile = scrape_user_posts(browser, ig_user, MAX_POSTS, DAYS_BACK)

            if profile:
                save_ig_profile(ig_user, profile)
                fol = profile.get('followers', '0')
                log.info(f"  Profil: {fol} takipçi")

            if posts:
                new = sum(1 for p in posts if save_post_to_db(p, ig_user))
                total_new += new
                success += 1
                log.info(f"  OK: {len(posts)} post ({new} yeni)")
            else:
                skip += 1
                reason = "gizli hesap" if profile and parse_ig_metric(str(profile.get('followers','0'))) > 0 else "içerik yok / erişilemiyor"
                log.warning(f"  SKIP: post bulunamadı ({reason})")

            if i < len(users):
                time.sleep(4)

        except KeyboardInterrupt:
            log.info("Durduruldu.")
            break
        except Exception as e:
            fail += 1
            log.error(f"  HATA: {e}")
            time.sleep(5)

    try:
        browser.close()
    except Exception:
        pass

    log.info(f"\n{'='*50}")
    log.info(f"RETRY TAMAMLANDI")
    log.info(f"  Başarılı: {success} | Boş/Gizli: {skip} | Hata: {fail}")
    log.info(f"  Yeni post: {total_new}")
    log.info(f"{'='*50}")


if __name__ == "__main__":
    main()
