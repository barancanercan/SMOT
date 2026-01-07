#!/usr/bin/env python3
"""
🐦 Scraper Worker v3.1 - With improved rate limiting
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict
import time
import random

from x_scraper import XTwitterScraper
from models.database import (
    init_database, load_councilors, save_tweets, get_stats, 
    get_connection
)


def load_data_csv(csv_path: str = "data/data.csv") -> List[Dict]:
    """Load councilor data from CSV"""
    try:
        df = pd.read_csv(csv_path)
        councilors = []
        
        for _, row in df.iterrows():
            link = str(row.get("link", "")).strip()
            username = link.split("x.com/")[-1].strip("/").replace("@", "") if link else ""
            
            if username:
                councilors.append({
                    "username": username,
                    "name": row.get("Meclis Üyesi", ""),
                    "party": row.get("Parti", ""),
                    "district": row.get("İlçe", "")
                })
        
        return councilors
    except Exception as e:
        print(f"❌ CSV Error: {e}")
        return []


def detect_retweet(tweet_text: str) -> tuple:
    """Improved RT detection"""
    if not tweet_text:
        return False, None
    
    text = tweet_text.strip()
    
    if text.startswith("RT @"):
        try:
            rt_part = text.split(":")[0]
            rt_from = rt_part.replace("RT", "").replace("@", "").strip()
            return True, rt_from if rt_from else None
        except:
            pass
    
    if "X reposted" in text or "[X reposted]" in text:
        return True, None
    
    if text.startswith("Quote") or "originally posted" in text.lower():
        return True, None
    
    return False, None


def enhanced_tweet_extraction(raw_tweets: List[Dict]) -> List[Dict]:
    """Process raw tweets with RT detection"""
    processed = []
    
    for tweet in raw_tweets:
        text = (tweet.get('text', '') or '').strip()
        if not text or len(text) < 5:
            continue
        
        is_rt, rt_from = detect_retweet(text)
        
        processed.append({
            'text': text,
            'timestamp': tweet.get('timestamp'),
            'is_retweet': is_rt,
            'retweet_from': rt_from,
            'likes': int(tweet.get('likes', 0)),
            'replies': int(tweet.get('replies', 0)),
            'retweets': int(tweet.get('retweets', 0))
        })
    
    return processed


def scrape_and_save(
    usernames: List[str],
    max_tweets: int = 100,
    days_back: int = 90
) -> Dict:
    """Main scraping pipeline with improved rate limiting"""
    
    print("\n" + "=" * 70)
    print(f"🐦 SCRAPER WORKER v3.1 - {len(usernames)} users")
    print(f"   Max tweets/user: {max_tweets}")
    print(f"   Time window: {days_back} days")
    print(f"   Rate limiting: AGGRESSIVE (10-30s delays)")
    print("=" * 70 + "\n")
    
    results = {
        "total_scraped": 0,
        "total_saved": 0,
        "total_duplicates": 0,
        "users": {}
    }
    
    try:
        scraper = XTwitterScraper(headless=False)
        
        if not scraper.driver:
            print("❌ Scraper initialization failed")
            return results
        
        for i, username in enumerate(usernames, 1):
            print(f"[{i:2d}/{len(usernames)}] @{username:20s}", end=" ", flush=True)
            
            try:
                # Scrape
                raw_tweets = scraper.scrape_tweets(
                    username,
                    max_tweets=max_tweets,
                    days_back=days_back
                )
                
                if not raw_tweets:
                    print("⚠️  No tweets")
                    results["users"][username] = {"status": "no_tweets", "count": 0}
                    # Rate limiting even for no-tweets
                    if i < len(usernames):
                        delay = random.uniform(15, 30)  # 15-30 saniye
                        print(f"   ⏳ Rate limiting: {delay:.1f}s", end="", flush=True)
                        time.sleep(delay)
                        print("\r" + " " * 50 + "\r", end="", flush=True)
                    continue
                
                # Process (RT detection)
                processed_tweets = enhanced_tweet_extraction(raw_tweets)
                
                # Save to DB
                save_result = save_tweets(username, processed_tweets)
                
                results["total_scraped"] += len(raw_tweets)
                results["total_saved"] += save_result["saved"]
                results["total_duplicates"] += save_result["duplicates"]
                
                results["users"][username] = {
                    "status": "success",
                    "scraped": len(raw_tweets),
                    "saved": save_result["saved"],
                    "duplicates": save_result["duplicates"]
                }
                
                print(f"✅ {save_result['saved']} saved")
                
                # AGGRESSIVE rate limiting between users
                if i < len(usernames):
                    delay = random.uniform(15, 30)  # 15-30 saniye X.com tarafından
                    print(f"   ⏳ Rate limiting: {delay:.1f}s", end="", flush=True)
                    
                    # Show countdown
                    for remaining in range(int(delay), 0, -1):
                        time.sleep(1)
                        if remaining % 5 == 0:
                            print(f"\r   ⏳ Rate limiting: {remaining}s   ", end="", flush=True)
                    
                    print("\r" + " " * 50 + "\r", end="", flush=True)
                    
            except KeyboardInterrupt:
                print("\n\n⚠️  User interrupted - saving partial results...")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)[:40]}")
                results["users"][username] = {"status": "error", "error": str(e)}
                # Still apply rate limiting after error
                if i < len(usernames):
                    delay = random.uniform(15, 30)
                    time.sleep(delay)
        
        scraper.close()
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
    
    return results


def print_summary(results: Dict):
    """Print summary statistics"""
    print("\n" + "=" * 70)
    print("📊 SCRAPING SUMMARY")
    print("=" * 70)
    
    print(f"\n📈 Totals:")
    print(f"   Scraped: {results['total_scraped']}")
    print(f"   Saved: {results['total_saved']}")
    print(f"   Duplicates: {results['total_duplicates']}")
    
    print(f"\n👤 By User:")
    for username, data in sorted(results['users'].items()):
        if data.get('status') == 'success':
            print(f"   ✅ @{username:20s} → {data['saved']} saved, {data['duplicates']} dup")
        else:
            print(f"   ⚠️  @{username:20s} → {data['status']}")
    
    # Database stats
    stats = get_stats()
    print(f"\n💾 Database Stats:")
    print(f"   Total Councilors: {stats['total_councilors']}")
    print(f"   Total Tweets: {stats['total_tweets']}")
    print(f"   Retweets: {stats['total_retweets']}")
    print(f"   Original: {stats['original_tweets']}")
    print(f"   Active Users: {stats['active_users']}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    init_database()
    
    councilors = load_data_csv("data/data.csv")
    if not councilors:
        print("❌ No councilors loaded")
        exit(1)
    
    print(f"\n✅ Loaded {len(councilors)} councilors")
    loaded_count = load_councilors(councilors)
    print(f"✅ {loaded_count} councilors saved to DB")
    
    usernames = [c['username'] for c in councilors]
    results = scrape_and_save(
        usernames,
        max_tweets=100,
        days_back=90
    )
    
    print_summary(results)

