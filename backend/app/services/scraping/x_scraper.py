#!/usr/bin/env python3
"""
🐦 X/Twitter Scraper v3.1 - Exact 3-Month Collection
✅ Scrolls until exactly 3 months (90 days) of tweets collected
✅ Stops when 5 consecutive old tweets detected (date boundary reached)
✅ Collects ALL tweets within time window
✅ Enhanced RT detection + Views
"""

import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import random
import platform
from app.utils.logger import get_logger
from app.utils.retry_config import retry_on_scraping_error

# Logger init
logger = get_logger("XScraper")

# Safe imports
try:
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import (
        TimeoutException,
        NoSuchElementException,
        StaleElementReferenceException
    )

    SELENIUM_AVAILABLE = True
except ImportError as e:
    SELENIUM_AVAILABLE = False
    logger.warning(f"Selenium not available: {e}")

try:
    import undetected_chromedriver as uc

    UNDETECTED_AVAILABLE = True
except ImportError:
    UNDETECTED_AVAILABLE = False
    logger.warning("undetected-chromedriver not available")


class XTwitterScraper:
    """X/Twitter scraper v3.0 - Aggressive time-based collection"""

    def __init__(self, headless=True, require_manual_login=True):
        self.driver = None
        self.headless = headless
        self.logged_in = False
        self.require_manual_login = require_manual_login

        if not SELENIUM_AVAILABLE or not UNDETECTED_AVAILABLE:
            logger.error("Required libraries not installed")
            return

        try:
            self._init_driver()
            if require_manual_login:
                self._manual_login_wait()
        except Exception as e:
            logger.error(f"Driver init failed: {e}")
            self.driver = None

    def _init_driver(self):
        """Initialize Undetected Chrome WebDriver with platform detection"""
        if not SELENIUM_AVAILABLE or not UNDETECTED_AVAILABLE:
            raise Exception("Required libraries not available")

        try:
            options = uc.ChromeOptions()

            # Platform-specific browser selection
            if platform.system() == "Windows":
                options.binary_location = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
                logger.info("Undetected Chrome initializing (Brave on Windows)...")
            else:
                logger.info("Undetected Chrome initializing (Chrome on Linux)...")

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

            # Launch undetected chrome
            self.driver = uc.Chrome(options=options, headless=False)

            logger.info("Browser ready (bot detection bypass active)")
        except Exception as e:
            logger.error(f"Chrome error: {e}")
            raise

    def _manual_login_wait(self):
        """Wait for user to manually login to X.com"""
        try:
            logger.info("=" * 70)
            logger.info("MANUEL LOGIN GEREKLİ")
            logger.info("=" * 70)

            logger.info("X.com login sayfası açılıyor...")
            self.driver.get("https://x.com/login")
            time.sleep(2)

            logger.info("MANUEL LOGIN BEKLENİYOR")
            logger.info("Lütfen açılan Brave browser'da: 1. Email/username, 2. Password, 3. Login")
            logger.info("Sistem 120 saniye bekleyecek...")

            # Wait for login (max 120 seconds)
            for i in range(120):
                # Check if at home page
                current_url = self.driver.current_url
                if "x.com/login" not in current_url and "x.com/i/flow" not in current_url:
                    self.logged_in = True
                    logger.info("LOGIN BAŞARILI! Scraping başlıyor...")
                    return True

                # Check for navigation element
                try:
                    self.driver.find_element(By.XPATH, "//nav[@aria-label='Primary navigation']")
                    self.logged_in = True
                    logger.info("LOGIN BAŞARILI! Scraping başlıyor...")
                    return True
                except Exception:
                    pass

                # Progress indicator every 10 seconds
                if i % 10 == 0 and i > 0:
                    logger.info(f"Bekleniyor... {i}s geçti, {120 - i}s kaldı")

                time.sleep(1)

            logger.warning("120 saniye doldu, login algılanamadı")
            self.logged_in = False
            return False

        except Exception as e:
            logger.error(f"Login hatası: {e}")
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
        except Exception:
            return None

    def _is_within_days(self, tweet_date: datetime, days_back: int) -> bool:
        """Check if tweet is within last N days"""
        if not tweet_date:
            return True  # Unknown date = include

        try:
            cutoff_date = datetime.now(tweet_date.tzinfo) - timedelta(days=days_back)
            return tweet_date >= cutoff_date
        except Exception:
            return True

    def _parse_metric(self, text: str) -> int:
        """Parse engagement metrics like '1.2K', '5.5M', etc."""
        try:
            text = text.strip().upper()
            if not text:
                return 0

            # Remove non-numeric characters except K, M, B, decimal point
            text = ''.join(c for c in text if c.isdigit() or c in ['.', 'K', 'M', 'B'])

            if 'K' in text:
                return int(float(text.replace('K', '')) * 1000)
            elif 'M' in text:
                return int(float(text.replace('M', '')) * 1000000)
            elif 'B' in text:
                return int(float(text.replace('B', '')) * 1000000000)
            else:
                return int(text) if text else 0
        except Exception:
            return 0

    @retry_on_scraping_error
    def scrape_tweets(self, username: str, max_tweets: int = 500, days_back: int = 90) -> List[Dict]:
        """
        Scrape tweets - AGGRESSIVE TIME-BASED COLLECTION

        Strategy:
        1. Scroll aggressively (200 scrolls max)
        2. Skip tweets outside time window (no early stop!)
        3. Continue until max_scrolls OR max_tweets reached
        4. Collect ALL tweets within time window
        """
        if not self.driver or not SELENIUM_AVAILABLE:
            return []

        tweets: List[Dict] = []
        url = f"https://x.com/{username}"

        logger.info(f"Scraping: @{username}")

        try:
            self.driver.get(url)
            time.sleep(random.uniform(2, 3))

            # Check if profile exists
            try:
                self.driver.find_element(By.XPATH, "//span[contains(text(), 'does not exist')]")
                logger.warning(f"@{username} not found")
                return []
            except NoSuchElementException:
                pass  # Profile exists, continue

            # Wait for tweets to load
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//article[@data-testid='tweet']"))
                )
            except TimeoutException:
                logger.warning(f"Timeout waiting for tweets to load for @{username}")
                pass

            # ==========================================
            # TIME-BASED SCROLLING STRATEGY
            # ==========================================
            seen_tweets = set()
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            scroll_count = 0
            max_scrolls = 500  # Increased for 3-month window
            consecutive_no_new = 0  # Counter for stale scrolls
            max_consecutive_no_new = 20  # More tolerance for lazy loading
            consecutive_old_tweets = 0  # Track old tweets to detect 3-month boundary
            max_consecutive_old = 15  # Stop after 15 consecutive old tweets (more tolerant)
            reached_date_limit = False

            while scroll_count < max_scrolls and len(tweets) < max_tweets and not reached_date_limit:
                old_tweet_count = len(tweets)

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
                            # Click "Show more" button if present (for long tweets)
                            try:
                                show_more_btn = element.find_element(
                                    By.XPATH,
                                    ".//button[@data-testid='tweet-text-show-more-link']"
                                )
                                show_more_btn.click()
                                time.sleep(0.3)  # Brief wait for expansion
                            except (NoSuchElementException, StaleElementReferenceException):
                                pass  # No "Show more" button or element became stale

                            # Get FULL tweet text (after expanding if needed)
                            text_elem = element.find_element(
                                By.XPATH,
                                ".//div[@data-testid='tweetText']"
                            )
                            tweet_text = text_elem.text.strip()

                            # Get timestamp
                            tweet_date = None
                            try:
                                time_elem = element.find_element(By.XPATH, ".//time")
                                timestamp_str = time_elem.get_attribute("datetime")
                                tweet_date = self._parse_tweet_date(timestamp_str)
                            except (NoSuchElementException, StaleElementReferenceException):
                                tweet_date = None

                            # Deduplication first
                            if not tweet_text or tweet_text in seen_tweets or len(tweet_text) < 5:
                                continue

                            # ==========================================
                            # RT DETECTION (before time filter)
                            # ==========================================
                            is_rt = False
                            rt_from = None

                            try:
                                # Get tweet author handle
                                author_elem = element.find_element(
                                    By.XPATH,
                                    ".//div[@data-testid='User-Name']//a[contains(@href, '/')]"
                                )
                                author_href = author_elem.get_attribute("href") or ""
                                tweet_author = author_href.split("/")[-1] if author_href else ""

                                # Check if tweet author != profile owner
                                if tweet_author and tweet_author.lower() != username.lower():
                                    is_rt = True
                                    rt_from = tweet_author
                            except (NoSuchElementException, StaleElementReferenceException):
                                pass

                            # Fallback: Text-based RT detection
                            if not is_rt and tweet_text.strip().startswith("RT @"):
                                is_rt = True
                                try:
                                    rt_part = tweet_text.split(":")[0]
                                    rt_from = rt_part.replace("RT", "").replace("@", "").strip()
                                except Exception:
                                    pass

                            # ==========================================
                            # TIME FILTER: Only for original tweets
                            # Retweets show original date, so skip time check for RTs
                            # ==========================================
                            if not is_rt and tweet_date and not self._is_within_days(tweet_date, days_back):
                                consecutive_old_tweets += 1
                                if consecutive_old_tweets >= max_consecutive_old:
                                    # Reached 3-month boundary, stop scrolling
                                    reached_date_limit = True
                                    break
                                continue
                            elif not is_rt:
                                # Reset counter only for original tweets within range
                                consecutive_old_tweets = 0

                            # ==========================================
                            # ENGAGEMENT METRICS
                            # ==========================================
                            likes = 0
                            replies = 0
                            retweets_count = 0
                            views = 0

                            try:
                                like_btn = element.find_element(By.XPATH, ".//button[@data-testid='like']")
                                like_aria = like_btn.get_attribute("aria-label") or ""
                                if like_aria:
                                    like_parts = like_aria.split()
                                    if len(like_parts) > 0:
                                        likes = self._parse_metric(like_parts[0])
                            except (NoSuchElementException, StaleElementReferenceException):
                                pass

                            try:
                                reply_btn = element.find_element(By.XPATH, ".//button[@data-testid='reply']")
                                reply_aria = reply_btn.get_attribute("aria-label") or ""
                                if reply_aria:
                                    reply_parts = reply_aria.split()
                                    if len(reply_parts) > 0:
                                        replies = self._parse_metric(reply_parts[0])
                            except (NoSuchElementException, StaleElementReferenceException):
                                pass

                            try:
                                rt_btn = element.find_element(By.XPATH, ".//button[@data-testid='retweet']")
                                rt_aria = rt_btn.get_attribute("aria-label") or ""
                                if rt_aria:
                                    rt_parts = rt_aria.split()
                                    if len(rt_parts) > 0:
                                        retweets_count = self._parse_metric(rt_parts[0])
                            except (NoSuchElementException, StaleElementReferenceException):
                                pass

                            try:
                                views_link = element.find_element(
                                    By.XPATH,
                                    ".//a[contains(@aria-label, 'görüntülenme') or contains(@aria-label, 'views')]"
                                )
                                views_aria = views_link.get_attribute("aria-label") or ""
                                if views_aria:
                                    views_parts = views_aria.split()
                                    if len(views_parts) > 0:
                                        views = self._parse_metric(views_parts[0])
                            except (NoSuchElementException, StaleElementReferenceException):
                                pass

                            # Save tweet (full text, no character limit)
                            tweets.append({
                                "text": tweet_text,
                                "timestamp": tweet_date.isoformat() if tweet_date else None,
                                "username": username,
                                "is_retweet": is_rt,
                                "retweet_from": rt_from,
                                "likes": likes,
                                "replies": replies,
                                "retweets": retweets_count,
                                "views": views,
                            })
                            seen_tweets.add(tweet_text)

                        except StaleElementReferenceException:
                            logger.debug("Stale element encountered, skipping")
                            continue
                        except Exception as e:
                            logger.warning(f"Error parsing tweet element: {e}")
                            pass
                except (TimeoutException, NoSuchElementException) as e:
                    logger.debug(f"Element search timeout/not found: {e}")
                    pass
                except Exception as e:
                    logger.warning(f"Unexpected error in tweet collection: {e}")
                    pass

                # Check if we got new tweets
                if len(tweets) == old_tweet_count:
                    consecutive_no_new += 1
                    if consecutive_no_new >= max_consecutive_no_new:
                        # No new tweets for 5 scrolls → probably at the end
                        break
                else:
                    consecutive_no_new = 0

                # ==========================================
                # SCROLL WITH TWITTER-FRIENDLY DELAY
                # ==========================================
                delay = random.uniform(1.0, 2.0)  # Slower for Twitter lazy load
                self.driver.execute_script("window.scrollBy(0, 800);")  # Smaller scroll for more tweets
                time.sleep(delay)
                scroll_count += 1

                # Check if at end
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    consecutive_no_new += 1
                    if consecutive_no_new >= max_consecutive_no_new:
                        break
                else:
                    consecutive_no_new = 0
                    last_height = new_height

            if tweets:
                if reached_date_limit:
                    logger.info(f"DONE: @{username} - {len(tweets)} tweets (3-month limit reached)")
                else:
                    logger.info(f"DONE: @{username} - {len(tweets)} tweets")
            else:
                logger.warning(f"No tweets found for @{username}")

            return tweets

        except Exception as e:
            logger.error(f"Scrape error @{username}: {e}")
            return []

    def scrape_multiple(self, usernames: List[str], max_tweets: int = 500, days_back: int = 90) -> Dict[
        str, List[Dict]]:
        """Scrape multiple users"""
        logger.info(f"START BATCH: {len(usernames)} users, {days_back} days window")

        results = {}
        for i, username in enumerate(usernames, 1):
            logger.info(f"Processing {i}/{len(usernames)}: @{username}")
            tweets = self.scrape_tweets(username, max_tweets, days_back)
            if tweets:
                results[username] = tweets

            # Rate limiting (reduced)
            if i < len(usernames):
                delay = random.uniform(1, 3)  # FASTER: 1-3s (was 2-5s)
                time.sleep(delay)

        total = sum(len(t) for t in results.values())
        logger.info(f"BATCH FINISHED: {total} total tweets")
        return results

    def close(self):
        """Close browser"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()