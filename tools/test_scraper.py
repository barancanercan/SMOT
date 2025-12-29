#!/usr/bin/env python3
"""
🧪 X Scraper Test Script
data.csv'den meclis üyeleri çek → X'ten tweets al → Kalite kontrol
"""

import pandas as pd
import json
from typing import Dict, List
from x_scraper import XTwitterScraper

# ============================================================================
# CONFIG
# ============================================================================

CSV_PATH = "data.csv"
OUTPUT_JSON = "scraper_test_results.json"
MAX_TWEETS_PER_USER = 100  # Daha fazla tweet çek


# ============================================================================
# STEP 1: CSV Oku
# ============================================================================

def load_csv(csv_path: str) -> List[str]:
    """CSV'den meclis üyeleri çek"""
    print("\n" + "=" * 70)
    print("📖 STEP 1: CSV'DEN MECLİS ÜYELERİNİ ÇEKME")
    print("=" * 70 + "\n")

    try:
        df = pd.read_csv(csv_path)
        print(f"✅ CSV açıldı: {csv_path}")
        print(f"   Satır sayısı: {len(df)}")
        print(f"   Sütunlar: {list(df.columns)}\n")

        # Link sütunundan username çek
        usernames = []
        for idx, row in df.iterrows():
            link = str(row.get("link", "")).strip()
            if link and "x.com/" in link:
                username = link.split("x.com/")[-1].strip("/").replace("@", "")
                name = row.get("Meclis Üyesi", "Unknown")
                usernames.append({
                    "username": username,
                    "name": name,
                    "party": row.get("Parti", "Unknown"),
                    "district": row.get("İlçe", "Unknown")
                })

        print(f"✅ {len(usernames)} üye bulundu:")
        for i, u in enumerate(usernames[:5], 1):
            print(f"   {i}. @{u['username']:20s} ({u['name']})")
        if len(usernames) > 5:
            print(f"   ... +{len(usernames) - 5} üye daha\n")

        return [u["username"] for u in usernames], usernames

    except Exception as e:
        print(f"❌ CSV hatası: {e}")
        return [], []


# ============================================================================
# STEP 2: X Scraping
# ============================================================================

def scrape_tweets(usernames: List[str], max_per_user: int = 100, days_back: int = 90) -> Dict:
    """X'ten tweets çek"""
    print("\n" + "=" * 70)
    print(f"🐦 STEP 2: X'TEN TWEETS ÇEKME (Son {days_back} Gün)")
    print("=" * 70 + "\n")

    print(f"⚙️  Settings:")
    print(f"   - Max tweets/user: {max_per_user}")
    print(f"   - Zaman aralığı: Son {days_back} gün")
    print(f"   - Headless mode: OFF (Görünür)")
    print(f"   - Timeout: 60+ saniye")
    print(f"   - Authentication: ✅ ON (Private accounts)\n")

    results = {}

    try:
        # X hesabı ile giriş yap
        scraper = XTwitterScraper(
            headless=False,
            username="yereldeetk",
            password="yereldeetkilesiyoruz.1"
        )

        if scraper.driver is None:
            print("❌ Scraper driver initialize edilemedi!")
            return {}

        print(f"🔄 {len(usernames)} üyeden tweet çekiliyor...\n")

        for i, username in enumerate(usernames, 1):
            print(f"[{i:2d}/{len(usernames)}]", end=" ")
            tweets = scraper.scrape_tweets(username, max_tweets=max_per_user, days_back=days_back)

            if tweets:
                results[username] = {
                    "count": len(tweets),
                    "tweets": tweets,
                    "status": "✅ Success"
                }
            else:
                results[username] = {
                    "count": 0,
                    "tweets": [],
                    "status": "⚠️  No tweets"
                }

        scraper.close()

        print(f"\n\n✅ Scraping tamamlandı!")
        return results

    except Exception as e:
        print(f"\n❌ Scraping hatası: {e}")
        return results


# ============================================================================
# STEP 3: Kalite Kontrol
# ============================================================================

