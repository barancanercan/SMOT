#!/usr/bin/env python3
"""
📅 COMPREHENSIVE DATE VALIDATOR v2.0
✅ Analyze ALL 599 tweets
✅ Check date ranges
✅ Monthly distribution
✅ Party-based analysis
✅ User-based stats
"""

import sqlite3
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from typing import List, Dict, Tuple

DB_PATH = "meclis.db"
DAYS_BACK = 90


def parse_tweet_date(date_str: str) -> datetime:
    """Parse ISO format date from database"""
    try:
        if not date_str:
            return None

        if date_str.endswith('Z'):
            date_str = date_str.replace('Z', '+00:00')

        return datetime.fromisoformat(date_str)
    except Exception as e:
        return None


def get_all_tweets() -> List[Dict]:
    """Get ALL tweets from database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            t.id,
            t.username,
            c.name,
            c.party,
            t.tweet_text,
            t.tweet_date,
            t.is_retweet,
            t.retweet_from,
            t.likes,
            t.replies,
            t.retweets,
            t.views,
            t.created_at
        FROM tweets t
        JOIN councilors c ON t.username = c.username
        ORDER BY t.tweet_date ASC
    """)

    rows = cursor.fetchall()
    conn.close()

    tweets = []
    for row in rows:
        tweets.append({
            "id": row[0],
            "username": row[1],
            "name": row[2],
            "party": row[3],
            "text": row[4],
            "tweet_date": row[5],
            "is_retweet": row[6],
            "retweet_from": row[7],
            "likes": row[8],
            "replies": row[9],
            "retweets": row[10],
            "views": row[11],
            "created_at": row[12]
        })

    return tweets


def validate_all_tweets(tweets: List[Dict], days_back: int = 90) -> Dict:
    """Validate ALL tweets"""
    now = datetime.now(timezone.utc)
    cutoff_date = now - timedelta(days=days_back)

    results = {
        "total": len(tweets),
        "valid": [],
        "invalid": [],
        "no_date": [],
        "by_month": defaultdict(int),
        "by_party": defaultdict(lambda: {"valid": 0, "invalid": 0}),
        "by_user": defaultdict(lambda: {"valid": 0, "invalid": 0, "party": ""}),
        "oldest_date": None,
        "newest_date": None,
        "date_span_days": 0,
    }

    for tweet in tweets:
        tweet_date_str = tweet.get("tweet_date")
        tweet_date = parse_tweet_date(tweet_date_str)
        party = tweet.get("party", "Unknown")
        username = tweet.get("username")

        # Store party info
        results["by_user"][username]["party"] = party

        if not tweet_date:
            results["no_date"].append(tweet)
            continue

        # Track date range
        if not results["oldest_date"] or tweet_date < results["oldest_date"]:
            results["oldest_date"] = tweet_date
        if not results["newest_date"] or tweet_date > results["newest_date"]:
            results["newest_date"] = tweet_date

        # Check if in range
        is_valid = tweet_date >= cutoff_date

        if is_valid:
            results["valid"].append({
                **tweet,
                "parsed_date": tweet_date
            })
            results["by_party"][party]["valid"] += 1
            results["by_user"][username]["valid"] += 1

            # Monthly distribution
            month_key = tweet_date.strftime("%Y-%m")
            results["by_month"][month_key] += 1
        else:
            results["invalid"].append({
                **tweet,
                "parsed_date": tweet_date,
                "days_old": (now - tweet_date).days
            })
            results["by_party"][party]["invalid"] += 1
            results["by_user"][username]["invalid"] += 1

    # Calculate date span
    if results["oldest_date"] and results["newest_date"]:
        results["date_span_days"] = (results["newest_date"] - results["oldest_date"]).days

    return results


def print_section_header(title: str):
    """Print formatted section header"""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80 + "\n")


