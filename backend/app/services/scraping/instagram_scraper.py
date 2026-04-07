#!/usr/bin/env python3
"""
📸 Instagram Scraper v1.0 - Post & Profile Collection
✅ Manual login support (like X scraper)
✅ Profile info: followers, following, posts count
✅ Posts: caption, likes, comments, date
✅ Brave browser on Windows
"""

import os
import platform
import random
import re
import time
from datetime import datetime, timedelta

from app.utils.logger import get_logger
from app.utils.retry_config import retry_on_scraping_error

logger = get_logger("InstagramScraper")

# Safe imports
try:
    from selenium.common.exceptions import (
        NoSuchElementException,
        StaleElementReferenceException,
        TimeoutException,
    )
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait
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

# Instaloader - API based scraping (faster, no browser needed)
try:
    import instaloader
    from instaloader import Profile
    INSTALOADER_AVAILABLE = True
except ImportError:
    INSTALOADER_AVAILABLE = False
    logger.info("instaloader not installed - pip install instaloader")


class InstagramScraper:
    """Instagram scraper v1.0 - Profile & Posts collection"""

    def __init__(self, headless=False, require_manual_login=True):
        self.driver = None
        self.headless = headless
        self.logged_in = False
        self.require_manual_login = require_manual_login
        # Instaloader (fast mode)
        self.insta_loader = None
        self.insta_logged_in = False

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
        """Initialize Undetected Chrome WebDriver"""
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

            # Launch undetected chrome with version matching
            self.driver = uc.Chrome(options=options, headless=False, version_main=146)

            logger.info("Browser ready (bot detection bypass active)")
        except Exception as e:
            logger.error(f"Chrome error: {e}")
            raise

    def _manual_login_wait(self):
        """Wait for user to manually login to Instagram"""
        try:
            logger.info("=" * 70)
            logger.info("MANUEL LOGIN GEREKLİ")
            logger.info("=" * 70)

            logger.info("Instagram login sayfası açılıyor...")
            self.driver.get("https://www.instagram.com/accounts/login/")
            time.sleep(3)

            # Accept cookies if present
            try:
                cookie_btn = self.driver.find_element(
                    By.XPATH,
                    "//button[contains(text(), 'Allow') or contains(text(), 'Kabul') or contains(text(), 'Accept')]"
                )
                cookie_btn.click()
                time.sleep(1)
            except NoSuchElementException:
                pass

            logger.info("MANUEL LOGIN BEKLENİYOR")
            logger.info("Lütfen açılan Brave browser'da:")
            logger.info("  1. Kullanıcı adı/email girin")
            logger.info("  2. Şifrenizi girin")
            logger.info("  3. Giriş yapın")
            logger.info("Sistem 120 saniye bekleyecek...")

            # Wait for login (max 120 seconds)
            for i in range(120):
                current_url = self.driver.current_url

                # Check if logged in (not on login page)
                if "instagram.com/accounts/login" not in current_url:
                    # Double check by looking for profile icon
                    try:
                        self.driver.find_element(
                            By.XPATH,
                            "//span[@aria-label='Profile' or @aria-label='Profil']"
                        )
                        self.logged_in = True
                        logger.info("LOGIN BAŞARILI! Scraping başlıyor...")
                        return True
                    except NoSuchElementException:
                        pass

                    # Alternative check - home feed
                    try:
                        self.driver.find_element(
                            By.XPATH,
                            "//a[@href='/direct/inbox/' or contains(@href, '/explore/')]"
                        )
                        self.logged_in = True
                        logger.info("LOGIN BAŞARILI! Scraping başlıyor...")
                        return True
                    except NoSuchElementException:
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

    def _parse_count(self, text: str) -> int:
        """
        Parse count strings - handles both EN and TR formats:
        - EN: "72.4K", "1,234", "5.5M"
        - TR: "72,4B", "1.234", "5,5M" (comma=decimal, dot=thousands)

        Instagram uses 'B' for 'Bin' (thousand) in Turkish, same as 'K'
        """
        if not text:
            return 0

        try:
            original = text.strip().upper()

            # Check for suffix (K, M, B for thousand/million/billion)
            # Note: In Turkish Instagram, "B" means "Bin" (thousand), not billion
            # But we'll check context - if number is small like "72,4B" it's thousand
            suffix_match = re.search(r'([KMBTN]+)$', original)
            suffix = suffix_match.group(1) if suffix_match else ''

            # Extract the numeric part
            num_str = re.sub(r'[KMBTN]+$', '', original).strip()

            if not num_str:
                return 0

            # Determine format: TR uses comma as decimal, EN uses period
            # Heuristic: If there's a comma followed by 1-2 digits at end, it's decimal
            # "72,4" -> TR decimal (72.4)
            # "1,234" -> EN thousands (1234)
            # "72.400" -> TR thousands (72400)
            # "72.4" -> EN decimal (72.4)

            has_comma = ',' in num_str
            has_dot = '.' in num_str

            if has_comma and has_dot:
                # Both present - determine which is decimal
                # Last separator before suffix is likely decimal if followed by 1-2 digits
                comma_pos = num_str.rfind(',')
                dot_pos = num_str.rfind('.')

                if comma_pos > dot_pos:
                    # Comma is last: "1.234,5" -> TR format
                    num_str = num_str.replace('.', '').replace(',', '.')
                else:
                    # Dot is last: "1,234.5" -> EN format
                    num_str = num_str.replace(',', '')

            elif has_comma:
                # Only comma: could be TR decimal or EN thousands
                parts = num_str.split(',')
                if len(parts) == 2 and len(parts[1]) <= 2:
                    # "72,4" -> TR decimal = 72.4
                    num_str = num_str.replace(',', '.')
                else:
                    # "1,234" -> EN thousands = 1234
                    num_str = num_str.replace(',', '')

            elif has_dot:
                # Only dot: could be EN decimal or TR thousands
                parts = num_str.split('.')
                if len(parts) == 2 and len(parts[1]) <= 2 and suffix:
                    # "72.4K" -> EN decimal with suffix = 72.4
                    pass  # Keep as is
                elif len(parts[-1]) == 3:
                    # "72.400" -> TR thousands = 72400
                    num_str = num_str.replace('.', '')
                # else keep as is (EN decimal)

            # Parse the number
            try:
                num = float(num_str) if num_str else 0
            except ValueError:
                # Extract just digits and one decimal point
                clean = ''.join(c for c in num_str if c.isdigit() or c == '.')
                num = float(clean) if clean else 0

            # Apply suffix multiplier
            if suffix:
                if suffix in ['K', 'B']:  # K (EN) or B/Bin (TR) = thousand
                    num *= 1_000
                elif suffix in ['M', 'MN']:
                    num *= 1_000_000
                elif suffix in ['BN', 'T']:  # Billion or Trilyon
                    num *= 1_000_000_000

            return int(num)

        except Exception:
            return 0

    def _parse_instagram_date(self, date_text: str) -> datetime | None:
        """Parse Instagram relative date format"""
        if not date_text:
            return None

        try:
            date_text = date_text.lower().strip()
            now = datetime.now()

            # "1 gün önce", "2 days ago", etc.
            if 'gün' in date_text or 'day' in date_text:
                match = re.search(r'(\d+)', date_text)
                if match:
                    days = int(match.group(1))
                    return now - timedelta(days=days)

            # "1 hafta önce", "2 weeks ago"
            if 'hafta' in date_text or 'week' in date_text:
                match = re.search(r'(\d+)', date_text)
                if match:
                    weeks = int(match.group(1))
                    return now - timedelta(weeks=weeks)

            # "1 ay önce", "2 months ago"
            if 'ay' in date_text or 'month' in date_text:
                match = re.search(r'(\d+)', date_text)
                if match:
                    months = int(match.group(1))
                    return now - timedelta(days=months * 30)

            # "1 yıl önce", "2 years ago"
            if 'yıl' in date_text or 'year' in date_text:
                match = re.search(r'(\d+)', date_text)
                if match:
                    years = int(match.group(1))
                    return now - timedelta(days=years * 365)

            # "1 saat önce", "2 hours ago"
            if 'saat' in date_text or 'hour' in date_text:
                match = re.search(r'(\d+)', date_text)
                if match:
                    hours = int(match.group(1))
                    return now - timedelta(hours=hours)

            # "1 dakika önce", "2 minutes ago"
            if 'dakika' in date_text or 'minute' in date_text:
                match = re.search(r'(\d+)', date_text)
                if match:
                    minutes = int(match.group(1))
                    return now - timedelta(minutes=minutes)

            return now  # Default to now if can't parse

        except Exception:
            return None

    @retry_on_scraping_error
    def scrape_profile(self, username: str) -> dict | None:
        """
        Scrape profile info: followers, following, posts count

        Returns:
            {
                'username': str,
                'full_name': str,
                'bio': str,
                'followers': int,
                'following': int,
                'posts_count': int,
                'scrape_date': str (YYYY-MM-DD)
            }
        """
        if not self.driver:
            logger.error("Driver yok")
            return None

        url = f"https://www.instagram.com/{username}/"

        try:
            self.driver.get(url)
            time.sleep(random.uniform(3, 5))

            # Check if profile exists
            try:
                self.driver.find_element(
                    By.XPATH,
                    "//span[contains(text(), 'Sorry') or contains(text(), 'Üzgünüz') or contains(text(), \"isn't available\")]"
                )
                logger.warning(f"@{username}: Profil bulunamadı")
                return None
            except NoSuchElementException:
                pass  # Profile exists

            result = {
                'username': username,
                'full_name': '',
                'bio': '',
                'followers': 0,
                'following': 0,
                'posts_count': 0,
                'scrape_date': datetime.now().strftime("%Y-%m-%d")
            }

            # Wait for profile to load
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//header"))
                )
            except TimeoutException:
                pass

            # ==========================================
            # PARSE FROM META DESCRIPTION (Most reliable)
            # Format EN: "72.4K Followers, 1,283 Following, 1,570 Posts"
            # Format TR: "72,4B Takipçi, 1.283 Takip Edilen, 1.570 Gönderi"
            # ==========================================
            try:
                meta = self.driver.find_element(By.XPATH, "//meta[@name='description']")
                content = meta.get_attribute("content") or ""

                # Parse followers: English or Turkish
                # "72.4K Followers" or "72,4B Takipçi" or "72.400 Followers"
                followers_match = re.search(
                    r'([\d.,]+)\s*([KMB])?\s*(?:Followers|Takipçi|takipçi)',
                    content, re.IGNORECASE
                )
                if followers_match:
                    num_str = followers_match.group(1)
                    suffix = followers_match.group(2) or ''
                    full_str = num_str + suffix.upper()
                    result['followers'] = self._parse_count(full_str)

                # Parse following
                following_match = re.search(
                    r'([\d.,]+)\s*([KMB])?\s*(?:Following|Takip)',
                    content, re.IGNORECASE
                )
                if following_match:
                    num_str = following_match.group(1)
                    suffix = following_match.group(2) or ''
                    full_str = num_str + suffix.upper()
                    result['following'] = self._parse_count(full_str)

                # Parse posts
                posts_match = re.search(
                    r'([\d.,]+)\s*([KMB])?\s*(?:Posts|Gönderi|gönderi)',
                    content, re.IGNORECASE
                )
                if posts_match:
                    num_str = posts_match.group(1)
                    suffix = posts_match.group(2) or ''
                    full_str = num_str + suffix.upper()
                    result['posts_count'] = self._parse_count(full_str)

            except NoSuchElementException:
                pass

            # ==========================================
            # FALLBACK: Parse from page elements (if meta failed)
            # ==========================================
            if result['followers'] == 0:
                try:
                    elem = self.driver.find_element(By.CSS_SELECTOR, "a[href*='/followers/'] span span")
                    text = elem.text.strip()
                    if text:
                        result['followers'] = self._parse_count(text)
                except NoSuchElementException:
                    pass

            if result['following'] == 0:
                try:
                    elem = self.driver.find_element(By.CSS_SELECTOR, "a[href*='/following/'] span span")
                    text = elem.text.strip()
                    if text:
                        result['following'] = self._parse_count(text)
                except NoSuchElementException:
                    pass

            # ==========================================
            # SANITY CHECK - No account has > 1 billion followers
            # ==========================================
            MAX_REALISTIC_FOLLOWERS = 500_000_000  # 500 million (most followed ~600M)
            if result['followers'] > MAX_REALISTIC_FOLLOWERS:
                logger.warning(f"@{username}: Unrealistic followers {result['followers']:,}, resetting to 0")
                result['followers'] = 0
            if result['following'] > 100_000_000:
                result['following'] = 0
            if result['posts_count'] > 1_000_000:
                result['posts_count'] = 0

            # ==========================================
            # FULL NAME
            # ==========================================
            try:
                name_elem = self.driver.find_element(
                    By.XPATH,
                    "//header//span[contains(@class, 'x1lliihq')]"
                )
                result['full_name'] = name_elem.text.strip()
            except NoSuchElementException:
                pass

            # ==========================================
            # BIO
            # ==========================================
            try:
                bio_elem = self.driver.find_element(
                    By.XPATH,
                    "//header//div[contains(@class, '_aa_c')]//span"
                )
                result['bio'] = bio_elem.text.strip()
            except NoSuchElementException:
                pass

            return result

        except Exception as e:
            logger.error(f"@{username}: Profile scrape hatası - {str(e)[:50]}")
            return None

    @retry_on_scraping_error
    def scrape_posts(self, username: str, max_posts: int = 50, days_back: int = 90) -> list[dict]:
        """
        Scrape posts from a profile - Updated for Instagram 2026 DOM

        Returns list of:
            {
                'username': str,
                'caption': str,
                'likes': int,
                'comments': int,
                'post_date': str (ISO format),
                'post_url': str,
                'is_video': bool
            }
        """
        if not self.driver:
            logger.error("Driver yok")
            return []

        posts: list[dict] = []
        url = f"https://www.instagram.com/{username}/"

        logger.info(f"Scraping posts: @{username}")

        try:
            self.driver.get(url)
            time.sleep(random.uniform(4, 6))

            # Check if profile exists
            page_source = self.driver.page_source.lower()
            if "sorry, this page" in page_source or "sayfa bulunamadı" in page_source:
                logger.warning(f"@{username} not found")
                return []

            # Check if private
            if "this account is private" in page_source or "bu hesap gizli" in page_source:
                logger.warning(f"@{username} is private")
                return []

            # Multiple selector strategies for finding posts
            post_selectors = [
                "a[href*='/p/']",
                "a[href*='/reel/']",
                "div._aagw a",  # Grid item links
                "article a[href*='/p/']",
                "main a[href*='/p/']",
            ]

            # Wait for any posts to appear
            posts_found = False
            for selector in post_selectors[:2]:
                try:
                    WebDriverWait(self.driver, 8).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    posts_found = True
                    logger.info(f"Posts found with selector: {selector}")
                    break
                except TimeoutException:
                    continue

            if not posts_found:
                # Try scrolling down first
                self.driver.execute_script("window.scrollTo(0, 500);")
                time.sleep(2)

            # Collect post links
            seen_posts = set()
            scroll_count = 0
            max_scrolls = 50
            consecutive_no_new = 0

            while scroll_count < max_scrolls and len(posts) < max_posts:
                # Find all post links using multiple methods
                post_links = []

                for selector in post_selectors:
                    try:
                        links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        post_links.extend(links)
                    except Exception:
                        pass

                # Also try XPath as fallback
                try:
                    xpath_links = self.driver.find_elements(
                        By.XPATH,
                        "//a[contains(@href, '/p/') or contains(@href, '/reel/')]"
                    )
                    post_links.extend(xpath_links)
                except Exception:
                    pass

                # Remove duplicates while preserving order
                unique_hrefs = []
                for link in post_links:
                    try:
                        href = link.get_attribute("href")
                        if href and ('/p/' in href or '/reel/' in href):
                            if href not in seen_posts and href not in unique_hrefs:
                                unique_hrefs.append(href)
                    except StaleElementReferenceException:
                        continue

                # Process new posts
                for href in unique_hrefs:
                    if len(posts) >= max_posts:
                        break

                    if href in seen_posts:
                        continue

                    seen_posts.add(href)

                    try:
                        # Open post and get details
                        post_data = self._scrape_single_post(href, username)
                        if post_data:
                            # Check date limit
                            if post_data.get('post_date'):
                                try:
                                    post_date_str = post_data['post_date'].replace('Z', '+00:00')
                                    if '+' not in post_date_str and 'T' in post_date_str:
                                        post_date_str = post_date_str + '+00:00'
                                    post_date = datetime.fromisoformat(post_date_str)
                                    cutoff = datetime.now(post_date.tzinfo) - timedelta(days=days_back)
                                    if post_date < cutoff:
                                        logger.info(f"Reached {days_back} day limit")
                                        return posts
                                except Exception:
                                    pass  # Continue if date parsing fails

                            posts.append(post_data)
                            caption_preview = post_data.get('caption', '')[:60] + '...' if post_data.get('caption') else '(caption yok)'
                            logger.info(f"Post {len(posts)}/{max_posts}: {post_data.get('likes', 0)} likes, {post_data.get('comments', 0)} comments | Caption: {caption_preview}")

                    except Exception as e:
                        logger.debug(f"Post error: {str(e)[:30]}")
                        continue

                # Check progress
                old_count = len(seen_posts)

                # Scroll down
                self.driver.execute_script("window.scrollBy(0, 1000);")
                time.sleep(random.uniform(1.5, 2.5))
                scroll_count += 1

                # Check if we're getting new posts
                if len(seen_posts) == old_count:
                    consecutive_no_new += 1
                    if consecutive_no_new >= 3:
                        # Try one more aggressive scroll
                        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(2)
                        consecutive_no_new = 0
                        scroll_count += 5  # Count as multiple scrolls
                else:
                    consecutive_no_new = 0

                # Progress log every 10 scrolls
                if scroll_count % 10 == 0:
                    logger.info(f"Scroll {scroll_count}: {len(posts)} posts, {len(seen_posts)} seen")

            logger.info(f"DONE: @{username} - {len(posts)} posts collected")
            return posts

        except Exception as e:
            logger.error(f"Scrape error @{username}: {e}")
            return posts  # Return what we have

    def _extract_engagement_from_dom(self) -> dict:
        """
        Extract likes and comments from Instagram DOM (2026 method).
        Instagram uses spans with specific classes for engagement counts.
        """
        result = {'likes': 0, 'comments': 0}

        try:
            # Method 1: Find the engagement section and get spans
            # Structure: <section> contains like count span, comment icon, comment count span
            # Class pattern: x1ypdohk x1s688f x2fvf9 xe9ewy2

            # Find all spans with the engagement count class
            count_spans = self.driver.find_elements(
                By.CSS_SELECTOR,
                "section span.x1ypdohk.x1s688f.x2fvf9.xe9ewy2"
            )

            if len(count_spans) >= 2:
                # First span = likes, Second span = comments
                likes_text = count_spans[0].text.strip()
                comments_text = count_spans[1].text.strip()

                if likes_text:
                    result['likes'] = self._parse_count(likes_text)
                if comments_text:
                    result['comments'] = self._parse_count(comments_text)

                logger.debug(f"DOM extraction: {result['likes']} likes, {result['comments']} comments")
                return result

            # Method 2: Alternative selector - look for spans near like/comment icons
            # Find section with engagement buttons
            sections = self.driver.find_elements(By.CSS_SELECTOR, "section.x6s0dn4")
            for section in sections:
                spans = section.find_elements(By.CSS_SELECTOR, "span[role='button'][tabindex='0']")
                numbers = []
                for span in spans:
                    text = span.text.strip()
                    if text and text.isdigit() or any(c.isdigit() for c in text):
                        numbers.append(self._parse_count(text))

                if len(numbers) >= 2:
                    result['likes'] = numbers[0]
                    result['comments'] = numbers[1]
                    return result

            # Method 3: XPath fallback - look for aria-label patterns
            try:
                # Look for like button and get adjacent text
                like_section = self.driver.find_element(
                    By.XPATH,
                    "//svg[@aria-label='Beğen' or @aria-label='Like']/ancestor::div[1]/following-sibling::span"
                )
                if like_section:
                    result['likes'] = self._parse_count(like_section.text)
            except NoSuchElementException:
                pass

            try:
                # Look for comment button and get adjacent text
                comment_section = self.driver.find_element(
                    By.XPATH,
                    "//svg[@aria-label='Yorum Yap' or @aria-label='Comment']/ancestor::div[1]/following-sibling::span"
                )
                if comment_section:
                    result['comments'] = self._parse_count(comment_section.text)
            except NoSuchElementException:
                pass

        except Exception as e:
            logger.debug(f"DOM extraction error: {e}")

        return result

    def _scrape_single_post(self, post_url: str, username: str) -> dict | None:
        """Scrape details from a single post - Updated for Instagram 2026"""
        try:
            # Open post
            self.driver.get(post_url)
            time.sleep(random.uniform(2, 4))

            result = {
                'username': username,
                'caption': '',
                'likes': 0,
                'comments': 0,
                'post_date': None,
                'post_url': post_url,
                'is_video': False
            }

            # ==========================================
            # METHOD 1: Extract from DOM (2026 - most reliable)
            # ==========================================
            dom_data = self._extract_engagement_from_dom()
            if dom_data:
                result['likes'] = dom_data.get('likes', 0)
                result['comments'] = dom_data.get('comments', 0)

            # ==========================================
            # METHOD 2: DOM Extraction (fallback)
            # ==========================================

            # Check if video/reel
            if not result['is_video']:
                try:
                    self.driver.find_element(By.CSS_SELECTOR, "video")
                    result['is_video'] = True
                except NoSuchElementException:
                    pass

            # ==========================================
            # CAPTION - Multiple selector strategies (2026 updated)
            # ==========================================
            if not result['caption']:
                # Try to find the caption - it's usually a span after the username in the first comment
                caption_patterns = [
                    # 2026 Instagram: caption is in span with x126k92a class (after username)
                    ("css", "span.x193iq5w.xeuugli.x13faqbe.x1vvkbs.x126k92a"),
                    # Alternative: look for the first span with dir='auto' that has substantial text
                    ("xpath", "//div[contains(@class, '_a9zs')]//span[@dir='auto']"),
                    # Legacy selectors
                    ("css", "h1._ap3a"),
                    ("css", "div._a9zs span"),
                    ("css", "span._ap3a._aaco._aacu._aacx._aad7._aade"),
                    # Find span after username link in the comment section
                    ("xpath", "//span[contains(@class, 'x126k92a')]"),
                    ("xpath", "//article//span[@dir='auto'][string-length(text()) > 20]"),
                ]

                for method, selector in caption_patterns:
                    try:
                        if method == "css":
                            elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                        else:
                            elem = self.driver.find_element(By.XPATH, selector)
                        text = elem.text.strip()
                        # Caption should be substantial (not just username or timestamp)
                        if text and len(text) > 10 and not text.startswith('@'):
                            result['caption'] = text[:2500]
                            logger.info(f"  -> Caption bulundu ({method}): {text[:50]}...")
                            break
                    except NoSuchElementException:
                        continue

                # Fallback: Try to get from meta description
                if not result['caption']:
                    try:
                        meta = self.driver.find_element(By.XPATH, "//meta[@property='og:description']")
                        content = meta.get_attribute("content")
                        if content:
                            # Remove "X likes, Y comments - " prefix
                            import re as re_module
                            cleaned = re_module.sub(r'^[\d,.]+ likes?, [\d,.]+ comments? - ', '', content)
                            if cleaned and len(cleaned) > 10:
                                result['caption'] = cleaned[:2500]
                                logger.info(f"  -> Caption meta'dan bulundu: {cleaned[:50]}...")
                    except NoSuchElementException:
                        pass

            # Caption bulunamadıysa log
            if not result['caption']:
                logger.debug(f"  -> Caption bulunamadı: {post_url}")

            # ==========================================
            # LIKES - Multiple strategies
            # ==========================================
            if result['likes'] == 0:
                likes_patterns = [
                    # CSS selectors
                    ("css", "a[href*='/liked_by/'] span"),
                    ("css", "section span[class*='_ae']"),
                    ("css", "span.x1lliihq"),  # 2026 class
                    # XPath patterns
                    ("xpath", "//a[contains(@href, '/liked_by/')]/span"),
                    ("xpath", "//section//span[contains(text(), 'like')]"),
                    ("xpath", "//section//span[contains(text(), 'beğenme')]"),
                    ("xpath", "//button[contains(@class, '_abl-')]//span"),
                    # 2026 patterns
                    ("xpath", "//span[contains(@class, 'x1lliihq') and contains(text(), ',')]"),
                ]

                for method, selector in likes_patterns:
                    try:
                        if method == "css":
                            elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                        else:
                            elem = self.driver.find_element(By.XPATH, selector)
                        text = elem.text.strip()
                        if text:
                            likes_count = self._parse_count(text)
                            if likes_count > 0:
                                result['likes'] = likes_count
                                break
                    except NoSuchElementException:
                        continue

                # Fallback: parse from page source
                if result['likes'] == 0:
                    try:
                        page_source = self.driver.page_source
                        match = re.search(r'([\d,\.]+)\s*(?:likes|beğenme|like)', page_source, re.IGNORECASE)
                        if match:
                            result['likes'] = self._parse_count(match.group(1))
                    except Exception:
                        pass

            # ==========================================
            # COMMENTS COUNT - Multiple strategies (2026 updated)
            # ==========================================
            if result['comments'] == 0:
                comment_patterns = [
                    # "View all X comments" / "Tüm yorumları gör (X)"
                    ("xpath", "//span[contains(text(), 'View all') and contains(text(), 'comment')]"),
                    ("xpath", "//span[contains(text(), 'Tüm') and contains(text(), 'yorum')]"),
                    ("xpath", "//a[contains(text(), 'View all') and contains(text(), 'comment')]"),
                    ("xpath", "//a[contains(text(), 'comment')]"),
                    ("xpath", "//a[contains(text(), 'yorum')]"),
                    ("xpath", "//span[contains(text(), 'comment')]"),
                    ("xpath", "//span[contains(text(), 'yorum')]"),
                    # CSS fallbacks
                    ("css", "a[href*='/comments/'] span"),
                    ("css", "span.x1lliihq"),
                ]

                for method, selector in comment_patterns:
                    try:
                        if method == "css":
                            elems = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        else:
                            elems = self.driver.find_elements(By.XPATH, selector)

                        for elem in elems:
                            text = elem.text.strip().lower()
                            # Look for "View all 123 comments" or "123 yorum"
                            if 'comment' in text or 'yorum' in text:
                                match = re.search(r'([\d,\.]+)', text)
                                if match:
                                    comments_count = self._parse_count(match.group(1))
                                    if comments_count > 0:
                                        result['comments'] = comments_count
                                        break
                        if result['comments'] > 0:
                            break
                    except NoSuchElementException:
                        continue

                # Fallback: Count actual comment elements on page
                if result['comments'] == 0:
                    try:
                        # Count visible comment elements
                        comment_elems = self.driver.find_elements(
                            By.XPATH,
                            "//ul//li[contains(@class, '_a9z')]//span[contains(@class, '_ap3a')]"
                        )
                        if len(comment_elems) > 1:  # More than just the caption
                            result['comments'] = len(comment_elems) - 1
                    except Exception:
                        pass

                # Final fallback: Parse page source for comment count
                if result['comments'] == 0:
                    try:
                        page_source = self.driver.page_source
                        # Look for "View all X comments" pattern
                        patterns = [
                            r'View all\s*([\d,\.]+)\s*comment',
                            r'Tüm\s*yorumları\s*gör\s*\(([\d,\.]+)\)',
                            r'([\d,\.]+)\s*(?:comment|yorum)',
                        ]
                        for pattern in patterns:
                            match = re.search(pattern, page_source, re.IGNORECASE)
                            if match:
                                result['comments'] = self._parse_count(match.group(1))
                                if result['comments'] > 0:
                                    break
                    except Exception:
                        pass

            # ==========================================
            # DATE - Get from time element
            # ==========================================
            if not result['post_date']:
                try:
                    time_elem = self.driver.find_element(By.CSS_SELECTOR, "time")
                    datetime_attr = time_elem.get_attribute("datetime")
                    if datetime_attr:
                        result['post_date'] = datetime_attr
                    else:
                        title = time_elem.get_attribute("title")
                        if title:
                            parsed = self._parse_instagram_date(title)
                            if parsed:
                                result['post_date'] = parsed.isoformat()
                except NoSuchElementException:
                    result['post_date'] = datetime.now().isoformat()

            logger.info(f"  -> Scraped: {result['likes']} likes, {result['comments']} comments")
            return result

        except Exception as e:
            logger.debug(f"Single post error: {e}")
            return None

    def scrape_user_complete(self, username: str, max_posts: int = 50, days_back: int = 90) -> dict:
        """
        Scrape both profile and posts for a user

        Returns:
            {
                'profile': {...},
                'posts': [...]
            }
        """
        logger.info(f"Complete scrape: @{username}")

        profile = self.scrape_profile(username)
        posts = self.scrape_posts(username, max_posts, days_back)

        return {
            'profile': profile,
            'posts': posts
        }

    def scrape_multiple(self, usernames: list[str], max_posts: int = 50, days_back: int = 90) -> dict[str, dict]:
        """Scrape multiple users"""
        logger.info(f"START BATCH: {len(usernames)} users")

        results = {}
        for i, username in enumerate(usernames, 1):
            logger.info(f"Processing {i}/{len(usernames)}: @{username}")
            data = self.scrape_user_complete(username, max_posts, days_back)
            results[username] = data

            # Rate limiting
            if i < len(usernames):
                delay = random.uniform(5, 10)  # Instagram is stricter
                time.sleep(delay)

        return results

    def update_post_engagement(self, post_url: str) -> dict | None:
        """
        Re-visit a single post URL to get updated engagement data (likes, comments, caption).
        Use this to update existing posts in database.

        Returns:
            {'likes': int, 'comments': int, 'is_video': bool, 'caption': str} or None
        """
        if not self.driver:
            logger.error("Driver yok")
            return None

        try:
            self.driver.get(post_url)
            time.sleep(random.uniform(2, 4))

            result = {'likes': 0, 'comments': 0, 'is_video': False, 'caption': ''}

            # Extract engagement from DOM (2026 method)
            dom_data = self._extract_engagement_from_dom()
            if dom_data:
                result['likes'] = dom_data.get('likes', 0)
                result['comments'] = dom_data.get('comments', 0)

            # Check if video
            try:
                self.driver.find_element(By.CSS_SELECTOR, "video")
                result['is_video'] = True
            except NoSuchElementException:
                pass

            # Extract caption (2026 method)
            caption_patterns = [
                ("css", "span.x193iq5w.xeuugli.x13faqbe.x1vvkbs.x126k92a"),
                ("xpath", "//span[contains(@class, 'x126k92a')]"),
                ("xpath", "//div[contains(@class, '_a9zs')]//span[@dir='auto']"),
                ("css", "h1._ap3a"),
            ]

            for method, selector in caption_patterns:
                try:
                    if method == "css":
                        elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    else:
                        elem = self.driver.find_element(By.XPATH, selector)
                    text = elem.text.strip()
                    if text and len(text) > 10 and not text.startswith('@'):
                        result['caption'] = text[:2500]
                        logger.info(f"  -> Caption ({method}): {text[:60]}...")
                        break
                except NoSuchElementException:
                    continue

            # Fallback: og:description meta tag
            if not result['caption']:
                try:
                    meta = self.driver.find_element(By.XPATH, "//meta[@property='og:description']")
                    content = meta.get_attribute("content")
                    if content:
                        # Remove "X likes, Y comments - " prefix
                        cleaned = re.sub(r'^[\d,.]+ likes?, [\d,.]+ comments? - ', '', content)
                        if cleaned and len(cleaned) > 10:
                            result['caption'] = cleaned[:2500]
                            logger.info(f"  -> Caption (meta): {cleaned[:60]}...")
                except NoSuchElementException:
                    pass

            if not result['caption']:
                logger.warning("  -> Caption bulunamadi!")

            return result

        except Exception as e:
            logger.error(f"Update engagement error: {e}")
            return None

    def batch_update_engagement(self, post_urls: list[str], delay: float = 2.0) -> dict[str, dict]:
        """
        Update engagement for multiple posts.

        Args:
            post_urls: List of Instagram post URLs
            delay: Delay between requests (seconds)

        Returns:
            {post_url: {'likes': int, 'comments': int}, ...}
        """
        results = {}
        total = len(post_urls)

        for i, url in enumerate(post_urls, 1):
            logger.info(f"[{i}/{total}] Updating: {url}")

            data = self.update_post_engagement(url)
            if data:
                results[url] = data
                logger.info(f"  -> {data['likes']} likes, {data['comments']} comments")
            else:
                logger.warning("  -> Failed to update")

            if i < total:
                time.sleep(delay + random.uniform(0, 1))

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

    # =========================================================================
    # INSTALOADER METHODS - API based, faster, no browser needed
    # =========================================================================

    def init_instaloader(self, username: str = None, password: str = None, session_file: str = None) -> bool:
        """
        Initialize instaloader for API-based scraping (10-20x faster than Selenium)

        Args:
            username: Instagram username for login
            password: Instagram password
            session_file: Path to saved session file

        Returns:
            True if initialized successfully
        """
        if not INSTALOADER_AVAILABLE:
            logger.error("instaloader not installed! pip install instaloader")
            return False

        try:
            self.insta_loader = instaloader.Instaloader(
                download_pictures=False,
                download_videos=False,
                download_video_thumbnails=False,
                download_geotags=False,
                download_comments=False,
                save_metadata=False,
                compress_json=False,
                post_metadata_txt_pattern='',
                max_connection_attempts=3,
                request_timeout=30,
            )

            # Try to load existing session
            if session_file and os.path.exists(session_file):
                try:
                    self.insta_loader.load_session_from_file(username, session_file)
                    self.insta_logged_in = True
                    logger.info(f"Instaloader session loaded from {session_file}")
                    return True
                except Exception as e:
                    logger.warning(f"Could not load session: {e}")

            # Login if credentials provided
            if username and password:
                try:
                    self.insta_loader.login(username, password)
                    self.insta_logged_in = True
                    logger.info(f"Instaloader logged in as @{username}")

                    # Save session
                    if session_file:
                        self.insta_loader.save_session_to_file(session_file)
                        logger.info(f"Session saved to {session_file}")
                    return True
                except Exception as e:
                    logger.error(f"Instaloader login failed: {e}")
                    return False

            # No login - limited functionality
            self.insta_logged_in = False
            logger.info("Instaloader initialized without login (limited access)")
            return True

        except Exception as e:
            logger.error(f"Instaloader init error: {e}")
            return False

    def scrape_profile_fast(self, username: str) -> dict | None:
        """
        Scrape profile using instaloader (faster than Selenium)

        Returns same format as scrape_profile()
        """
        if not hasattr(self, 'insta_loader') or not self.insta_loader:
            if not self.init_instaloader():
                return None

        try:
            profile = Profile.from_username(self.insta_loader.context, username)

            return {
                'username': profile.username,
                'full_name': profile.full_name or '',
                'bio': profile.biography or '',
                'followers': profile.followers,
                'following': profile.followees,
                'posts_count': profile.mediacount,
                'is_private': profile.is_private,
                'is_verified': profile.is_verified,
                'scrape_date': datetime.now().strftime("%Y-%m-%d")
            }

        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                logger.warning(f"@{username}: Profile not found")
            elif "403" in str(e) or "401" in str(e):
                logger.warning(f"@{username}: Login required (403/401)")
            else:
                logger.error(f"@{username}: {str(e)[:50]}")
            return None

    def scrape_posts_fast(
        self,
        username: str,
        max_posts: int = 50,
        since_date: datetime = None
    ) -> list[dict]:
        """
        Scrape posts using instaloader (faster than Selenium)

        Returns same format as scrape_posts()
        """
        if not hasattr(self, 'insta_loader') or not self.insta_loader:
            if not self.init_instaloader():
                return []

        if since_date is None:
            since_date = datetime(2026, 1, 1)

        posts = []

        try:
            profile = Profile.from_username(self.insta_loader.context, username)

            if profile.is_private and not getattr(self, 'insta_logged_in', False):
                logger.warning(f"@{username}: Private profile, login required")
                return []

            logger.info(f"Fetching posts @{username} (since {since_date.strftime('%Y-%m-%d')})")

            post_count = 0
            for post in profile.get_posts():
                post_date = post.date_utc

                # Skip if older than since_date
                if post_date < since_date:
                    logger.info(f"Reached posts before {since_date.strftime('%Y-%m-%d')}")
                    break

                post_data = {
                    'username': username,
                    'caption': post.caption or '',
                    'likes': post.likes,
                    'comments': post.comments,  # <-- YORUM SAYISI
                    'post_date': post_date.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                    'post_url': f"https://www.instagram.com/p/{post.shortcode}/",
                    'is_video': post.is_video,
                    'video_views': post.video_view_count if post.is_video else 0,
                }

                posts.append(post_data)
                post_count += 1

                if post_count % 10 == 0:
                    logger.info(f"@{username}: {post_count} posts...")

                if post_count >= max_posts:
                    break

                # Small delay
                time.sleep(random.uniform(0.3, 0.8))

            logger.info(f"@{username}: {len(posts)} posts collected")
            return posts

        except Exception as e:
            if "429" in str(e) or "rate" in str(e).lower():
                logger.error("RATE LIMITED! Wait 5-10 minutes")
            elif "403" in str(e) or "401" in str(e):
                logger.error(f"@{username}: Login required")
            else:
                logger.error(f"@{username}: {str(e)[:50]}")
            return posts

    def scrape_user_complete_fast(
        self,
        username: str,
        max_posts: int = 50,
        since_date: datetime = None
    ) -> dict:
        """
        Scrape profile + posts using instaloader (fast mode)
        """
        profile = self.scrape_profile_fast(username)

        time.sleep(random.uniform(1, 2))

        posts = []
        if profile and not profile.get('is_private', True):
            posts = self.scrape_posts_fast(username, max_posts, since_date)
        elif profile and profile.get('is_private'):
            logger.info(f"@{username}: Private profile, skipping posts")

        return {
            'profile': profile,
            'posts': posts
        }