def quality_check(results: Dict, metadata: List, days_back: int = 90) -> Dict:
    """Çekilen verileri kontrol et"""
    print("\n" + "=" * 70)
    print(f"🔍 STEP 3: KALİTE KONTROL (Son {days_back} Gün)")
    print("=" * 70 + "\n")

    from datetime import datetime, timedelta

    stats = {
        "total_users": len(results),
        "successful": 0,
        "failed": 0,
        "total_tweets": 0,
        "avg_tweets_per_user": 0,
        "empty_tweets": [],
        "errors": [],
        "date_range": {
            "oldest": None,
            "newest": None,
            "out_of_range": 0
        }
    }

    cutoff_date = datetime.now() - timedelta(days=days_back)

    # Hesapla
    for username, data in results.items():
        if data["count"] > 0:
            stats["successful"] += 1
            stats["total_tweets"] += data["count"]

            # Tarih kontrolü
            for tweet in data["tweets"]:
                if isinstance(tweet, dict) and tweet.get("timestamp"):
                    try:
                        tweet_date = datetime.fromisoformat(
                            tweet["timestamp"].replace('Z', '+00:00')
                        )

                        # Track date range
                        if stats["date_range"]["oldest"] is None:
                            stats["date_range"]["oldest"] = tweet_date
                            stats["date_range"]["newest"] = tweet_date
                        else:
                            if tweet_date < stats["date_range"]["oldest"]:
                                stats["date_range"]["oldest"] = tweet_date
                            if tweet_date > stats["date_range"]["newest"]:
                                stats["date_range"]["newest"] = tweet_date

                        # Check if in range
                        if tweet_date < cutoff_date:
                            stats["date_range"]["out_of_range"] += 1
                    except:
                        pass
        else:
            stats["failed"] += 1
            stats["empty_tweets"].append(username)

    if stats["successful"] > 0:
        stats["avg_tweets_per_user"] = stats["total_tweets"] / stats["successful"]

    # Rapor
    print(f"📊 Genel İstatistikler:")
    print(f"   Total Users: {stats['total_users']}")
    print(f"   ✅ Başarılı: {stats['successful']}")
    print(f"   ❌ Başarısız: {stats['failed']}")
    print(f"   Total Tweets: {stats['total_tweets']}")
    print(f"   Avg/User: {stats['avg_tweets_per_user']:.1f}")

    print(f"\n📈 Başarı Oranı: {(stats['successful'] / stats['total_users'] * 100):.1f}%" if stats[
                                                                                                'total_users'] > 0 else "   ❌ Veri yok")

    # Tarih kontrolü
    print(f"\n📅 TARİH KONTROL:")
    if stats["date_range"]["newest"]:
        print(f"   ✅ En Yeni Tweet: {stats['date_range']['newest'].strftime('%d.%m.%Y %H:%M')}")
        print(f"   ✅ En Eski Tweet: {stats['date_range']['oldest'].strftime('%d.%m.%Y %H:%M')}")
        print(f"   ⚠️  {days_back} günden eski: {stats['date_range']['out_of_range']} tweet")

        if stats["date_range"]["out_of_range"] > 0:
            print(f"   ❌ HATA: Filtre çalışmıyor! Eski tweetler var!")
        else:
            print(f"   ✅ BAŞARILI: Tüm tweetler son {days_back} günde!")

    if stats["empty_tweets"]:
        print(f"\n⚠️  Tweet Alamadığımız Üyeler:")
        for u in stats["empty_tweets"][:5]:
            print(f"   • @{u}")
        if len(stats["empty_tweets"]) > 5:
            print(f"   ... +{len(stats['empty_tweets']) - 5} daha")

    # Top users
    sorted_users = sorted(results.items(), key=lambda x: x[1]["count"], reverse=True)
    print(f"\n🏆 En Çok Tweet Alan 5 Üye (son {days_back} gün):")
    for i, (username, data) in enumerate(sorted_users[:5], 1):
        meta = next((m for m in metadata if m["username"] == username), {})
        print(f"   {i}. @{username:20s} - {data['count']:3d} tweet ({meta.get('name', 'Unknown')})")

    return stats


# ============================================================================
# STEP 4: Örnek Tweet Göster
# ============================================================================