def main():
    """Main validation workflow"""
    print_section_header("📅 COMPREHENSIVE DATE VALIDATOR v2.0 - ALL TWEETS")

    # Get cutoff info
    now = datetime.now(timezone.utc)
    cutoff_date = now - timedelta(days=DAYS_BACK)

    print(f"🎯 TIME WINDOW:")
    print(f"   Cutoff Date: {cutoff_date.strftime('%Y-%m-%d %H:%M')} ({DAYS_BACK} days ago)")
    print(f"   Today: {now.strftime('%Y-%m-%d %H:%M')}")

    # Load all tweets
    print(f"\n📥 Loading all tweets from database...")
    tweets = get_all_tweets()
    print(f"✅ Loaded {len(tweets)} tweets")

    # Validate all
    print(f"\n⏳ Validating all {len(tweets)} tweets...")
    results = validate_all_tweets(tweets, DAYS_BACK)

    # ==========================================
    # SECTION 1: OVERALL SUMMARY
    # ==========================================
    print_section_header("📊 OVERALL VALIDATION SUMMARY")

    valid_count = len(results["valid"])
    invalid_count = len(results["invalid"])
    no_date_count = len(results["no_date"])

    print(f"📈 Results:")
    print(f"   Total Tweets: {results['total']}")
    print(f"   ✅ Valid (within {DAYS_BACK} days): {valid_count} ({valid_count / results['total'] * 100:.1f}%)")
    print(f"   ❌ Invalid (outside {DAYS_BACK} days): {invalid_count} ({invalid_count / results['total'] * 100:.1f}%)")
    print(f"   ⚠️  No Date: {no_date_count} ({no_date_count / results['total'] * 100:.1f}%)")

    if results["oldest_date"]:
        print(f"\n📅 Date Range in Database:")
        print(f"   Oldest: {results['oldest_date'].strftime('%Y-%m-%d %H:%M')}")
        print(f"   Newest: {results['newest_date'].strftime('%Y-%m-%d %H:%M')}")
        print(f"   Span: {results['date_span_days']} days")

    # ==========================================
    # SECTION 2: MONTHLY DISTRIBUTION
    # ==========================================
    print_section_header("📅 MONTHLY DISTRIBUTION")

    if results["by_month"]:
        sorted_months = sorted(results["by_month"].items())

        print("📊 Tweets by Month:")
        for month, count in sorted_months:
            # Parse month
            month_date = datetime.strptime(month, "%Y-%m")
            month_name = month_date.strftime("%B %Y")

            # Visual bar
            bar_length = int(count / max(results["by_month"].values()) * 40)
            bar = "█" * bar_length

            print(f"   {month_name:20s} │ {bar} {count:3d} tweets")
    else:
        print("⚠️  No monthly data available")

    # ==========================================
    # SECTION 3: PARTY-BASED ANALYSIS
    # ==========================================
    print_section_header("🏛️ PARTY-BASED ANALYSIS")

    if results["by_party"]:
        print("📊 Tweets by Party:\n")

        # Sort by total tweets
        party_totals = {
            party: stats["valid"] + stats["invalid"]
            for party, stats in results["by_party"].items()
        }
        sorted_parties = sorted(party_totals.items(), key=lambda x: x[1], reverse=True)

        for party, _ in sorted_parties:
            stats = results["by_party"][party]
            total = stats["valid"] + stats["invalid"]
            valid_pct = stats["valid"] / total * 100 if total > 0 else 0

            print(f"   {party:35s}")
            print(
                f"      Total: {total:3d} | ✅ Valid: {stats['valid']:3d} ({valid_pct:.1f}%) | ❌ Invalid: {stats['invalid']:3d}")

    # ==========================================
    # SECTION 4: USER-BASED ANALYSIS
    # ==========================================
    print_section_header("👤 USER-BASED ANALYSIS")

    if results["by_user"]:
        print("📊 Tweets by User:\n")

        # Sort by total tweets
        user_totals = {
            user: stats["valid"] + stats["invalid"]
            for user, stats in results["by_user"].items()
        }
        sorted_users = sorted(user_totals.items(), key=lambda x: x[1], reverse=True)

        for username, _ in sorted_users:
            stats = results["by_user"][username]
            total = stats["valid"] + stats["invalid"]
            valid_pct = stats["valid"] / total * 100 if total > 0 else 0
            party = stats["party"]

            party_short = "CHP" if "Cumhuriyet" in party else "AKP"

            print(f"   @{username:20s} [{party_short}]")
            print(
                f"      Total: {total:3d} | ✅ Valid: {stats['valid']:3d} ({valid_pct:.1f}%) | ❌ Invalid: {stats['invalid']:3d}")

    # ==========================================
    # SECTION 5: INVALID TWEETS (if any)
    # ==========================================
    if results["invalid"]:
        print_section_header("❌ INVALID TWEETS (Outside 90-Day Window)")

        print(f"⚠️  Found {len(results['invalid'])} tweets outside the time window:\n")

        for i, tweet in enumerate(results["invalid"][:10], 1):  # Show first 10
            date_str = tweet["parsed_date"].strftime("%Y-%m-%d %H:%M")
            days_old = tweet["days_old"]

            rt_label = " [RT]" if tweet["is_retweet"] else ""
            text_preview = tweet["text"][:60] + "..." if len(tweet["text"]) > 60 else tweet["text"]

            print(f"   {i}. 📅 {date_str} ({days_old} days old)")
            print(f"      @{tweet['username']} [{tweet['party'][:10]}]")
            print(f"      {text_preview}{rt_label}\n")

        if len(results["invalid"]) > 10:
            print(f"   ... +{len(results['invalid']) - 10} more invalid tweets")

    # ==========================================
    # SECTION 6: SAMPLE VALID TWEETS
    # ==========================================
    print_section_header("✅ SAMPLE VALID TWEETS")

    if results["valid"]:
        print("📝 First 5 Valid Tweets (Oldest):\n")

        for i, tweet in enumerate(results["valid"][:5], 1):
            date_str = tweet["parsed_date"].strftime("%Y-%m-%d %H:%M")
            rt_label = " [RT]" if tweet["is_retweet"] else ""
            text_preview = tweet["text"][:60] + "..." if len(tweet["text"]) > 60 else tweet["text"]

            print(f"   {i}. 📅 {date_str}")
            print(f"      @{tweet['username']} [{tweet['party'][:10]}]")
            print(f"      {text_preview}{rt_label}\n")

        print("\n📝 Last 5 Valid Tweets (Newest):\n")

        for i, tweet in enumerate(results["valid"][-5:], 1):
            date_str = tweet["parsed_date"].strftime("%Y-%m-%d %H:%M")
            rt_label = " [RT]" if tweet["is_retweet"] else ""
            text_preview = tweet["text"][:60] + "..." if len(tweet["text"]) > 60 else tweet["text"]

            print(f"   {i}. 📅 {date_str}")
            print(f"      @{tweet['username']} [{tweet['party'][:10]}]")
            print(f"      {text_preview}{rt_label}\n")

    # ==========================================
    # SECTION 7: FINAL VERDICT
    # ==========================================
    print_section_header("🎯 FINAL VERDICT")

    if invalid_count == 0 and no_date_count == 0:
        print("✅ VALIDATION PASSED!")
        print(f"   All {valid_count} tweets are within the {DAYS_BACK}-day window.")
        print("   Date filtering is working correctly.")
        print("\n   🚀 Ready for LLM analysis!")
    elif invalid_count == 0 and no_date_count > 0:
        print("⚠️  VALIDATION WARNING!")
        print(f"   {no_date_count} tweets have no date information.")
        print("   However, all dated tweets are within the time window.")
        print("\n   ✅ Can proceed with LLM analysis (use dated tweets only)")
    else:
        print("❌ VALIDATION FAILED!")
        print(f"   {invalid_count} tweets found outside the {DAYS_BACK}-day window.")
        print("   Scraper date filtering is NOT working correctly.")
        print("\n   🔧 ACTION REQUIRED:")
        print("      1. Check x_scraper.py date filtering logic")
        print("      2. Re-scrape with fixed scraper")
        print("      3. Run validation again")

    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()