# ============================================================================
# CLI / TEST
# ============================================================================

if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Instagram Scraper")
    parser.add_argument("--users", nargs="+", required=True, help="Instagram kullanıcı adları")
    parser.add_argument("--max-posts", type=int, default=50, help="Maksimum post sayısı")
    parser.add_argument("--days", type=int, default=90, help="Kaç gün geriye git")
    parser.add_argument("--profile-only", action="store_true", help="Sadece profil bilgisi")
    parser.add_argument("--output", type=str, help="JSON çıktı dosyası")
    # Fast mode (instaloader)
    parser.add_argument("--fast", action="store_true", help="Instaloader kullan (hızlı mod)")
    parser.add_argument("--login", type=str, help="Instagram kullanıcı adı (fast mode)")
    parser.add_argument("--password", type=str, help="Instagram şifre (fast mode)")

    args = parser.parse_args()

    results = {}

    if args.fast:
        # FAST MODE - Instaloader (no browser)
        print("FAST MODE - Instaloader")
        scraper = InstagramScraper(require_manual_login=False)

        if args.login and args.password:
            if not scraper.init_instaloader(args.login, args.password):
                print("Instaloader login başarısız!")
                exit(1)
        else:
            if not scraper.init_instaloader():
                print("Instaloader başlatılamadı!")
                exit(1)
            print("UYARI: Login olmadan sınırlı erişim")

        since_date = datetime.now() - timedelta(days=args.days)

        for username in args.users:
            print(f"\nScraping: @{username}")
            if args.profile_only:
                profile = scraper.scrape_profile_fast(username)
                results[username] = {'profile': profile}
                if profile:
                    print(f"  Takipci: {profile.get('followers', 0):,}")
            else:
                data = scraper.scrape_user_complete_fast(username, args.max_posts, since_date)
                results[username] = data
                # Show quick stats
                if data.get('posts'):
                    total_likes = sum(p.get('likes', 0) for p in data['posts'])
                    total_comments = sum(p.get('comments', 0) for p in data['posts'])
                    print(f"  {len(data['posts'])} post, {total_likes} like, {total_comments} yorum")

    else:
        # SELENIUM MODE - Browser with manual login
        with InstagramScraper() as scraper:
            if not scraper.logged_in:
                print("Login başarısız!")
                exit(1)

            for username in args.users:
                if args.profile_only:
                    profile = scraper.scrape_profile(username)
                    results[username] = {'profile': profile}
                else:
                    data = scraper.scrape_user_complete(username, args.max_posts, args.days)
                    results[username] = data

    # Output
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\nSonuçlar kaydedildi: {args.output}")
    else:
        print(json.dumps(results, ensure_ascii=False, indent=2))
