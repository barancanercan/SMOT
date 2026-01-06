#!/usr/bin/env python3
"""
🧪 SPRINT GÜN 1 - SIMPLIFIED TEST (No external dependencies required)
CSV parsing, Database init, Basic verification
"""

import sqlite3
import csv
from pathlib import Path


def print_header(title):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def step1_chrome_fix_check():
    """✅ STEP 1: Chrome Fix Verification"""
    print_header("STEP 1: CHROME FIX VERIFICATION")

    print("📋 Checking x_scraper.py for headless detection...\n")

    try:
        with open('x_scraper.py', 'r') as f:
            content = f.read()

        checks = {
            "headless=None": "headless=None" in content,
            "GUI detection": "os.environ.get('DISPLAY')" in content,
            "Auto headless": "--headless=new" in content,
            "Fallback logic": "if self.headless:" in content,
        }

        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"{status} {check}")

        all_passed = all(checks.values())
        print(f"\n{'✅ All checks passed!' if all_passed else '❌ Some checks failed'}")
        return all_passed

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def step2_csv_parsing():
    """✅ STEP 2: CSV Parsing"""
    print_header("STEP 2: CSV PARSING")

    try:
        csv_path = "data.csv"

        if not Path(csv_path).exists():
            print(f"❌ {csv_path} not found")
            return False

        councilors = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                username = row['link'].split('/')[-1].replace('@', '').strip()
                councilors.append({
                    'username': username,
                    'name': row['Meclis Üyesi'],
                    'party': row['Parti'],
                    'district': row['İlçe']
                })

        print(f"✅ CSV loaded: {csv_path}")
        print(f"   Rows: {len(councilors)}")
        print(f"\n📋 Councilors:")

        # Red Team (CHP)
        red = [c for c in councilors if 'Cumhuriyet' in c['party']]
        print(f"   🔴 Red Team (CHP): {len(red)}")
        for c in red[:3]:
            print(f"      • @{c['username']:20s} - {c['name']}")

        # Green Team (AKP)
        green = [c for c in councilors if 'Adalet' in c['party']]
        print(f"\n   🟢 Green Team (AKP): {len(green)}")
        for c in green[:3]:
            print(f"      • @{c['username']:20s} - {c['name']}")

        return councilors

    except Exception as e:
        print(f"❌ CSV Error: {e}")
        return False


def step3_database_init(councilors):
    """✅ STEP 3: Database Initialization"""
    print_header("STEP 3: DATABASE INITIALIZATION")

    db_path = "meclis.db"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create tables
        print("🔨 Creating schema...\n")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS councilors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                name TEXT,
                party TEXT,
                district TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("   ✅ councilors table")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tweets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                tweet_text TEXT NOT NULL,
                tweet_date TEXT,
                is_retweet BOOLEAN DEFAULT 0,
                retweet_from TEXT,
                likes INTEGER DEFAULT 0,
                replies INTEGER DEFAULT 0,
                retweets INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (username) REFERENCES councilors(username)
            )
        """)
        print("   ✅ tweets table")

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tweets_username ON tweets(username)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tweets_date ON tweets(tweet_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tweets_retweet ON tweets(is_retweet)")
        print("   ✅ indexes created")

        # Load councilors
        print(f"\n💾 Loading {len(councilors)} councilors...\n")

        for c in councilors:
            cursor.execute(
                "INSERT OR REPLACE INTO councilors (username, name, party, district) VALUES (?, ?, ?, ?)",
                (c['username'], c['name'], c['party'], c['district'])
            )

        conn.commit()
        print(f"   ✅ {len(councilors)} councilors inserted")

        # Verify
        cursor.execute("SELECT COUNT(*) FROM councilors")
        count = cursor.fetchone()[0]
        print(f"\n✅ Database initialized: {db_path}")
        print(f"   Total councilors: {count}")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ Database Error: {e}")
        return False


def step4_mock_tweet_insert():
    """✅ STEP 4: Mock Tweet Insert Test"""
    print_header("STEP 4: MOCK TWEET INSERT & VERIFICATION")

    db_path = "meclis.db"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Mock tweets for abbas_atamer
        test_username = "abbas_atamer"
        mock_tweets = [
            {
                "text": "Ankara'nın sosyal politikaları çok önemli. Halkımız için çalışmaya devam edeceğiz.",
                "timestamp": "2025-01-05T14:30:00+00:00",
                "is_retweet": False,
                "retweet_from": None,
                "likes": 45,
                "replies": 3,
                "retweets": 12,
            },
            {
                "text": "RT @ankara_harita: Ankara'nın önemli infrastruktur projeleri bu yıl hızlanacak",
                "timestamp": "2025-01-04T10:15:00+00:00",
                "is_retweet": True,
                "retweet_from": "ankara_harita",
                "likes": 120,
                "replies": 8,
                "retweets": 34,
            },
            {
                "text": "Emeği geçen herkese teşekkür ederim. Ankara'nın gelişimi hepimizin sorumluluğu.",
                "timestamp": "2025-01-03T16:45:00+00:00",
                "is_retweet": False,
                "retweet_from": None,
                "likes": 67,
                "replies": 5,
                "retweets": 18,
            }
        ]

        print(f"🐦 Inserting mock tweets for @{test_username}...\n")

        # Clear old tweets
        cursor.execute("DELETE FROM tweets WHERE username = ?", (test_username,))

        # Insert mock tweets
        for tweet in mock_tweets:
            cursor.execute(
                """INSERT INTO tweets 
                   (username, tweet_text, tweet_date, is_retweet, retweet_from, likes, replies, retweets)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    test_username,
                    tweet['text'],
                    tweet['timestamp'],
                    tweet['is_retweet'],
                    tweet['retweet_from'],
                    tweet['likes'],
                    tweet['replies'],
                    tweet['retweets']
                )
            )

        conn.commit()

        print(f"✅ {len(mock_tweets)} mock tweets inserted")
        print(f"\n📝 Sample tweets:\n")

        for i, tweet in enumerate(mock_tweets, 1):
            is_rt = "🔄 RT" if tweet['is_retweet'] else "✍️  Original"
            text = tweet['text'][:60] + "..." if len(tweet['text']) > 60 else tweet['text']
            likes = tweet['likes']
            print(f"{i}. {is_rt} | ❤️ {likes}")
            print(f"   {text}\n")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ Mock Insert Error: {e}")
        return False


