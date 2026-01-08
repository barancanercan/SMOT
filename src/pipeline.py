"""Main pipeline - Scraping, Database, Analysis"""

import time
from typing import List, Dict
import sqlite3
from models.database import init_database
from config import QUESTIONS, MAX_TWEETS_TO_SCRAPE, MAX_TWEETS_TO_ANALYZE, DB_PATH
from x_scraper import XTwitterScraper
from src.csv_parser import parse_csv
from src.analyzer import Analyzer


def save_tweets(conn: sqlite3.Connection, username: str, tweets: List, name: str = "",
                party: str = "", district: str = ""):
    """Save tweets with transaction support"""
    if not tweets:
        return 0

    cursor = conn.cursor()

    try:
        cursor.execute("BEGIN TRANSACTION")

        # Step 1: Save councilor
        cursor.execute(
            """INSERT OR REPLACE INTO councilors 
               (username, name, party, district) 
               VALUES (?, ?, ?, ?)""",
            (username, name, party, district)
        )
        print(f"  ✅ @{username} kaydedildi")

        # Step 2: Delete old tweets
        cursor.execute("DELETE FROM tweets WHERE username = ?", (username,))

        # Step 3: Insert new tweets
        inserted_count = 0
        for tweet in tweets:
            try:
                if isinstance(tweet, dict):
                    text = tweet.get("text", "")[:500]
                    tweet_date = tweet.get("timestamp")
                    is_rt = tweet.get("is_retweet", False)
                    rt_from = tweet.get("retweet_from")
                    likes = tweet.get("likes", 0)
                    replies = tweet.get("replies", 0)
                    retweets = tweet.get("retweets", 0)
                else:
                    text = str(tweet)[:500]
                    tweet_date = None
                    is_rt = text.strip().startswith("RT @")
                    rt_from = None
                    likes = 0
                    replies = 0
                    retweets = 0
                    if is_rt:
                        try:
                            rt_from = text.split(":")[0].replace("RT", "").replace("@", "").strip()
                        except:
                            pass

                if not text or len(text) < 5:
                    continue

                cursor.execute(
                    """INSERT INTO tweets 
                       (username, tweet_text, tweet_date, is_retweet, 
                        retweet_from, likes, replies, retweets) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (username, text, tweet_date, int(is_rt),
                     rt_from, int(likes), int(replies), int(retweets))
                )
                inserted_count += 1

            except Exception as e:
                print(f"    ⚠️  Tweet hatası: {str(e)[:30]}")
                continue

        conn.commit()
        print(f"  ✅ {inserted_count} tweet kaydedildi")
        return inserted_count

    except Exception as e:
        print(f"  ❌ HATA! GERİ ALINDI: {str(e)[:50]}")
        conn.rollback()
        return 0


def get_tweets(conn: sqlite3.Connection, username: str) -> List[Dict]:
    """Get tweets from database"""
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute(f"""
        SELECT 
            tweet_text, 
            tweet_date, 
            is_retweet, 
            retweet_from,
            likes,
            replies,
            retweets
        FROM tweets 
        WHERE username = ? 
        ORDER BY tweet_date DESC
        LIMIT {MAX_TWEETS_TO_ANALYZE}
    """, (username,))
    
    results = cursor.fetchall()

    tweets_list = []
    for row in results:
        tweets_list.append({
            "text": row[0],
            "date": row[1],
            "is_retweet": bool(row[2]),
            "retweet_from": row[3],
            "likes": row[4] or 0,
            "replies": row[5] or 0,
            "retweets": row[6] or 0,
        })
    return tweets_list


def scrape_and_analyze(csv_file) -> str:
    """
    Main pipeline:
    1. Parse CSV (+ metadata)
    2. Scrape tweets from X
    3. Save to database
    4. Analyze with LLM
    5. Generate report
    """

    if csv_file is None:
        return "❌ CSV dosyası seçin"

    # Step 1: Parse CSV (YENİ - metadata döndürüyor)
    print("\n" + "=" * 60)
    print("📊 MECLIS İSTİHBARAT SİSTEMİ")
    print("=" * 60)

    print("\n[1/4] CSV PARSING...")
    usernames, metadata = parse_csv(csv_file)

    if not usernames:
        return "❌ CSV'de username veya link bulunamadı"

    print(f"✅ {len(usernames)} üye bulundu")
    print(f"   {', '.join(usernames[:5])}")
    if len(usernames) > 5:
        print(f"   +{len(usernames) - 5} üye daha")

    # Step 2: Scrape tweets
    print("\n[2/4] X'TEN TWEETS FETCH EDILIYOR...")
    scraped_data = {}

    try:
        scraper = XTwitterScraper(
            headless=False
        )
        results = scraper.scrape_multiple(usernames, max_tweets=MAX_TWEETS_TO_SCRAPE)
        scraper.close()
        scraped_data = results
    except Exception as e:
        print(f"⚠️  Scraping hatası: {str(e)[:80]}")
        print("   Fallback modu")

    # Step 3: Save to database (YENİ - metadata ile)
    print("\n[3/4] DATABASE'YE KAYDEDILIYOR...")
    conn = sqlite3.connect(DB_PATH)
    for username in usernames:
        tweets_data = scraped_data.get(username, [])
        tweet_texts = []
        for t in tweets_data:
            if isinstance(t, dict):
                tweet_texts.append(t.get("text", ""))
            else:
                tweet_texts.append(str(t))

        # Metadata'yı al
        user_meta = metadata.get(username, {"name": "Unknown", "party": "", "district": ""})
        
        # save_tweets ile name, party, district'i gönder
        save_tweets(
            conn,
            username, 
            tweet_texts,
            name=user_meta.get("name", "Unknown"),
            party=user_meta.get("party", ""),
            district=user_meta.get("district", "")
        )

    print(f"✅ {len(usernames)} üye kaydedildi")
    total_tweets = sum(len(scraped_data.get(u, [])) for u in usernames)
    print(f"   {total_tweets} tweet toplandı")

    # Step 4: Analyze with LLM
    print("\n[4/4] ANALIZ VE RAPOR OLUŞTURULUYOR...")
    analyzer = Analyzer()

    report = "# 📊 Ankara Meclis Üyeleri Analiz Raporu\n\n"

    for idx, username in enumerate(usernames, 1):
        tweets = get_tweets(conn, username)

        if not tweets:
            continue

        print(f"\n[{idx}/{len(usernames)}] @{username} analiz ediliyor...")

        report += f"## 👤 @{username}\n\n"

        for q_idx, question in enumerate(QUESTIONS, 1):
            print(f"  ├─ Soru {q_idx}/3: {question[:35]}...", end=" ", flush=True)

            answer = analyzer.analyze(tweets, username, question)

            print("✅")

            report += f"### Q{q_idx}: {question}\n\n"
            report += f"{answer}\n\n"

        report += "---\n\n"

    conn.close()
    print("\n" + "=" * 60)
    print("✅ RAPOR TAMAMLANDI!")
    print("=" * 60 + "\n")

    return report
