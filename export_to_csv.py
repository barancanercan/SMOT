#!/usr/bin/env python3
"""
📤 Export Database to CSV
- Tweets with full metadata
- Quality check
- Missing data detection
"""

import sqlite3
import csv
from pathlib import Path
from datetime import datetime

DB_PATH = "meclis.db"
CSV_OUTPUT = "tweets_export.csv"

def export_to_csv():
    """Export all tweets to CSV with metadata"""
    
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
            t.is_retweet,
            t.retweet_from,
            t.likes,
            t.replies,
            t.retweets,
            t.engagement_score,
            t.created_at,
            t.is_deleted
        FROM tweets t
        JOIN councilors c ON t.username = c.username
        ORDER BY c.username, t.tweet_date DESC
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        print("❌ No tweets found in database")
        return
    
    # Write to CSV
    with open(CSV_OUTPUT, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Headers
        writer.writerow([
            'Username',
            'Name',
            'Party',
            'Tweet Text',
            'Tweet Date (Twitter)',
            'Is Retweet',
            'Retweet From',
            'Likes',
            'Replies',
            'Retweets',
            'Engagement Score',
            'Saved Date',
            'Is Deleted'
        ])
        
        # Data
        writer.writerows(rows)
    
    print(f"✅ Exported {len(rows)} tweets to {CSV_OUTPUT}")
    return rows

def quality_check(rows):
    """Check for missing or invalid data"""
    
    print("\n" + "=" * 70)
    print("🔍 QUALITY CHECK - Missing Data Analysis")
    print("=" * 70 + "\n")
    
    issues = {
        "missing_username": 0,
        "missing_name": 0,
        "missing_party": 0,
        "missing_tweet_text": 0,
        "missing_tweet_date": 0,
        "missing_engagement": 0,
        "deleted_tweets": 0,
        "short_tweets": 0,
        "invalid_dates": 0
    }
    
    tweet_lengths = []
    engagement_scores = []
    dates_ok = 0
    dates_bad = 0
    
    for row in rows:
        username, name, party, text, date, is_rt, rt_from, likes, replies, retweets, score, saved, is_deleted = row
        
        # Check missing fields
        if not username:
            issues["missing_username"] += 1
        if not name:
            issues["missing_name"] += 1
        if not party:
            issues["missing_party"] += 1
        if not text or len(text) < 5:
            issues["missing_tweet_text"] += 1
            issues["short_tweets"] += 1
        if not date:
            issues["missing_tweet_date"] += 1
        
        # Check engagement
        if likes is None or replies is None or retweets is None:
            issues["missing_engagement"] += 1
        
        # Check deleted
        if is_deleted:
            issues["deleted_tweets"] += 1
        
        # Collect stats
        if text:
            tweet_lengths.append(len(text))
        
        if score is not None:
            engagement_scores.append(score)
        
        # Validate date format
        if date:
            try:
                datetime.fromisoformat(date.replace('Z', '+00:00'))
                dates_ok += 1
            except:
                issues["invalid_dates"] += 1
                dates_bad += 1
    
    # Print issues
    print("⚠️  ISSUES FOUND:")
    print()
    
    for issue, count in issues.items():
        if count > 0:
            status = "❌" if count > 10 else "⚠️ "
            print(f"{status} {issue}: {count} tweets")
        else:
            print(f"✅ {issue}: 0")
    
    print(f"\n📅 DATE VALIDATION:")
    print(f"   ✅ Valid dates: {dates_ok}")
    print(f"   ❌ Invalid dates: {dates_bad}")
    
    print(f"\n📝 TWEET LENGTH STATS:")
    if tweet_lengths:
        print(f"   Min: {min(tweet_lengths)} chars")
        print(f"   Max: {max(tweet_lengths)} chars")
        print(f"   Avg: {sum(tweet_lengths)/len(tweet_lengths):.0f} chars")
    
    print(f"\n💬 ENGAGEMENT STATS:")
    if engagement_scores:
        print(f"   Min score: {min(engagement_scores):.2f}")
        print(f"   Max score: {max(engagement_scores):.2f}")
        print(f"   Avg score: {sum(engagement_scores)/len(engagement_scores):.2f}")
    
    print(f"\n📊 SUMMARY:")
    total_issues = sum(issues.values())
    issue_rate = (total_issues / (len(rows) * 13)) * 100  # 13 fields per row
    
    print(f"   Total rows: {len(rows)}")
    print(f"   Total issues: {total_issues}")
    print(f"   Issue rate: {issue_rate:.2f}%")
    
    if issue_rate < 5:
        print(f"\n✅ DATA QUALITY: EXCELLENT (< 5% issues)")
    elif issue_rate < 15:
        print(f"\n⚠️  DATA QUALITY: GOOD (5-15% issues)")
    else:
        print(f"\n❌ DATA QUALITY: NEEDS IMPROVEMENT (> 15% issues)")
    
    print("\n" + "=" * 70)

def sample_rows(rows):
    """Show sample tweets"""
    print("\n📝 SAMPLE TWEETS:")
    print("=" * 70 + "\n")
    
    for i, row in enumerate(rows[:5], 1):
        username, name, party, text, date, is_rt, rt_from, likes, replies, retweets, score, saved, is_deleted = row
        
        rt_label = f" [RT from @{rt_from}]" if is_rt else ""
        deleted_label = " [DELETED]" if is_deleted else ""
        
        print(f"Tweet {i}:")
        print(f"  👤 @{username} ({name})")
        print(f"  🏛️  {party}")
        print(f"  📝 {text[:100]}...{rt_label}{deleted_label}")
        print(f"  📅 {date}")
        print(f"  💬 Likes: {likes}, Replies: {replies}, RTs: {retweets}, Score: {score:.2f}")
        print()

if __name__ == "__main__":
    print("📤 DATABASE → CSV EXPORT\n")
    
    # Export
    rows = export_to_csv()
    
    if rows:
        # Sample
        sample_rows(rows)
        
        # Quality check
        quality_check(rows)
        
        print(f"\n✅ CSV file saved: {CSV_OUTPUT}")
        print(f"📊 Ready to inspect in Excel or text editor\n")

