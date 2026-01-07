#!/usr/bin/env python3
"""Scraper Worker v4.0 - Full Pipeline"""

import pandas as pd
from datetime import datetime
import time
import random

from x_scraper import XTwitterScraper
from models.database import load_councilors, save_tweets, get_stats

def load_data_csv(csv_path: str = "data/data.csv"):
    """Load councilor data"""
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

def scrape_and_save(usernames, max_tweets=100, days_back=90):
    """Scrape and save"""
    
    print("\n" + "=" * 70)
    print(f"🐦 SCRAPER WORKER v4.0 - {len(usernames)} users")
    print(f"   RT Detection: ADVANCED (author handle comparison)")
    print(f"   Views: ENABLED")
    print(f"   Full Metadata: YES")
    print("=" * 70 + "\n")
    
    results = {"total_scraped": 0, "total_saved": 0, "total_duplicates": 0, "users": {}}
    
    try:
        scraper = XTwitterScraper(headless=False)
        
        if not scraper.driver:
            print("❌ Scraper initialization failed")
            return results
        
        for i, username in enumerate(usernames, 1):
            print(f"[{i:2d}/{len(usernames)}] @{username:20s}", end=" ", flush=True)
            
            try:
                raw_tweets = scraper.scrape_tweets(username, max_tweets, days_back)
                
                if not raw_tweets:
                    print("⚠️  No tweets")
                    results["users"][username] = {"status": "no_tweets"}
                    continue
                
                # Save to DB
                save_result = save_tweets(username, raw_tweets)
                
                results["total_scraped"] += len(raw_tweets)
                results["total_saved"] += save_result["saved"]
                results["total_duplicates"] += save_result["duplicates"]
                results["users"][username] = {
                    "status": "success",
                    "scraped": len(raw_tweets),
                    "saved": save_result["saved"]
                }
                
                print(f"✅ {save_result['saved']} saved")
                
                # Rate limiting
                if i < len(usernames):
                    delay = random.uniform(15, 30)
                    time.sleep(delay)
                    
            except Exception as e:
                print(f"❌ Error: {str(e)[:40]}")
        
        scraper.close()
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
    
    return results

def print_summary(results):
    """Print summary"""
    print("\n" + "=" * 70)
    print("📊 SCRAPING SUMMARY")
    print("=" * 70)
    
    print(f"\n📈 Totals:")
    print(f"   Scraped: {results['total_scraped']}")
    print(f"   Saved: {results['total_saved']}")
    print(f"   Duplicates: {results['total_duplicates']}")
    
    # Database stats
    stats = get_stats()
    print(f"\n💾 Database:")
    print(f"   Total Tweets: {stats['total_tweets']}")
    print(f"   Retweets: {stats['total_retweets']}")
    print(f"   Original: {stats['original_tweets']}")
    print(f"   Total Views: {stats['total_views']:,}")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    councilors = load_data_csv("data/data.csv")
    usernames = [c['username'] for c in councilors]
    
    results = scrape_and_save(usernames, max_tweets=100, days_back=90)
    print_summary(results)

