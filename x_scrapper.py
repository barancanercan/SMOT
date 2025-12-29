#!/usr/bin/env python3
"""
🐦 X/Twitter Scraper - Selenium with Undetected Chrome
Bot detection bypass ile gerçek tweet'leri çek
"""

import time
from datetime import datetime, timedelta
from typing import List, Dict

# Safe imports
try:
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    SELENIUM_AVAILABLE = True
except ImportError as e:
    SELENIUM_AVAILABLE = False
    print(f"⚠️  Selenium not available: {e}")

try:
    import undetected_chromedriver as uc

    UNDETECTED_AVAILABLE = True
except ImportError:
    UNDETECTED_AVAILABLE = False
    print("⚠️  undetected-chromedriver not available")


class XTwitterScraper:
    """X/Twitter scraper using Undetected Chrome"""

    def __init__(self, headless=True):
        self.driver = None
        self.headless = headless

        if not SELENIUM_AVAILABLE or not UNDETECTED_AVAILABLE:
            print("❌ Required libraries not installed")
            return

        try:
            self._init_driver()
        except Exception as e:
            print(f"⚠️  Driver init failed: {e}")
            self.driver = None

    def _init_driver(self):
        """Initialize Undetected Chrome WebDriver"""
        if not SELENIUM_AVAILABLE or not UNDETECTED_AVAILABLE:
            raise Exception("Required libraries not available")

        try:
            # Undetected chrome options
            options = uc.ChromeOptions()

            # Headless OFF - kullanıcıyı göster (GUI environment yoksa sorun)
            # if self.headless:
            #     options.add_argument("--headless=new")

            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-blink-features=AutomationControlled")

            # User agent
            options.add_argument(
                "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )

            # Disable images for faster loading
            options.add_argument("--blink-settings=imagesEnabled=false")

            # Launch undetected chrome (version otomatik detect)
            print("  ⏳ Undetected Chrome initializing (ilk kez yavaş olabilir)...")
            self.driver = uc.Chrome(options=options, version_main=None, use_subprocess=False)

            print("  ✅ Undetected Chrome ready (bot detection bypass active)")
        except Exception as e:
            print(f"  ❌ Chrome error: {e}")
            print("  💡 İpucu: X'in scroll loading'i sorun yaşayabilir")
            raise

    def _parse_tweet_date(self, timestamp_str: str) -> datetime:
        """Parse ISO format date"""
        try:
            if not timestamp_str:
                return None

            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str.replace('Z', '+00:00')

            dt = datetime.fromisoformat(timestamp_str)
            return dt
        except:
            return None

    def _is_within_days(self, tweet_date: datetime, days_back: int) -> bool:
        """Check if tweet is within last N days"""
        if not tweet_date:
            return False

        try:
            cutoff_date = datetime.now(tweet_date.tzinfo) - timedelta(days=days_back)
            return tweet_date >= cutoff_date
        except:
            return False

    def scrape_tweets(self, username: str, max_tweets: int = 50, days_back: int = 90) -> List[Dict]:
        """Scrape tweets from X profile with date filtering"""
        if not self.driver or not SELENIUM_AVAILABLE:
            return []

        tweets = []
        url = f"https://x.com/{username}"

        print(f"  🔍 @{username:20s}", end=" ", flush=True)

        try:
            self.driver.get(url)
            time.sleep(4)  # Daha uzun bekleme

            # Check if profile exists
            try:
                self.driver.find_element(By.XPATH, "//span[contains(text(), 'does not exist')]")
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
                pass

            # Scroll and collect tweets
            seen_tweets = set()
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            scroll_count = 0
            max_scrolls = 25  # Daha fazla scroll
            found_old_tweets = 0

            while scroll_count < max_scrolls and len(tweets) < max_tweets:
                # Get tweet elements
                try:
                    tweet_elements = self.driver.find_elements(
                        By.XPATH,
                        "//article[@data-testid='tweet']"
                    )

                    for element in tweet_elements:
                        if len(tweets) >= max_tweets:
                            break

                        try:
                            # Get tweet text
                            text_elem = element.find_element(
                                By.XPATH,
                                ".//div[@data-testid='tweetText']/span"
                            )
                            tweet_text = text_elem.text.strip()

                            # Get timestamp
                            tweet_date = None
                            try:
                                time_elem = element.find_element(
                                    By.XPATH,
                                    ".//time"
                                )
                                timestamp_str = time_elem.get_attribute("datetime")
                                tweet_date = self._parse_tweet_date(timestamp_str)
                            except:
                                tweet_date = None

                            # Filter by date
                            if tweet_date and not self._is_within_days(tweet_date, days_back):
                                found_old_tweets += 1
                                if found_old_tweets > 10:
                                    break
                                continue

                            if tweet_text and tweet_text not in seen_tweets and len(tweet_text) > 5:
                                tweets.append({
                                    "text": tweet_text[:500],
                                    "timestamp": tweet_date.isoformat() if tweet_date else None,
                                    "username": username,
                                })
                                seen_tweets.add(tweet_text)
                        except Exception as e:
                            pass
                except:
                    pass

                # Stop if found too many old tweets
                if found_old_tweets > 10:
                    break

                # Aggressive scroll
                self.driver.execute_script("window.scrollBy(0, 1000);")
                time.sleep(1.0)
                scroll_count += 1

                # Check if at end
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            if tweets:
                print(f"✅ {len(tweets):2d} tweet (son {days_back} gün)")
            else:
                print(f"⚠️  No tweets (son {days_back} gün)")

            return tweets

        except Exception as e:
            print(f"❌ Error: {str(e)[:30]}")
            return []

    def scrape_multiple(self, usernames: List[str], max_tweets: int = 50, days_back: int = 90) -> Dict[str, List[Dict]]:
        """Scrape multiple users"""
        print(f"\n🐦 X SCRAPER - {len(usernames)} users (last {days_back} days)")
        print(f"   🔓 Bot Detection Bypass: ACTIVE\n")

        results = {}
        for i, username in enumerate(usernames, 1):
            print(f"[{i:2d}/{len(usernames)}]", end=" ")
            tweets = self.scrape_tweets(username, max_tweets, days_back)
            if tweets:
                results[username] = tweets

        total = sum(len(t) for t in results.values())
        print(f"\n✅ Done! {total} tweets fetched (son {days_back} gün)\n")
        return results

    def close(self):
        """Close browser"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()