def step5_verification():
    """✅ STEP 5: Database Verification"""
    print_header("STEP 5: DATABASE VERIFICATION")

    db_path = "meclis.db"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check councilors
        cursor.execute("SELECT COUNT(*) FROM councilors")
        councilors_count = cursor.fetchone()[0]

        # Check tweets
        cursor.execute("SELECT COUNT(*) FROM tweets")
        tweets_count = cursor.fetchone()[0]

        # Check by party
        cursor.execute("""
            SELECT party, COUNT(*) 
            FROM councilors 
            GROUP BY party
        """)
        party_counts = cursor.fetchall()

        # Check tweets stats
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN is_retweet = 1 THEN 1 ELSE 0 END) as retweets,
                SUM(likes) as total_likes
            FROM tweets
        """)
        tweet_stats = cursor.fetchone()

        print("📊 Database Status:\n")
        print(f"   Councilors: {councilors_count}")
        print(f"   By party:")
        for party, count in party_counts:
            print(f"      • {party}: {count}")

        print(f"\n   Tweets: {tweets_count}")
        if tweet_stats[0]:
            print(f"      • Total: {tweet_stats[0]}")
            print(f"      • Retweets: {tweet_stats[1]}")
            print(f"      • Original: {tweet_stats[0] - (tweet_stats[1] or 0)}")
            print(f"      • Total Likes: {tweet_stats[2] or 0}")

        # List all tables
        print("\n📋 Tables:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        for table in cursor.fetchall():
            print(f"      • {table[0]}")

        # List all indexes
        print("\n🔑 Indexes:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx%'")
        for idx in cursor.fetchall():
            print(f"      • {idx[0]}")

        conn.close()

        print(f"\n✅ Database verification: OK")
        print(f"   Database file: {db_path}")
        print(f"   Size: {Path(db_path).stat().st_size / 1024:.1f} KB")

        return True

    except Exception as e:
        print(f"❌ Verification Error: {e}")
        return False


def main():
    """Main test flow"""
    print("\n" + "=" * 70)
    print("  🏛️ MECLIS İSTİHBARAT SİSTEMİ - GÜN 1")
    print("  Sprint Test | Chrome Fix + CSV + Database")
    print("=" * 70)

    results = {}

    # Step 1: Chrome fix check
    results['chrome_fix'] = step1_chrome_fix_check()

    # Step 2: CSV parsing
    councilors = step2_csv_parsing()
    results['csv_parsing'] = councilors is not False and len(councilors) > 0

    # Step 3: Database init
    if councilors:
        results['db_init'] = step3_database_init(councilors)
    else:
        results['db_init'] = False

    # Step 4: Mock insert
    if results['db_init']:
        results['mock_insert'] = step4_mock_tweet_insert()
    else:
        results['mock_insert'] = False

    # Step 5: Verification
    if results['db_init']:
        results['verification'] = step5_verification()
    else:
        results['verification'] = False

    # Summary
    print_header("📋 TEST SUMMARY")

    for step, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        step_name = step.replace('_', ' ').title()
        print(f"{status}  {step_name}")

    total = sum(results.values())
    print(f"\n📊 Results: {total}/{len(results)} tests passed\n")

    if total == len(results):
        print("🎉 ALL TESTS PASSED!")
        print("\n✅ Completed:")
        print("   1. Chrome headless detection ✅")
        print("   2. CSV → councilors loading ✅")
        print("   3. Database initialization ✅")
        print("   4. Mock tweets insertion ✅")
        print("   5. Database verification ✅")
        print("\n➡️  Next steps:")
        print("   • Real @abbas_atamer scrape (when headless works)")
        print("   • Migrate all 13 councilors")
        print("   • Test LLM analysis pipeline")
    else:
        print("⚠️  Some tests failed. Review output above.")

    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()