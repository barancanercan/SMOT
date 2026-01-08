#!/usr/bin/env python3
"""
📊 Enhanced CSV Export v3.2
✅ Views column added
✅ RT detection results
✅ Full tweet statistics
"""

import sqlite3
import csv
from datetime import datetime

DB_PATH = "meclis.db"


def export_all_tweets(output_file="tweets_export_v3_2.csv"):
    """Export all tweets with full metadata including views"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get all tweets with councilor info
    cursor.execute("""
        SELECT 
            c.username,
            c.name,
            c.party,
            t.tweet_text,
            t.tweet_date,
            CASE WHEN t.is_retweet = 1 THEN 'YES' ELSE 'NO' END as is_retweet,
            t.retweet_from,
            t.likes,
            t.replies,
            t.retweets,
            t.views,
            t.created_at
        FROM tweets t
        JOIN councilors c ON t.username = c.username
        ORDER BY c.username, t.tweet_date DESC
    """)

    tweets = cursor.fetchall()

    # Write to CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            "Username",
            "Name",
            "Party",
            "Tweet Text",
            "Tweet Date (Twitter)",
            "Is Retweet",
            "Retweet From",
            "Likes",
            "Replies",
            "Retweets",
            "Views",  # NEW
            "Saved Date"
        ])
        writer.writerows(tweets)

    print(f"✅ Full CSV exported: {output_file}")
    print(f"   {len(tweets)} tweets with views metadata\n")

    conn.close()
    return len(tweets)


def export_statistics(output_file="tweets_statistics_v3_2.csv"):
    """Export per-user statistics with views"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            c.username,
            c.name,
            c.party,
            COUNT(t.id) as total_tweets,
            SUM(CASE WHEN t.is_retweet = 1 THEN 1 ELSE 0 END) as retweet_count,
            COUNT(t.id) - SUM(CASE WHEN t.is_retweet = 1 THEN 1 ELSE 0 END) as original_count,
            COALESCE(SUM(t.likes), 0) as total_likes,
            COALESCE(SUM(t.replies), 0) as total_replies,
            COALESCE(SUM(t.retweets), 0) as total_retweets,
            COALESCE(SUM(t.views), 0) as total_views,
            COALESCE(AVG(t.views), 0) as avg_views_per_tweet
        FROM councilors c
        LEFT JOIN tweets t ON c.username = t.username
        GROUP BY c.username
        ORDER BY total_tweets DESC
    """)

    stats = cursor.fetchall()

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            "Username",
            "Name",
            "Party",
            "Total Tweets",
            "Retweets",
            "Original",
            "Total Likes",
            "Total Replies",
            "Total Retweets",
            "Total Views",  # NEW
            "Avg Views/Tweet"  # NEW
        ])
        writer.writerows(stats)

    print(f"✅ Statistics CSV exported: {output_file}")
    print(f"   {len(stats)} users\n")

    conn.close()
    return len(stats)


def export_rt_analysis(output_file="rt_analysis_v3_2.csv"):
    """Detailed RT analysis - who retweets whom"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            c.username as retweeter,
            c.name as retweeter_name,
            c.party as retweeter_party,
            t.retweet_from as original_author,
            t.tweet_text,
            t.tweet_date,
            t.likes,
            t.replies,
            t.retweets as retweet_count,
            t.views
        FROM tweets t
        JOIN councilors c ON t.username = c.username
        WHERE t.is_retweet = 1
        ORDER BY c.username, t.tweet_date DESC
    """)

    rts = cursor.fetchall()

    if rts:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "Retweeter Username",
                "Retweeter Name",
                "Retweeter Party",
                "Original Author",
                "Tweet Text",
                "Date",
                "Likes",
                "Replies",
                "Retweets",
                "Views"
            ])
            writer.writerows(rts)

        print(f"✅ RT Analysis exported: {output_file}")
        print(f"   {len(rts)} retweets analyzed\n")
    else:
        print(f"⚠️  No retweets found (skipping RT analysis)\n")

    conn.close()
    return len(rts)


def show_summary():
    """Display database summary with views"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("\n" + "=" * 70)
    print("📊 DATABASE SUMMARY (v3.2 with Views)")
    print("=" * 70 + "\n")

    # Total stats
    cursor.execute("SELECT COUNT(*) FROM councilors")
    total_councilors = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tweets")
    total_tweets = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tweets WHERE is_retweet = 1")
    total_rts = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(likes), 0) FROM tweets")
    total_likes = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(replies), 0) FROM tweets")
    total_replies = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(retweets), 0) FROM tweets")
    total_retweet_count = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(views), 0) FROM tweets")
    total_views = cursor.fetchone()[0]

    print(f"📈 General Statistics:")
    print(f"   Total Councilors: {total_councilors}")
    print(f"   Total Tweets: {total_tweets}")
    print(f"   ├─ Retweets: {total_rts} ({total_rts/total_tweets*100:.1f}%)" if total_tweets > 0 else "   ├─ Retweets: 0")
    print(f"   └─ Original: {total_tweets - total_rts}")
    print()
    print(f"💬 Engagement:")
    print(f"   Total Likes: {total_likes:,}")
    print(f"   Total Replies: {total_replies:,}")
    print(f"   Total Retweets: {total_retweet_count:,}")
    print(f"   👁️ Total Views: {total_views:,}")
    print(f"   Avg Views/Tweet: {total_views/total_tweets:,.0f}" if total_tweets > 0 else "   Avg Views/Tweet: 0")

    # Top 5 by views
    print(f"\n🏆 Top 5 Users by Total Views:")
    cursor.execute("""
        SELECT 
            c.username,
            c.name,
            COUNT(t.id) as tweet_count,
            COALESCE(SUM(t.views), 0) as total_views
        FROM councilors c
        LEFT JOIN tweets t ON c.username = t.username
        GROUP BY c.username
        ORDER BY total_views DESC
        LIMIT 5
    """)

    for i, row in enumerate(cursor.fetchall(), 1):
        username, name, tweet_count, views = row
        print(f"   {i}. @{username:20s} - {views:>10,} views ({tweet_count} tweets)")

    print("\n" + "=" * 70 + "\n")

    conn.close()


def main():
    """Main export workflow"""
    print("\n" + "=" * 70)
    print("📊 CSV EXPORT v3.2 - Enhanced with Views")
    print("=" * 70 + "\n")

    # Show summary first
    show_summary()

    # Export all data
    print("💾 Exporting data...")
    print()

    total_tweets = export_all_tweets()
    total_users = export_statistics()
    total_rts = export_rt_analysis()

    print("=" * 70)
    print("✅ EXPORT COMPLETE")
    print("=" * 70)
    print(f"\n📁 Generated Files:")
    print(f"   1. tweets_export_v3_2.csv - {total_tweets} tweets (with views)")
    print(f"   2. tweets_statistics_v3_2.csv - {total_users} users")
    if total_rts > 0:
        print(f"   3. rt_analysis_v3_2.csv - {total_rts} retweets")
    print()


if __name__ == "__main__":
    main()