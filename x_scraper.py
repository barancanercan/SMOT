#!/usr/bin/env python3
"""
🐦 X/Twitter Scraper v4.1 - FIXED LOGIN
- Programmatic form filling (no popup needed)
- Advanced RT detection
- Views extraction
"""

import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import random
import re

try:
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException
    SELENIUM_AVAILABLE = True
except ImportError as e:
    SELENIUM_AVAILABLE = False

try:
    import undetected_chromedriver as uc
    UNDETECTED_AVAILABLE = True
except ImportError:
    UNDETECTED_AVAILABLE = False


class XTwitterScraper:
    """X/Twitter scraper with programmatic login"""

    MAX_SCROLLS = 100
    CONSECUTIVE_OLD_THRESHOLD = 20
    SCROLL_DISTANCE = 1500
    SCROLL_DELAY_MIN = 0.3
    SCROLL_DELAY_MAX = 1.0

    def __init__(self, headless=True, username: str = None, password: str = None):
        self.driver = None
        self.headless = headless
        self.username = username
        self.password = password
        self.logged_in = False

        if not SELENIUM_AVAILABLE or not UNDETECTED_AVAILABLE:
            print("❌ Required libraries not installed")
            return

        try:
            self._init_driver()
            if username and password:
                self._login_programmatic()
        except Exception as e:
            print(f"⚠️  Driver init failed: {e}")
            self.driver = None

    def _init_driver(self):
        """Initialize Undetected Chrome WebDriver"""
        if not SELENIUM_AVAILABLE or not UNDETECTED_AVAILABLE:
            raise Exception("Required libraries not available")

        try:
            options = uc.ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument(
                "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            options.add_argument("--blink-settings=imagesEnabled=false")

            print("  ⏳ Undetected Chrome initializing...")
            self.driver = uc.Chrome(options=options, version_main=None, use_subprocess=False)

            print("  ✅ Undetected Chrome ready")
        except Exception as e:
            print(f"  ❌ Chrome error: {e}")
            raise

    def _login_programmatic(self):
        """
        Programmatic login - fill form fields directly
        No popup waiting needed
        """
        try:
            print("  🔐 Logging in programmatically...")
            
            # Go to login page
            self.driver.get("https://x.com/login")
            time.sleep(3)
            
            # STEP 1: Find and fill username/email field
            print("     ⏳ Looking for username field...")
            try:
                # Try multiple selectors for username input
                username_input = None
                selectors = [
                    "//input[@autocomplete='username']",
                    "//input[@name='text']",
                    "//input[@placeholder='Phone, email or username']",
                    "//input[@type='text'][1]"
                ]
                
                for selector in selectors:
                    try:
                        username_input = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, selector))
                        )
                        break
                    except:
                        pass
                
                if not username_input:
                    print("     ❌ Username field not found")
                    return False
                
                # Fill username
                username_input.clear()
                username_input.send_keys(self.username)
                print(f"     ✅ Username filled: {self.username}")
                time.sleep(1)
                
            except TimeoutException:
                print("     ❌ Username field timeout")
                return False
            
            # STEP 2: Click "Next" button
            print("     ⏳ Looking for Next button...")
            try:
                next_buttons = self.driver.find_elements(By.XPATH, "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'next')]")
                if not next_buttons:
                    next_buttons = self.driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Next')]")
                if not next_buttons:
                    # Try any button that might be "Next"
                    next_buttons = self.driver.find_elements(By.XPATH, "//button[@type='button' or @type='submit'][-1]")
                
                if next_buttons:
                    next_buttons[0].click()
                    print("     ✅ Next button clicked")
                    time.sleep(2)
            except Exception as e:
                print(f"     ⚠️  Next button error: {str(e)[:40]}")
            
            # STEP 3: Find and fill password field
            print("     ⏳ Looking for password field...")
            try:
                password_input = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@type='password']"))
                )
                password_input.clear()
                password_input.send_keys(self.password)
                print(f"     ✅ Password filled")
                time.sleep(1)
                
            except TimeoutException:
                print("     ❌ Password field not found")
                return False
            
            # STEP 4: Click Login button
            print("     ⏳ Looking for Login button...")
            try:
                login_buttons = self.driver.find_elements(By.XPATH, "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'log in')]")
                if not login_buttons:
                    login_buttons = self.driver.find_elements(By.XPATH, "//button[@role='button' and contains(text(), 'in')]")
                if not login_buttons:
                    # Get last button as fallback
                    all_buttons = self.driver.find_elements(By.XPATH, "//button[@type='button' or @type='submit']")
                    if all_buttons:
                        login_buttons = [all_buttons[-1]]
                
                if login_buttons:
                    login_buttons[0].click()
                    print("     ✅ Login button clicked")
                    time.sleep(3)
            except Exception as e:
                print(f"     ⚠️  Login button error: {str(e)[:40]}")
            
            # STEP 5: Wait for home feed
            print("     ⏳ Waiting for home feed...")
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, "//nav[@aria-label='Primary navigation']"))
                )
                self.logged_in = True
                print("  ✅ X'e giriş başarılı!")
                return True
            except TimeoutException:
                print("     ⚠️  Home feed timeout - checking if already logged in...")
                # Check if tweets are visible anyway
                try:
                    self.driver.find_element(By.XPATH, "//article[@data-testid='tweet']")
                    self.logged_in = True
                    print("  ✅ Tweets detected - logged in!")
                    return True
                except:
                    print("  ❌ Login verification failed")
                    return False

        except Exception as e:
            print(f"  ❌ Login error: {e}")
            self.logged_in = False
            return False

    def _parse_tweet_date(self, timestamp_str: str) -> Optional[datetime]:
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

    def _is_within_days(self, tweet_date: Optional[datetime], days_back: int) -> bool:
        """Check if tweet is within last N days"""
        if not tweet_date:
            return False
        try:
            cutoff_date = datetime.now(tweet_date.tzinfo) - timedelta(days=days_back)
            return tweet_date >= cutoff_date
        except:
            return False

    def _detect_retweet(self, tweet_element, profile_username: str) -> Tuple[bool, Optional[str]]:
        """Advanced RT detection using author handle comparison"""
        try:
            user_names_el = tweet_element.find_element(By.CSS_SELECTOR, 'div[data-testid="User-Names"]')
            user_text = user_names_el.text
            
            parts = user_text.split('\n')
            if len(parts) < 2:
                return False, None
            
            author_handle = parts[1].lstrip('@').lower().strip()
            profile_lower = profile_username.lower().lstrip('@').strip()
            
            is_retweet = author_handle != profile_lower
            retweet_from = author_handle if is_retweet else None
            
            # Secondary confirmation
            try:
                repost_indicators = tweet_element.find_elements(
                    By.XPATH,
                    './/span[contains(text(), "reposted") or contains(text(), "Reposted")]'
                )
                if repost_indicators:
                    is_retweet = True
                    if not retweet_from:
                        retweet_from = author_handle
            except:
                pass
            
            return is_retweet, retweet_from

        except Exception as e:
            return False, None

    def _extract_views(self, tweet_element) -> int:
        """Extract views count"""
        try:
            views_elements = tweet_element.find_elements(By.XPATH, './/*[@aria-label]')
            for elem in views_elements:
                aria_label = elem.get_attribute('aria-label') or ""
                match = re.search(r'([\d,\.]+[KMB]?)\s*view', aria_label.lower())
                if match:
                    return self._parse_number(match.group(1))
            return 0
        except:
            return 0

    def _parse_number(self, num_str: str) -> int:
        """Parse number string like '1.2K' to 1200"""
        try:
            num_str = num_str.strip().upper()
            num_str = num_str.replace(',', '')
            
            if 'B' in num_str:
                return int(float(num_str.replace('B', '')) * 1_000_000_000)
            elif 'M' in num_str:
                return int(float(num_str.replace('M', '')) * 1_000_000)
            elif 'K' in num_str:
                return int(float(num_str.replace('K', '')) * 1_000)
            else:
                return int(float(num_str))
        except:
            return 0

    def _extract_engagement_metrics(self, tweet_element) -> Dict[str, int]:
        """Extract engagement metrics"""
        metrics = {'likes': 0, 'replies': 0, 'retweets': 0, 'views': 0}

        try:
            stat_elements = tweet_element.find_elements(By.XPATH, './/*[@aria-label]')
            
            for elem in stat_elements:
                aria_label = (elem.get_attribute('aria-label') or "").lower()
                
                if 'repl' in aria_label:
                    match = re.search(r'([\d,\.]+)', aria_label)
                    if match:
                        metrics['replies'] = self._parse_number(match.group(1))
                
                elif 'retweet' in aria_label:
                    match = re.search(r'([\d,\.]+)', aria_label)
                    if match:
                        metrics['retweets'] = self._parse_number(match.group(1))
                
                elif 'like' in aria_label:
                    match = re.search(r'([\d,\.]+)', aria_label)
                    if match:
                        metrics['likes'] = self._parse_number(match.group(1))
                
                elif 'view' in aria_label:
                    match = re.search(r'([\d,\.]+)', aria_label)
                    if match:
                        metrics['views'] = self._parse_number(match.group(1))
        
        except Exception as e:
            pass

        return metrics

    def scrape_tweets(self, username: str, max_tweets: int = 50, days_back: int = 90) -> List[Dict]:
        """Scrape tweets from X profile"""
        if not self.driver or not SELENIUM_AVAILABLE:
            return []

        tweets = []
        url = f"https://x.com/{username}"

        print(f"  🔍 @{username:20s}", end=" ", flush=True)

        try:
            self.driver.get(url)
            time.sleep(random.uniform(2, 4))

            try:
                self.driver.find_element(By.XPATH, "//span[contains(text(), 'does not exist')]")
                print("❌ Not found")
                return []
            except:
                pass

            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//article[@data-testid='tweet']"))
                )
            except:
                pass

            seen_tweets = set()
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            scroll_count = 0
            found_old_tweets = 0

            while scroll_count < self.MAX_SCROLLS and len(tweets) < max_tweets:
                try:
                    tweet_elements = self.driver.find_elements(
                        By.XPATH,
                        "//article[@data-testid='tweet']"
                    )

                    for element in tweet_elements:
                        if len(tweets) >= max_tweets:
                            break

                        try:
                            text_elem = element.find_element(
                                By.XPATH,
                                ".//div[@data-testid='tweetText']/span"
                            )
                            tweet_text = text_elem.text.strip()

                            tweet_date = None
                            try:
                                time_elem = element.find_element(By.XPATH, ".//time")
                                timestamp_str = time_elem.get_attribute("datetime")
                                tweet_date = self._parse_tweet_date(timestamp_str)
                            except:
                                tweet_date = None

                            if tweet_date and not self._is_within_days(tweet_date, days_back):
                                found_old_tweets += 1
                                if found_old_tweets > self.CONSECUTIVE_OLD_THRESHOLD:
                                    break
                                continue

                            if tweet_text and tweet_text not in seen_tweets and len(tweet_text) > 5:
                                is_rt, rt_from = self._detect_retweet(element, username)
                                metrics = self._extract_engagement_metrics(element)

                                tweets.append({
                                    "text": tweet_text[:500],
                                    "timestamp": tweet_date.isoformat() if tweet_date else None,
                                    "username": username,
                                    "is_retweet": is_rt,
                                    "retweet_from": rt_from,
                                    "likes": metrics['likes'],
                                    "replies": metrics['replies'],
                                    "retweets": metrics['retweets'],
                                    "views": metrics['views'],
                                })
                                seen_tweets.add(tweet_text)
                        except Exception as e:
                            pass
                except:
                    pass

                if found_old_tweets > self.CONSECUTIVE_OLD_THRESHOLD:
                    break

                delay = random.uniform(self.SCROLL_DELAY_MIN, self.SCROLL_DELAY_MAX)
                self.driver.execute_script(f"window.scrollBy(0, {self.SCROLL_DISTANCE});")
                time.sleep(delay)
                scroll_count += 1

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
            print(f"❌ Error: {str(e)[:30]}")
            return []

    def scrape_multiple(self, usernames: List[str], max_tweets: int = 50, days_back: int = 90) -> Dict[str, List[Dict]]:
        """Scrape multiple users"""
        print(f"\n🐦 X SCRAPER v4.1 - {len(usernames)} users")
        print(f"   ✅ Programmatic Login: ON")
        print(f"   ✅ Advanced RT Detection: ON")
        print(f"   ✅ Views Extraction: ON\n")

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
        print(f"\n✅ Done! {total} tweets fetched\n")
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

