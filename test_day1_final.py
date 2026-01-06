#!/usr/bin/env python3
"""DAY 1 TEST - MOCK MODE (No Chrome)"""

import os
import sys
import sqlite3
import pandas as pd
from mock_scraper import MockTwitterScraper

print("\n" + "="*70)
print("🧪 DAY 1 TEST SUITE - MOCK MODE")
print("="*70 + "\n")

# TEST 1: CSV
print("[TEST 1] CSV Parsing...")
try:
    df = pd.read_csv("data/data.csv")
    usernames = []
    for _, row in df.iterrows():
        link = str(row.get("link", "")).strip()
        if "x.com/" in link:
            username = link.split("x.com/")[-1].strip("/").replace("@", "")
            usernames.append(username)
    
    assert len(df) == 13
    assert len(usernames) == 13
    
    print(f"  ✅ PASS: {len(df)} rows, {len(usernames)} usernames\n")
except Exception as e:
    print(f"  ❌ FAIL: {e}\n")
    sys.exit(1)

# TEST 2: MOCK SCRAPER
print("[TEST 2] Mock Scraper...")
try:
    scraper = MockTwitterScraper()
    
    # Single user
    tweets = scraper.scrape_tweets("abbas_atamer")
    assert len(tweets) == 3
    assert tweets[0]["username"] == "abbas_atamer"
    print(f"  ✅ PASS: Single user returned {len(tweets)} tweets")
    
    # Multiple users
    results = scraper.scrape_multiple(["abbas_atamer", "atila_celik06", "cihanayhan85"])
    assert len(results) == 3
    total = sum(len(t) for t in results.values())
    print(f"  ✅ PASS: Multiple users returned {total} tweets\n")
except Exception as e:
    print(f"  ❌ FAIL: {e}\n")
    sys.exit(1)

# TEST 3: DATABASE
print("[TEST 3] Database...")
try:
    db_path = "test_temp.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE councilors (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            name TEXT,
            party TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE tweets (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            tweet_text TEXT NOT NULL,
            tweet_date TEXT,
            likes INTEGER DEFAULT 0
        )
    """)
    
    conn.commit()
    
    # Insert
    cursor.execute(
        "INSERT INTO councilors (username, name, party) VALUES (?, ?, ?)",
        ("abbas_atamer", "Abbas ATAMER", "CHP")
    )
    cursor.execute(
        "INSERT INTO tweets (username, tweet_text, tweet_date, likes) VALUES (?, ?, ?, ?)",
        ("abbas_atamer", "Test tweet", "2025-01-06T10:00:00Z", 10)
    )
    conn.commit()
    
    cursor.execute("SELECT COUNT(*) FROM councilors")
    council = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM tweets")
    tweets = cursor.fetchone()[0]
    
    assert council == 1
    assert tweets == 1
    
    print(f"  ✅ PASS: {council} councilor, {tweets} tweet inserted\n")
    
    conn.close()
    os.remove(db_path)
except Exception as e:
    print(f"  ❌ FAIL: {e}\n")
    sys.exit(1)

print("="*70)
print("✅ ALL 3 TESTS PASSED!")
print("="*70)
print("""
DAY 1 COMPLETE:
  ✅ CSV parsing (13 members)
  ✅ Mock scraper (9 tweets)
  ✅ Database (insert/query)
  
Ready for DAY 2: Real X scraping + LLM
""")
print("="*70 + "\n")
