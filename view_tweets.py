#!/usr/bin/env python3
"""
📊 Database'deki Tweetleri CSV/Tablo Formatında Göster
"""

import sqlite3
import csv
from tabulate import tabulate

DB_PATH = "meclis.db"


def view_tweets_table():
    """Database'deki tweetleri tablo formatında göster"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Tüm tweetleri getir (tarih ve retweet bilgisi ile)
    cursor.execute("""
        SELECT 
            c.username,
            c.name,
            c.party,
            COUNT(t.id) as tweet_count,
            SUM(CASE WHEN t.is_retweet = 1 THEN 1 ELSE 0 END) as retweet_count
        FROM councilors c
        LEFT JOIN tweets t ON c.username = t.username
        GROUP BY c.username
        ORDER BY tweet_count DESC
    """)

    data = cursor.fetchall()

    # Tablo başlıkları
    headers = ["Username", "Ad", "Parti", "Tweet Sayısı", "RT Sayısı"]

    print("\n" + "=" * 120)
    print("📊 ANKARA MECLİS ÜYELERİ - TWEET İSTATİSTİKLERİ (Tablo)")
    print("=" * 120 + "\n")

    # Tablo yazdır
    print(tabulate(data, headers=headers, tablefmt="grid"))

    # Özet istatistikler
    cursor.execute("SELECT COUNT(*) FROM tweets")
    total_tweets = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tweets WHERE is_retweet = 1")
    total_retweets = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT username) FROM tweets")
    active_users = cursor.fetchone()[0]

    print(f"\n📈 ÖZT İSTATİSTİKLER:")
    print(f"   Total Tweet: {total_tweets}")
    print(
        f"   Total Retweet: {total_retweets} ({total_retweets / total_tweets * 100:.1f}%)" if total_tweets > 0 else "   Total Retweet: 0")
    print(f"   Orijinal Tweet: {total_tweets - total_retweets}")
    print(f"   Aktif Üye: {active_users}/{len(data)}")
    print(f"   Ortalama/Üye: {total_tweets / active_users if active_users > 0 else 0:.1f}\n")

    conn.close()


def export_to_csv(output_file="tweets_all.csv"):
    """Tweetleri CSV'ye export et - TÜMLÜ BİLGİ"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Tüm tweetleri getir
    cursor.execute("""
        SELECT 
            c.username,
            c.name,
            c.party,
            t.tweet_text,
            t.tweet_date,
            CASE WHEN t.is_retweet = 1 THEN 'EVET' ELSE 'HAYIR' END as is_retweet,
            t.retweet_from,
            t.created_at
        FROM tweets t
        JOIN councilors c ON t.username = c.username
        ORDER BY c.username, t.created_at DESC
    """)

    tweets = cursor.fetchall()

    # CSV'ye yaz
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            "Username",
            "İsim",
            "Parti",
            "Tweet",
            "Tweet Tarihi (Twitter)",
            "Retweet Mi?",
            "Kimden RT?",
            "Kaydedilme Tarihi"
        ])
        writer.writerows(tweets)

    print(f"✅ CSV dosyası kaydedildi: {output_file}")
    print(f"   Toplam {len(tweets)} tweet dışa aktarıldı")
    print(f"   Sütunlar: Username, İsim, Parti, Tweet, Tweet Tarihi, Retweet, RT Kaynağı, Kaydedilme Tarihi\n")

    conn.close()


def export_summary_csv(output_file="tweets_statistics.csv"):
    """Özet istatistikleri CSV'ye export et"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            c.username,
            c.name,
            c.party,
            COUNT(t.id) as tweet_count,
            SUM(CASE WHEN t.is_retweet = 1 THEN 1 ELSE 0 END) as retweet_count,
            COUNT(t.id) - SUM(CASE WHEN t.is_retweet = 1 THEN 1 ELSE 0 END) as original_count
        FROM councilors c
        LEFT JOIN tweets t ON c.username = t.username
        GROUP BY c.username
        ORDER BY tweet_count DESC
    """)

    data = cursor.fetchall()

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Username", "Ad", "Parti", "Total Tweet", "Retweet", "Orijinal"])
        writer.writerows(data)

    print(f"✅ Özet CSV dosyası kaydedildi: {output_file}")
    print(f"   {len(data)} üyenin verisi kaydedildi\n")

    conn.close()


if __name__ == "__main__":
    # Tablo göster
    view_tweets_table()

    # CSV'ye export et
    print("=" * 100)
    print("💾 CSV EXPORT")
    print("=" * 100 + "\n")
    export_summary_csv("tweets_statistics.csv")
    export_to_csv("tweets_all.csv")