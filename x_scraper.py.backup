#!/usr/bin/env python3
"""
🐦 X/Twitter Scraper - ULTIMATE FIX
Proper RT detection, aggressive scrolling, 90-day full capture
"""

import time
from datetime import datetime, timedelta, timezone
from typing import List, Dict
import random

try:
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    UNDETECTED_AVAILABLE = True
except ImportError as e:
    UNDETECTED_AVAILABLE = False
    print(f"⚠️  undetected-chromedriver not available: {e}")


class XTwitterScraper:
    """X/Twitter scraper - Ultimate version with proper RT and date handling"""

    def __init__(self, headless=False, require_login=True):
        """Initialize scraper"""
        self.driver = None
        self.headless = headless
        self.logged_in = False
        self.require_login = require_login

        if not UNDETECTED_AVAILABLE:
            print("❌ undetected-chromedriver not installed")
            return

        try:
            self._init_driver()
            if require_login:
                print("\n" + "=" * 70)
                print("🔐 LOGIN REQUIRED")
                print("=" * 70)
                self._login_manual()
            else:
                self.logged_in = True
        except Exception as e:
            print(f"⚠️  Driver init failed: {e}")
            self.driver = None
            self.logged_in = False

    def _init_driver(self):
        """Initialize Undetected Chrome"""
        if not UNDETECTED_AVAILABLE:
            raise Exception("undetected-chromedriver not available")

        try:
            print("  ⏳ Undetected Chrome initializing...")
            options = uc.ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            options.add_argument("--blink-settings=imagesEnabled=false")

            self.driver = uc.Chrome(options=options, version_main=None, use_subprocess=False)
            print("  ✅ Undetected Chrome ready (bot detection bypass ACTIVE)")

        except Exception as e:
            print(f"  ❌ Chrome init error: {e}")
            raise

    def _login_manual(self):
        """Wait for user to manually login"""
        try:
            print("\n  📱 Opening X.com login page...")
            self.driver.get("https://x.com/login")
            time.sleep(2)

            print("\n" + "=" * 70)
            print("  ⏳ WAITING FOR LOGIN")
            print("=" * 70)
            print("\n  📍 Tarayıcıda aşağıdaki adımları takip et:")
            print("     1. Email/username gir")
            print("     2. Password gir")
            print("     3. Giriş yap")
            print("\n  ⏱️  Sistem otomatik 3 dakika boyunca giriş kontrol edecek")
            print("=" * 70 + "\n")

            login_timeout = 180
            check_interval = 2
            elapsed = 0

            while elapsed < login_timeout:
                try:
                    current_url = self.driver.current_url
                    if "x.com/login" not in current_url and "x.com/i/flow" not in current_url:
                        time.sleep(3)
                        print("  ✅ URL CHANGED - Login detected!\n")
                        self.logged_in = True
                        return True
                except:
                    pass

                try:
                    self.driver.find_element(By.XPATH, "//nav[@aria-label='Primary navigation']")
                    print("  ✅ PRIMARY NAVIGATION FOUND - Login successful!\n")
                    self.logged_in = True
                    time.sleep(2)
                    return True
                except:
                    pass

                try:
                    elements = self.driver.find_elements(By.XPATH, "//article[@data-testid='tweet']")
                    if elements and len(elements) > 0:
                        print("  ✅ TWEETS FOUND - Login successful!\n")
                        self.logged_in = True
                        time.sleep(2)
                        return True
                except:
                    pass

                elapsed += check_interval
                if elapsed % 10 == 0:
                    remaining = login_timeout - elapsed
                    print(f"     {elapsed}s geçti... {remaining}s kaldı")

                time.sleep(check_interval)

            print("  ❌ LOGIN TIMEOUT! (3 dakika doldu)\n")
            self.logged_in = False
            return False

        except Exception as e:
            print(f"  ❌ Login error: {e}\n")
            self.logged_in = False
            return False

    def _wait_for_page_load(self):
        """Aggressive page load wait"""
        try:
            WebDriverWait(self.driver, 25).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
        except:
            pass

        time.sleep(3)
        self.driver.execute_script("window.scrollBy(0, 200);")
        time.sleep(2)

    def _parse_tweet_date(self, timestamp_str: str) -> datetime:
        """Parse ISO 8601 date from Twitter"""
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
        """Check if tweet is within last N days - FIXED"""
        if not tweet_date:
            return False
        try:
            now = datetime.now(timezone.utc)
            cutoff_date = now - timedelta(days=days_back)

            if tweet_date.tzinfo is None:
                tweet_date = tweet_date.replace(tzinfo=timezone.utc)

            return tweet_date >= cutoff_date
        except:
            return False

    def _detect_retweet(self, element, tweet_text: str) -> tuple:
        """Detect retweet - SIMPLE & RELIABLE"""
        is_rt = False
        rt_from = None

        # ONLY method: Check if text starts with "RT @"
        # This is the most reliable indicator
        if tweet_text.strip().startswith("RT @"):
            is_rt = True
            try:
                # Extract @username from "RT @username: ..."
                rt_part = tweet_text.split(":")[0]  # "RT @username"
                rt_from = rt_part.replace("RT", "").replace("@", "").strip()
            except:
                pass

        return is_rt, rt_from

    def _parse_engagement_metrics(self, element) -> Dict:
        """Parse engagement metrics"""
        metrics = {
            "likes": 0,
            "replies": 0,
            "retweets": 0,
            "views": 0
        }

        try:
            # Try button elements
            buttons = element.find_elements(By.XPATH, ".//button | .//a[@role='button']")
            for btn in buttons:
                aria_label = btn.get_attribute("aria-label") or ""
                if not aria_label:
                    continue

                lower = aria_label.lower()

                if "reply" in lower or "cevap" in lower:
                    try:
                        nums = ''.join(filter(str.isdigit, aria_label.split()[0]))
                        if nums:
                            metrics["replies"] = int(nums)
                    except:
                        pass

                elif "retweet" in lower or "rt " in lower:
                    try:
                        nums = ''.join(filter(str.isdigit, aria_label.split()[0]))
                        if nums:
                            metrics["retweets"] = int(nums)
                    except:
                        pass

                elif "like" in lower or "beğeni" in lower:
                    try:
                        nums = ''.join(filter(str.isdigit, aria_label.split()[0]))
                        if nums:
                            metrics["likes"] = int(nums)
                    except:
                        pass

                elif "view" in lower or "görüntüleme" in lower:
                    try:
                        nums = ''.join(filter(str.isdigit, aria_label.split()[0]))
                        if nums:
                            metrics["views"] = int(nums)
                    except:
                        pass
        except:
            pass

        return metrics

    def _get_tweet_text(self, element) -> str:
        """Extract tweet text"""
        selectors = [
            ".//div[@data-testid='tweetText']//span",
            ".//div[@data-testid='tweetText']",
            ".//span[contains(@class, 'css-16my406')]",
            ".//div[contains(@class, 'r-bcqeeo')]",
            ".//span[contains(@class, 'r-bcqeeo')]",
        ]

        for selector in selectors:
            try:
                elem = element.find_element(By.XPATH, selector)
                text = elem.text.strip()
                if text and len(text) > 0:
                    return text
            except:
                pass

        return None

    def scrape_tweets(self, username: str, max_tweets: int = 100, days_back: int = 90) -> List[Dict]:
        """Scrape tweets - ULTIMATE VERSION"""
        if not self.driver or not self.logged_in:
            print(f"  🔍 @{username:20s} ❌ Not initialized")
            return []

        tweets = []
        url = f"https://x.com/{username}"
        print(f"  🔍 @{username:20s}", end=" ", flush=True)

        try:
            self.driver.get(url)
            time.sleep(3)
            self._wait_for_page_load()

            tweet_elements = self.driver.find_elements(By.XPATH, "//article[@data-testid='tweet']")

            if not tweet_elements or len(tweet_elements) == 0:
                tweet_elements = self.driver.find_elements(By.XPATH, "//div[@data-testid='tweet']")

            if not tweet_elements or len(tweet_elements) == 0:
                self.driver.execute_script("window.scrollBy(0, 500);")
                time.sleep(3)
                tweet_elements = self.driver.find_elements(By.XPATH, "//article[@data-testid='tweet']")

            if not tweet_elements or len(tweet_elements) == 0:
                print("⚠️  No tweets")
                return []

            seen_tweets = set()
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            scroll_count = 0
            max_scrolls = 50  # INCREASED: 25 → 50 for deeper scrolling
            found_old_tweets = 0
            consecutive_old = 0

            while scroll_count < max_scrolls and len(tweets) < max_tweets:
                try:
                    tweet_elements = self.driver.find_elements(By.XPATH, "//article[@data-testid='tweet']")

                    for element in tweet_elements:
                        if len(tweets) >= max_tweets:
                            break

                        try:
                            tweet_text = self._get_tweet_text(element)
                            if not tweet_text:
                                continue

                            # Get timestamp
                            tweet_date = None
                            try:
                                time_elem = element.find_element(By.XPATH, ".//time")
                                timestamp_str = time_elem.get_attribute("datetime")
                                tweet_date = self._parse_tweet_date(timestamp_str)
                            except:
                                tweet_date = None

                            # CRITICAL: Filter by last 90 days
                            if tweet_date and not self._is_within_days(tweet_date, days_back):
                                found_old_tweets += 1
                                consecutive_old += 1
                                if consecutive_old > 5:  # Stop after 5 consecutive old tweets
                                    break
                                continue
                            else:
                                consecutive_old = 0  # Reset counter for new tweets

                            if tweet_text and tweet_text not in seen_tweets and len(tweet_text) > 5:
                                # IMPROVED: Retweet detection with multiple methods
                                is_rt, rt_from = self._detect_retweet(element, tweet_text)

                                # Parse engagement metrics
                                metrics = self._parse_engagement_metrics(element)

                                tweets.append({
                                    "text": tweet_text[:500],
                                    "timestamp": tweet_date.isoformat() if tweet_date else None,
                                    "username": username,
                                    "is_retweet": is_rt,
                                    "retweet_from": rt_from,
                                    "likes": metrics["likes"],
                                    "replies": metrics["replies"],
                                    "retweets": metrics["retweets"],
                                    "views": metrics["views"],
                                })
                                seen_tweets.add(tweet_text)
                        except Exception:
                            pass

                except:
                    pass

                # Stop if too many old tweets
                if consecutive_old > 5:
                    break

                # AGGRESSIVE SCROLL: Faster and more frequent
                delay = random.uniform(0.3, 1.0)  # Reduced from 0.5-2.0
                self.driver.execute_script("window.scrollBy(0, 1500);")  # Increased from 1000
                time.sleep(delay)
                scroll_count += 1

                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    # Try one more aggressive scroll
                    self.driver.execute_script("window.scrollBy(0, 2000);")
                    time.sleep(1)
                    new_height = self.driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        break
                last_height = new_height

            if tweets:
                print(f"✅ {len(tweets):2d} tweet")
            else:
                print(f"⚠️  No tweets found")

            return tweets

        except Exception as e:
            print(f"❌ Error: {str(e)[:40]}")
            return []

    def scrape_multiple(self, usernames: List[str], max_tweets: int = 100, days_back: int = 90) -> Dict[
        str, List[Dict]]:
        """Scrape multiple users - 90 day full capture"""
        print(f"\n🐦 X SCRAPER - {len(usernames)} users (Last {days_back} days)")
        print(f"   ✅ Undetected-Chrome: BOT DETECTION BYPASS ACTIVE")
        print(f"   ✅ Aggressive scrolling enabled")
        print(f"   ✅ Improved RT detection\n")

        results = {}
        for i, username in enumerate(usernames, 1):
            print(f"[{i:2d}/{len(usernames)}]", end=" ")
            tweets = self.scrape_tweets(username, max_tweets, days_back)
            if tweets:
                results[username] = tweets

            if i < len(usernames):
                delay = random.uniform(2, 5)
                time.sleep(delay)

        total = sum(len(t) for t in results.values())
        print(f"\n✅ Done! {total} tweets fetched (including RT's)\n")
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