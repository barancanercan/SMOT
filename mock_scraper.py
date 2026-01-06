#!/usr/bin/env python3
"""Mock scraper - no Chrome needed"""

from typing import List, Dict
import time

class MockTwitterScraper:
    """Mock scraper for testing - returns hardcoded tweet data"""
    
    def __init__(self):
        self.headless = True
        print(f"✅ Mock Scraper initialized")
    
    def scrape_tweets(self, username: str, max_tweets: int = 50, days_back: int = 90) -> List[Dict]:
        """Return mock tweets"""
        print(f"  🔍 @{username:20s}", end=" ", flush=True)
        
        mock_tweets = [
            {
                "text": f"Test tweet 1 from @{username}",
                "timestamp": "2025-01-06T10:00:00Z",
                "username": username,
                "is_retweet": False,
                "retweet_from": None,
                "likes": 10,
                "replies": 2,
                "retweets": 1,
            },
            {
                "text": f"Test tweet 2 from @{username}",
                "timestamp": "2025-01-05T15:30:00Z",
                "username": username,
                "is_retweet": True,
                "retweet_from": "other_user",
                "likes": 5,
                "replies": 1,
                "retweets": 3,
            },
            {
                "text": f"Test tweet 3 from @{username}",
                "timestamp": "2025-01-04T09:15:00Z",
                "username": username,
                "is_retweet": False,
                "retweet_from": None,
                "likes": 20,
                "replies": 5,
                "retweets": 8,
            }
        ]
        
        time.sleep(0.3)
        print(f"✅ {len(mock_tweets)} tweets (mock)")
        return mock_tweets
    
    def scrape_multiple(self, usernames: List[str], max_tweets: int = 50, days_back: int = 90) -> Dict:
        """Scrape multiple users"""
        print(f"\n🐦 MOCK SCRAPER - {len(usernames)} users\n")
        
        results = {}
        for i, username in enumerate(usernames, 1):
            print(f"[{i:2d}/{len(usernames)}]", end=" ")
            tweets = self.scrape_tweets(username, max_tweets, days_back)
            if tweets:
                results[username] = tweets
            
            if i < len(usernames):
                time.sleep(0.3)
        
        total = sum(len(t) for t in results.values())
        print(f"\n✅ Done! {total} mock tweets\n")
        return results
    
    def close(self):
        pass