def show_samples(results: Dict, metadata: List, samples_per_user: int = 3):
    """Örnek tweetler göster"""
    print("\n" + "=" * 70)
    print("📝 STEP 4: ÖRNEK TWEETLER (TARİH İLE)")
    print("=" * 70 + "\n")

    for username, data in list(results.items())[:3]:  # İlk 3 üye
        if data["tweets"]:
            meta = next((m for m in metadata if m["username"] == username), {})
            print(f"👤 @{username} ({meta.get('name', 'Unknown')})")
            print(f"   Parti: {meta.get('party', 'Unknown')}")
            print(f"   Total Tweet: {data['count']}\n")

            for i, tweet_obj in enumerate(data["tweets"][:samples_per_user], 1):
                # Handle both dict and string
                if isinstance(tweet_obj, dict):
                    tweet_text = tweet_obj.get("text", "")
                    tweet_date = tweet_obj.get("timestamp", "N/A")
                else:
                    tweet_text = str(tweet_obj)
                    tweet_date = "N/A"

                tweet_preview = tweet_text[:120] + "..." if len(tweet_text) > 120 else tweet_text

                # Format date
                if tweet_date and tweet_date != "N/A":
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(tweet_date.replace('Z', '+00:00'))
                        date_str = dt.strftime("%d.%m.%Y %H:%M")
                    except:
                        date_str = tweet_date[:10]
                else:
                    date_str = "Tarih yok"

                print(f"   Tweet {i}: [{date_str}]")
                print(f"   >>> {tweet_preview}\n")

            print()


# ============================================================================
# STEP 5: JSON Export
# ============================================================================

def export_json(results: Dict, metadata: List, output_file: str):
    """Sonuçları JSON'a kaydet"""
    print("\n" + "=" * 70)
    print("💾 STEP 5: SONUÇLARI KAYDETME")
    print("=" * 70 + "\n")

    export_data = {
        "metadata": {
            "total_users": len(results),
            "total_tweets": sum(d["count"] for d in results.values()),
            "timestamp": pd.Timestamp.now().isoformat(),
            "days_back": 90
        },
        "results": {}
    }

    for username, data in results.items():
        meta = next((m for m in metadata if m["username"] == username), {})

        # Handle both dict and string tweets
        tweets_list = []
        for tweet in data["tweets"][:10]:
            if isinstance(tweet, dict):
                tweets_list.append({
                    "text": tweet.get("text", ""),
                    "timestamp": tweet.get("timestamp", None),
                    "username": tweet.get("username", username)
                })
            else:
                tweets_list.append({
                    "text": str(tweet),
                    "timestamp": None,
                    "username": username
                })

        export_data["results"][username] = {
            "metadata": meta,
            "tweet_count": data["count"],
            "status": data["status"],
            "tweets": tweets_list
        }

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        print(f"✅ Sonuçlar kaydedildi: {output_file}")
        print(f"   Dosya boyutu: {len(json.dumps(export_data, ensure_ascii=False)):.1f} KB")
        print(f"   Total tweets: {export_data['metadata']['total_tweets']}")

    except Exception as e:
        print(f"❌ Export hatası: {e}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("\n" + "=" * 70)
    print("🧪 X SCRAPER TEST - ANKARA MECLİS ÜYELERİ")
    print("=" * 70)

    DAYS_BACK = 90

    # Step 1: CSV Load
    usernames, metadata = load_csv(CSV_PATH)

    if not usernames:
        print("❌ Üye bulunamadı. Çıkılıyor...")
        return

    # Step 2: Scraping (son 90 gün)
    results = scrape_tweets(usernames, max_per_user=MAX_TWEETS_PER_USER, days_back=DAYS_BACK)

    # Step 3: Quality Check (90 gün)
    stats = quality_check(results, metadata, days_back=DAYS_BACK)

    # Step 4: Show Samples
    show_samples(results, metadata, samples_per_user=2)

    # Step 5: Export
    export_json(results, metadata, OUTPUT_JSON)

    # Final summary
    print("\n" + "=" * 70)
    print("✅ TEST TAMAMLANDI")
    print("=" * 70)
    print(f"\n📋 Sonuç Özeti:")
    print(f"   ✅ Başarılı: {stats['successful']}/{stats['total_users']}")
    print(f"   📊 Total Tweets: {stats['total_tweets']}")
    print(f"   ⏰ Zaman Aralığı: Son {DAYS_BACK} gün")
    print(f"   💾 JSON Dosyası: {OUTPUT_JSON}")
    print(f"\nSonraki adım: JSON'ı kontrol et → meclis_app.py'yı çalıştır!\n")


if __name__ == "__main__":
    main()