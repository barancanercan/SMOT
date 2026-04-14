#!/usr/bin/env python3
"""
Twitter Scraper — 3 kullanici ile test.
Gercek Chrome CDP kullanir (port 9222).
"""
import sqlite3, os, sys, json, logging
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from scrapers.twitter_scraper import TwitterCDPScraper, parse_metric

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger("TEST_TWITTER")

DB_PATH = os.path.join(PROJECT_ROOT, "data", "sam.db")
TEST_USERS = ["abbas_atamer", "atila_celik06", "cihanayhan85"]
MAX_TWEETS  = 10
DAYS_BACK   = 30


# ──────────────────────────────────────────────────────────────
# Birim testleri — parse_metric
# ──────────────────────────────────────────────────────────────

def test_parse_metric() -> bool:
    """parse_metric'in tum formatlari dogru integer'a cevirdigini dogrula."""
    cases = [
        # (girdi, beklenen, aciklama)
        ("1.2K",        1200,          "Ingilizce ondalik nokta + K"),
        ("5.5M",        5500000,       "M = milyon"),
        ("1.2B",        1200000000,    "B = milyar (Twitter Ingilizce)"),
        ("10K",         10000,         "tam K"),
        ("1,234",       1234,          "Ingilizce binlik virgul"),
        ("10,500",      10500,         "binlik virgul buyuk"),
        ("123",         123,           "duz sayi"),
        ("0",           0,             "sifir"),
        ("",            0,             "bos string"),
        (0,             0,             "integer sifir"),
        (1500,          1500,          "zaten integer"),
        ("2.5K",        2500,          "ondalik K"),
        ("100M",        100000000,     "tam M"),
    ]

    print("\n" + "="*60)
    print("BIRIM TEST — parse_metric (Twitter)")
    print("="*60)
    print(f"  {'Girdi':<20} {'Beklenen':>15} {'Sonuc':>15}  {'Durum'}")
    print("  " + "-"*60)

    passed = failed = 0
    for raw, expected, desc in cases:
        result = parse_metric(raw)
        ok = result == expected
        status = "OK" if ok else "HATA"
        marker = "" if ok else f"  ← beklenen {expected:,}"
        print(f"  {repr(raw):<20} {expected:>15,} {result:>15,}  {status}{marker}  ({desc})")
        if ok:
            passed += 1
        else:
            failed += 1

    print("  " + "-"*60)
    print(f"  Toplam: {passed} gecti / {failed} basarisiz")
    print("="*60)
    return failed == 0


# ──────────────────────────────────────────────────────────────
# DB yardimcilari
# ──────────────────────────────────────────────────────────────

