#!/usr/bin/env python3
"""
🐦 X/Twitter Scraper - Selenium-based
"""

import time
from typing import List, Dict

# Safe imports
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options

    SELENIUM_AVAILABLE = True
except ImportError as e:
    SELENIUM_AVAILABLE = False
    print(f"⚠️  Selenium not available: {e}")

try:
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service

    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False


class XTwitterScraper:
    """X/Twitter scraper using Selenium"""

    def __init__(self, headless=True):
        self.driver = None
        self.headless = headless

        if not SELENIUM_AVAILABLE:
            print("❌ Selenium not installed")
            return

        try:
            self._init_driver()
        except Exception as e:
            print(f"⚠️  Driver init failed: {e}")
            self.driver = None

    def _init_driver(self):
        """Initialize Chrome WebDriver"""
        if not SELENIUM_AVAILABLE:
            raise Exception("Selenium not available")

        options = Options()

        if self.headless:
            options.add_argument("--headless=new")

        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")

        try:
            if WEBDRIVER_MANAGER_AVAILABLE:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
            else:
                self.driver = webdriver.Chrome(options=options)
            print("  ✅ Chrome driver ready")
        except Exception as e:
            print(f"  ❌ Chrome error: {e}")
            raise

    def scrape_tweets(self, username: str, max_tweets: int = 50) -> List[str]:
        """Scrape tweets from X profile"""
        if not self.driver or not SELENIUM_AVAILABLE:
            return []

        tweets = []
        url = f"https://x.com/{username}"

        print(f"  🔍 @{username:20s}", end=" ", flush=True)

        try:
            self.driver.get(url)
            time.sleep(2)

            # Check if profile exists
            try:
                self.driver.find_element(By.XPATH, "//span[contains(text(), 'does not exist')]")
                print("❌ Not found")
                return []
            except:
                pass

            # Scroll and collect tweets
            seen_tweets = set()
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            scroll_count = 0
            max_scrolls = 8

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

                            if tweet_text and tweet_text not in seen_tweets:
                                tweets.append(tweet_text[:500])
                                seen_tweets.add(tweet_text)
                        except:
                            pass
                except:
                    pass

                # Scroll down
                self.driver.execute_script("window.scrollBy(0, 500);")
                time.sleep(0.3)
                scroll_count += 1

                # Check if at end
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            if tweets:
                print(f"✅ {len(tweets):2d} tweet")
            else:
                print("⚠️  No tweets")

            return tweets

        except Exception as e:
            print(f"❌ Error: {str(e)[:30]}")
            return []

    def scrape_multiple(self, usernames: List[str], max_tweets: int = 50) -> Dict[str, List[str]]:
        """Scrape multiple users"""
        print(f"\n🐦 X SCRAPER - {len(usernames)} users\n")

        results = {}
        for i, username in enumerate(usernames, 1):
            print(f"[{i:2d}/{len(usernames)}]", end=" ")
            tweets = self.scrape_tweets(username, max_tweets)
            if tweets:
                results[username] = tweets

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