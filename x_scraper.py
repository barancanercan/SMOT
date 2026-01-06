#!/usr/bin/env python3
"""
🐦 X/Twitter Scraper - COOKIE-BASED LOGIN
"""
import json
import os
import time
from datetime import datetime, timedelta
from typing import List, Dict
import random

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager

    SELENIUM_AVAILABLE = True
except ImportError as e:
    SELENIUM_AVAILABLE = False
    print(f"⚠️  Selenium not available: {e}")


class XTwitterScraper:
    """X/Twitter scraper - COOKIE-BASED LOGIN"""

    def __init__(self, headless=True, cookie_file: str = "cookies.json"):
        self.driver = None
        self.headless = False  # ALWAYS show browser for debugging
        self.logged_in = False
        self.cookie_file = cookie_file

        if not SELENIUM_AVAILABLE:
            print("❌ Selenium not installed")
            return

        try:
            self._init_driver()
            self._login_with_cookies()
        except Exception as e:
            print(f"⚠️  Driver init failed: {e}")
            self.driver = None

    def _init_driver(self):
        """Initialize Chrome WebDriver"""
        if not SELENIUM_AVAILABLE:
            raise Exception("Selenium not available")

        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            if self.headless:
                options.add_argument("--headless")
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

            print("  ⏳ ChromeDriver indiriliyor...")
            service = webdriver.chrome.service.Service(ChromeDriverManager().install())
            print("  ⏳ Chrome açılıyor...")
            self.driver = webdriver.Chrome(service=service, options=options)
            print("  ✅ Chrome açık.")
        except Exception as e:
            print(f"  ❌ Chrome error: {e}")
            raise

    def _login_with_cookies(self):
        """Login to X/Twitter using cookies"""
        if not os.path.exists(self.cookie_file):
            print("\n" + "=" * 70)
            print(f"‼️  Cookie dosyası bulunamadı: {self.cookie_file}")
            print("=" * 70)
            print("  Tarayıcınızdan X'e giriş yapın ve çerezleri dışa aktarın.")
            print("  Önerilen eklenti: 'Cookie-Editor'")
            print(f"  1. X.com'a gidin ve giriş yapın.")
            print(f"  2. 'Cookie-Editor' eklentisine tıklayın.")
            print(f"  3. 'Export' -> 'Export as JSON' seçin.")
            print(f"  4. İçeriği kopyalayıp bu dizinde '{self.cookie_file}' adlı bir dosyaya yapıştırın.")
            print("=" * 70 + "\n")
            self.driver.get("https://x.com/login") # Show login page to user
            return False

        try:
            print(f"🍪 '{self.cookie_file}' dosyasından çerezler yükleniyor...")
            self.driver.get("https://x.com")
            time.sleep(2)

            with open(self.cookie_file, 'r') as f:
                cookies = json.load(f)
            
            for cookie in cookies:
                if 'sameSite' not in cookie:
                    cookie['sameSite'] = 'None'
                self.driver.add_cookie(cookie)

            print("  ⏳ Sayfa yenileniyor ve giriş kontrol ediliyor...")
            self.driver.refresh()
            time.sleep(5)

            # Check if login was successful by looking for the main navigation
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//nav[@aria-label='Primary navigation']"))
            )
            self.logged_in = True
            print("\n✅ LOGIN BAŞARILI!\n")
            return True

        except Exception as e:
            print(f"❌ Çerezlerle giriş hatası: {e}")
            print("   Çerezler güncel olmayabilir. Lütfen dosyayı yenileyin.")
            return False

    def _parse_tweet_date(self, timestamp_str: str) -> datetime:
        try:
            if not timestamp_str:
                return None
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str.replace('Z', '+00:00')
            return datetime.fromisoformat(timestamp_str)
        except:
            return None

    def _is_within_days(self, tweet_date: datetime, days_back: int) -> bool:
        if not tweet_date:
            return False
        try:
            cutoff_date = datetime.now(tweet_date.tzinfo) - timedelta(days=days_back)
            return tweet_date >= cutoff_date
        except:
            return False

    def scrape_tweets(self, username: str, max_tweets: int = 50, days_back: int = 90) -> List[Dict]:
        if not self.driver or not self.logged_in or not SELENIUM_AVAILABLE:
            if not self.logged_in:
                print("⚠️  Giriş yapılmadığı için tweetler alınamıyor.")
            return []

        tweets = []
        url = f"https://x.com/{username}"
        print(f"  🔍 @{username:20s}", end=" ", flush=True)

        try:
            self.driver.get(url)
            time.sleep(random.uniform(2, 4))

            # Check for "This account doesn’t exist"
            try:
                if "This account doesn’t exist" in self.driver.page_source:
                    print("❌ Not found")
                    return []
            except:
                pass
            
            # Wait for tweets to load
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//article[@data-testid='tweet']"))
                )
            except:
                # If no tweets are found, it might be a suspended or protected account
                print("⚠️  Tweetler yüklenemedi (hesap korumalı/askıda olabilir).")
                return []

            seen_tweets = set()
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            scroll_count = 0
            found_old_tweets = 0

            while scroll_count < 25 and len(tweets) < max_tweets:
                try:
                    elements = self.driver.find_elements(By.XPATH, "//article[@data-testid='tweet']")

                    for element in elements:
                        if len(tweets) >= max_tweets:
                            break

                        try:
                            # Extract tweet text
                            text_elem = element.find_element(By.XPATH, ".//div[@data-testid='tweetText']")
                            tweet_text = text_elem.text.strip()

                            # Extract timestamp
                            tweet_date = None
                            try:
                                time_elem = element.find_element(By.XPATH, ".//time")
                                timestamp_str = time_elem.get_attribute("datetime")
                                tweet_date = self._parse_tweet_date(timestamp_str)
                            except:
                                pass

                            # Check if tweet is within the desired date range
                            if tweet_date and not self._is_within_days(tweet_date, days_back):
                                found_old_tweets += 1
                                if found_old_tweets > 10: # Stop if we keep finding old tweets
                                    break
                                continue

                            if tweet_text and tweet_text not in seen_tweets and len(tweet_text) > 5:
                                is_rt = tweet_text.strip().startswith("RT @")
                                rt_from = None
                                if is_rt:
                                    try:
                                        rt_from = tweet_text.split(":")[0].replace("RT", "").replace("@", "").strip()
                                    except:
                                        pass
                                
                                # Extract stats (likes, replies, retweets)
                                likes, replies, retweets_count = 0, 0, 0
                                try:
                                    stats = element.find_elements(By.XPATH, ".//div[@role='group']//a")
                                    for stat in stats:
                                        aria_label = stat.get_attribute("aria-label") or ""
                                        if "reply" in aria_label.lower():
                                            replies_text = stat.text.strip()
                                            if replies_text:
                                                replies = int(replies_text)
                                        elif "retweet" in aria_label.lower():
                                            retweets_text = stat.text.strip()
                                            if retweets_text:
                                                retweets_count = int(retweets_text)
                                        elif "like" in aria_label.lower():
                                            likes_text = stat.text.strip()
                                            if likes_text:
                                                likes = int(likes_text)
                                except:
                                    pass

                                tweets.append({
                                    "text": tweet_text[:500],
                                    "timestamp": tweet_date.isoformat() if tweet_date else None,
                                    "username": username,
                                    "is_retweet": is_rt,
                                    "retweet_from": rt_from,
                                    "likes": likes,
                                    "replies": replies,
                                    "retweets": retweets_count,
                                })
                                seen_tweets.add(tweet_text)
                        except:
                            pass
                except:
                    pass

                if found_old_tweets > 10:
                    break
                
                # Scroll down
                self.driver.execute_script("window.scrollBy(0, 1000);")
                time.sleep(random.uniform(0.5, 2.0))
                scroll_.count += 1

                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            if tweets:
                print(f"✅ {len(tweets):2d} tweet")
            else:
                print(f"⚠️  No tweets")
            return tweets

        except Exception as e:
            print(f"❌ Hata: {e}")
            return []

    def scrape_multiple(self, usernames: List[str], max_tweets: int = 50, days_back: int = 90) -> Dict:
        if not self.logged_in:
            print("‼️ Giriş yapılmadığı için scraping işlemi başlatılamıyor.")
            return {}

        print(f"\n🐦 X SCRAPER - {len(usernames)} users (COOKIE AUTHENTICATED)")
        print()

        results = {}
        for i, username in enumerate(usernames, 1):
            print(f"[{i:2d}/{len(usernames)}]", end=" ")
            tweets = self.scrape_tweets(username, max_tweets, days_back)
            if tweets:
                results[username] = tweets
            if i < len(usernames):
                time.sleep(random.uniform(2, 5))

        total = sum(len(t) for t in results.values())
        print(f"\n✅ Done! {total} tweets scraped from {len(results)} users.\n")
        return results

    def close(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()