def save_tweets(tweets: list, username: str) -> tuple:
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
            existing = conn.execute("SELECT id FROM tweets WHERE tweet_id=?", (tweet_id,)).fetchone()
            if existing:
                conn.execute(
                    "UPDATE tweets SET likes=?,replies=?,retweets=?,views=?,bookmarks=? WHERE id=?",
                    (t.get("likes",0), t.get("replies",0), t.get("retweets",0),
                     t.get("views",0), t.get("bookmarks",0), existing[0])
                )
                updated += 1
            else:
                conn.execute("""
                    INSERT INTO tweets (
                        username, tweet_id, tweet_url,
                        tweet_text, tweet_date,
                        is_retweet, retweet_from,
                        likes, replies, retweets, views, bookmarks,
                        media_type, media_urls, media_count,
                        hashtags, mentions, language, quote_tweet_id
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    username,
                    tweet_id,
                    t.get("tweet_url", ""),
                    t.get("text", ""),
                    t.get("timestamp", ""),
                    1 if t.get("is_retweet") else 0,
                    t.get("retweet_from"),
                    t.get("likes", 0), t.get("replies", 0),
                    t.get("retweets", 0), t.get("views", 0),
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


def save_profile(username: str, profile: dict) -> None:
    if not profile:
        return
    conn = sqlite3.connect(DB_PATH)
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
    finally:
        conn.close()


def verify_db(tweet_id: str) -> None:
    """DB'ye yazilan degerlerin tam integer oldugunu dogrula."""
    if not tweet_id:
        return
    try:
        conn = sqlite3.connect(DB_PATH)
        row = conn.execute(
            "SELECT likes, replies, retweets, views, bookmarks FROM tweets WHERE tweet_id=?",
            (tweet_id,)
        ).fetchone()
        conn.close()
        if row:
            likes, replies, retweets, views, bookmarks = row
            all_int = all(isinstance(v, int) for v in row)
            status = "OK" if all_int else "HATA"
            print(f"  [DB CHECK {status}] likes={likes}, replies={replies}, "
                  f"retweets={retweets}, views={views}, bookmarks={bookmarks}")
        else:
            print(f"  [DB CHECK] Tweet DB'de bulunamadi: {tweet_id}")
    except Exception as e:
        print(f"  [DB CHECK HATA] {e}")


# ──────────────────────────────────────────────────────────────
# Ekran ciktisi
# ──────────────────────────────────────────────────────────────

def print_tweet(t: dict, idx: int) -> None:
    likes     = t.get('likes', 0)
    replies   = t.get('replies', 0)
    retweets  = t.get('retweets', 0)
    views     = t.get('views', 0)
    bookmarks = t.get('bookmarks', 0)
    # Abbreviated string kalmamali
    for field, val in [("likes", likes), ("views", views)]:
        if isinstance(val, str):
            print(f"  [!ABBREVIATED?] {field}={val!r}")

    print(f"\n  --- Tweet #{idx} ---")
    print(f"  URL      : {t.get('tweet_url','')}")
    print(f"  Tarih    : {t.get('timestamp','')}")
    print(f"  Likes    : {likes:,}")
    print(f"  Replies  : {replies:,}")
    print(f"  Retweets : {retweets:,}")
    print(f"  Views    : {views:,}")
    print(f"  Bookmarks: {bookmarks:,}")
    print(f"  RT?      : {t.get('is_retweet')} | From: {t.get('retweet_from','')}")
    print(f"  Hashtags : {t.get('hashtags',[])}")
    print(f"  Mentions : {t.get('mentions',[])}")
    print(f"  Media    : {t.get('media_type')} x{t.get('media_count',0)}")
    text = str(t.get('text', ''))
    print(f"  Metin    : {text[:200]}{'...' if len(text) > 200 else ''}")


# ──────────────────────────────────────────────────────────────
# Ana test
# ──────────────────────────────────────────────────────────────

def main():
    # 1. Birim testleri calistir
    unit_ok = test_parse_metric()
    if not unit_ok:
        print("\n[!] Birim testleri basarisiz — scrape testi iptal.")
        return

    print("\n" + "="*60)
    print("TWITTER SCRAPE TESTI — 3 KULLANICI")
    print("="*60)

    scraper = TwitterCDPScraper(mock=False)

    try:
        for username in TEST_USERS:
            print(f"\n{'='*60}")
            print(f"@{username}")
            print(f"{'='*60}")

            # Profil
            print("\n[PROFIL ÇEKİLİYOR...]")
            profile = scraper.scrape_profile(username)
            if profile:
                fol = parse_metric(profile.get('followers', '0'))
                fwg = parse_metric(profile.get('following', '0'))
                tc  = parse_metric(profile.get('tweetCount', '0'))
                print(f"  Bio      : {profile.get('bio','')[:80]}")
                print(f"  Takipci  : {fol:,}  (ham: {profile.get('followers','?')})")
                print(f"  Takip    : {fwg:,}  (ham: {profile.get('following','?')})")
                print(f"  Tweetler : {tc:,}  (ham: {profile.get('tweetCount','?')})")
                save_profile(username, profile)
            else:
                print("  [!] Profil alinamadi")

            # Tweetler
            print(f"\n[TWEETLER ÇEKİLİYOR... max={MAX_TWEETS}, days={DAYS_BACK}]")
            tweets = scraper.scrape_tweets(username, max_tweets=MAX_TWEETS, days_back=DAYS_BACK)

            if tweets:
                saved, updated = save_tweets(tweets, username)
                print(f"\n  {len(tweets)} tweet | {saved} yeni | {updated} guncellendi")
                for i, t in enumerate(tweets[:2], 1):
                    print_tweet(t, i)
                    verify_db(t.get('tweet_id', ''))
            else:
                print("  [!] Hic tweet alinamadi")

    finally:
        scraper.close()

    print("\n" + "="*60)
    print("TEST TAMAMLANDI")
    print("="*60)


if __name__ == "__main__":
    main()
