#!/usr/bin/env python3
"""
Instagram Scraper — 3 kullanici ile test.
Brave/Chrome CDP port 9226 kullanir.

Onceden:
  Start-Process "C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe" `
    -ArgumentList "--remote-debugging-port=9226","--remote-allow-origins=*","--user-data-dir=C:\tmp\chrome-ig"
  Sonra instagram.com'a giris yap.
"""
import os, sys, logging, sqlite3
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from scrapers.batch_instagram import (
    scrape_user_posts, save_post_to_db, save_ig_profile,
    CDPBrowser, IG_CDP_PORT, parse_ig_metric, DB_PATH
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger("TEST_INSTAGRAM")

IG_SESSION = os.path.join(PROJECT_ROOT, "ig_session.json")
TEST_USERS  = ["atilacelik06", "tolgaturgut06", "avfatihunal"]
MAX_POSTS   = 5
DAYS_BACK   = 90


# ──────────────────────────────────────────────────────────────
# Birim testleri — parse_ig_metric
# ──────────────────────────────────────────────────────────────

def test_parse_ig_metric() -> bool:
    """parse_ig_metric'in tum formatlari dogru integer'a cevirdigini dogrula."""
    cases = [
        # (girdi, beklenen, aciklama)
        ("2,8B",        2800,      "Turkce B=Bin=1000"),
        ("2,8\xa0B",    2800,      "non-breaking space ile"),
        ("2.9B",        2900,      "Ingilizce ondalik nokta + B"),
        ("151",         151,       "duz sayi"),
        ("277",         277,       "duz sayi"),
        ("1.680",       1680,      "Turkce binlik nokta (3 hane)"),
        ("29.153",      29153,     "Turkce binlik nokta (5 hane)"),
        ("1.234.567",   1234567,   "cift binlik nokta"),
        ("72,4K",       72400,     "Turkce ondalik virgul + K"),
        ("1,2M",        1200000,   "Turkce ondalik virgul + M"),
        ("10.5K",       10500,     "Ingilizce ondalik nokta + K"),
        ("1,234",       1234,      "Ingilizce binlik virgul"),
        ("0",           0,         "sifir"),
        ("",            0,         "bos string"),
        (0,             0,         "integer sifir"),
        (2800,          2800,      "zaten integer"),
    ]

    print("\n" + "="*60)
    print("BIRIM TEST — parse_ig_metric")
    print("="*60)
    print(f"  {'Girdi':<20} {'Beklenen':>10} {'Sonuc':>10}  {'Durum'}")
    print("  " + "-"*55)

    passed = failed = 0
    for raw, expected, desc in cases:
        result = parse_ig_metric(raw)
        ok = result == expected
        status = "OK" if ok else "HATA"
        marker = "" if ok else f"  ← beklenen {expected}"
        print(f"  {repr(raw):<20} {expected:>10,} {result:>10,}  {status}{marker}  ({desc})")
        if ok:
            passed += 1
        else:
            failed += 1

    print("  " + "-"*55)
    print(f"  Toplam: {passed} gecti / {failed} basarisiz")
    print("="*60)
    return failed == 0


# ──────────────────────────────────────────────────────────────
# Ekran ciktisi
# ──────────────────────────────────────────────────────────────

def print_post(p: dict, idx: int) -> None:
    likes    = p.get('likes', 0)
    comments = p.get('comments', 0)
    views    = p.get('video_views', 0)
    # Tam integer mi? (abbreviated string kalmamali)
    likes_warn    = " [!ABBREVIATED?]" if isinstance(likes,    str) else ""
    comments_warn = " [!ABBREVIATED?]" if isinstance(comments, str) else ""
    views_warn    = " [!ABBREVIATED?]" if isinstance(views,    str) else ""

    print(f"\n  --- Post #{idx} ---")
    print(f"  URL      : {p.get('post_url','')}")
    print(f"  Shortcode: {p.get('shortcode','')}")
    print(f"  Tarih    : {p.get('post_date','')}")
    print(f"  Tur      : {p.get('post_type','')}")
    print(f"  Likes    : {likes:,}{likes_warn}")
    print(f"  Comments : {comments:,}{comments_warn}")
    print(f"  Video?   : {p.get('is_video')} | Views: {views:,}{views_warn}")
    print(f"  Hashtags : {p.get('hashtags',[])}")
    print(f"  Mentions : {p.get('mentions',[])}")
    caption = p.get('caption', '')
    print(f"  Caption  : {caption[:300]}{'...' if len(caption) > 300 else ''}")
    if p.get('_roleButtonSpans'):
        print(f"  [DBG] spans: {p.get('_roleButtonSpans')}")


def verify_db(ig_user: str, post_url: str) -> None:
    """DB'ye yazilan degerlerin tam integer oldugunu dogrula."""
    if not post_url:
        return
    try:
        conn = sqlite3.connect(DB_PATH)
        row = conn.execute(
            "SELECT likes, comments, video_views FROM instagram_posts WHERE post_url=?",
            (post_url,)
        ).fetchone()
        conn.close()
        if row:
            likes, comments, views = row
            # SQLite INTEGER tipinde saklanmali
            ok_l = isinstance(likes,    int)
            ok_c = isinstance(comments, int)
            ok_v = isinstance(views,    int)
            status = "OK" if (ok_l and ok_c and ok_v) else "HATA"
            print(f"  [DB CHECK {status}] likes={likes} ({type(likes).__name__}), "
                  f"comments={comments} ({type(comments).__name__}), "
                  f"views={views} ({type(views).__name__})")
        else:
            print(f"  [DB CHECK] Post DB'de bulunamadi: {post_url}")
    except Exception as e:
        print(f"  [DB CHECK HATA] {e}")


# ──────────────────────────────────────────────────────────────
# Ana test
# ──────────────────────────────────────────────────────────────

def main():
    # 1. Birim testleri calistir
    unit_ok = test_parse_ig_metric()
    if not unit_ok:
        print("\n[!] Birim testleri basarisiz — scrape testi iptal.")
        return

    print("\n" + "="*60)
    print("INSTAGRAM SCRAPE TESTI — 3 KULLANICI")
    print(f"CDP Port: {IG_CDP_PORT}")
    print("="*60)

    CDPBrowser._instance = None
    browser = CDPBrowser(chrome_port=IG_CDP_PORT)

    try:
        browser.ensure_running()
    except Exception as e:
        print(f"\n[HATA] Chrome baglantisi kurulamadi: {e}")
        print("\nBrave'i su sekilde baslat (PowerShell):")
        print(f'  Start-Process "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe" `')
        print(f'    -ArgumentList "--remote-debugging-port={IG_CDP_PORT}","--remote-allow-origins=*","--user-data-dir=C:\\tmp\\chrome-ig"')
        print("\nSonra instagram.com'a giris yap ve tekrar calistir.")
        return

    if os.path.isfile(IG_SESSION):
        browser.inject_cookies(IG_SESSION, ".instagram.com")
        log.info("Session yuklendi")
    else:
        log.warning(f"Session dosyasi yok: {IG_SESSION}")

    for ig_user in TEST_USERS:
        print(f"\n{'='*60}")
        print(f"@{ig_user}")
        print(f"{'='*60}")

        posts, profile = scrape_user_posts(browser, ig_user, MAX_POSTS, DAYS_BACK)

        # Profil
        if profile:
            fol = parse_ig_metric(profile.get('followers', '0'))
            fwg = parse_ig_metric(profile.get('following', '0'))
            pc  = parse_ig_metric(profile.get('postCount', '0'))
            print(f"\n  [PROFIL]")
            print(f"  Bio      : {profile.get('bio','')[:80]}")
            print(f"  Takipci  : {fol:,}  (ham: {profile.get('followers','?')})")
            print(f"  Takip    : {fwg:,}  (ham: {profile.get('following','?')})")
            print(f"  Post say : {pc:,}  (ham: {profile.get('postCount','?')})")
            save_ig_profile(ig_user, profile)
        else:
            print("  [!] Profil alinamadi")

        # Postlar
        if posts:
            new = sum(1 for p in posts if save_post_to_db(p, ig_user))
            print(f"\n  {len(posts)} post alindi ({new} yeni kaydedildi)")
            for i, p in enumerate(posts[:3], 1):
                print_post(p, i)
                # DB dogrulama: kaydedildi mi ve integer mi?
                verify_db(ig_user, p.get('post_url', ''))
        else:
            print("  [!] Post alinamadi")

    print("\n" + "="*60)
    print("TEST TAMAMLANDI")
    print("="*60)


if __name__ == "__main__":
    main()
