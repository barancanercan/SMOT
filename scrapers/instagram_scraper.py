#!/usr/bin/env python3
"""
Instagram CDP Scraper v2.0 - CDP-based post collection

- CDPBrowser singleton (Twitter scraper ile ayni pattern)
- ig_session.json cookie inject
- Post metni, begeni, yorum sayisi cekme
- SQLite kayit: instagram_posts tablosu
- Mock mod: --mock flag ile test
"""

import json
import os
import re
import random
import sqlite3
import time
import argparse
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

try:
    from .cdp_browser import CDPBrowser
except ImportError:
    from cdp_browser import CDPBrowser

logger = logging.getLogger("InstagramScraper")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(levelname)s: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Project paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
SESSION_FILE = os.path.join(PROJECT_ROOT, "ig_session.json")
DB_PATH = os.path.join(DATA_DIR, "politicians.db")


# ======================================================================
# JS: Profile info extraction
# ======================================================================

PROFILE_EXTRACT_JS = r"""
(() => {
    const result = {username: '', fullName: '', bio: '', followers: 0, following: 0, postsCount: 0};

    // Meta description: "72.4K Followers, 1,283 Following, 1,570 Posts"
    const meta = document.querySelector('meta[name="description"]');
    if (meta) {
        const content = meta.getAttribute('content') || '';

        // Followers
        const fMatch = content.match(/([\\d.,]+)\\s*([KMB])?\\s*(?:Followers|Takipçi)/i);
        if (fMatch) result.followers = fMatch[0];

        // Following
        const gMatch = content.match(/([\\d.,]+)\\s*([KMB])?\\s*(?:Following|Takip)/i);
        if (gMatch) result.following = gMatch[0];

        // Posts
        const pMatch = content.match(/([\\d.,]+)\\s*([KMB])?\\s*(?:Posts|Gönderi)/i);
        if (pMatch) result.postsCount = pMatch[0];
    }

    // Full name from header
    const nameEl = document.querySelector('header section span');
    if (nameEl) result.fullName = nameEl.innerText.trim();

    // Bio
    const bioEl = document.querySelector('header section > div:last-child span');
    if (bioEl) result.bio = bioEl.innerText.trim();

    return result;
})()
"""

# ======================================================================
# JS: Post extraction from profile grid + expanded posts
# ======================================================================

POST_EXTRACT_JS = r"""
(() => {
    const posts = [];
    const articles = document.querySelectorAll('article');

    for (const article of articles) {
        try {
            // Post text / caption
            let caption = '';
            const captionEl = article.querySelector('h1') ||
                              article.querySelector('span[dir="auto"]') ||
                              article.querySelector('div > span');
            if (captionEl) caption = captionEl.innerText.trim();

            // Likes
            let likes = '0';
            const likeSection = article.querySelector('section');
            if (likeSection) {
                const likeText = likeSection.innerText || '';
                const likeMatch = likeText.match(/([\d.,]+[KMB]?)\\s*(?:like|beğen)/i);
                if (likeMatch) likes = likeMatch[1];
            }

            // Comments
            let comments = '0';
            const commentLinks = article.querySelectorAll('a[href*="/comments/"], span');
            for (const el of commentLinks) {
                const text = el.innerText || '';
                const cMatch = text.match(/(?:View all\\s+)?([\d.,]+[KMB]?)\\s*(?:comment|yorum)/i);
                if (cMatch) { comments = cMatch[1]; break; }
            }

            // Post URL
            let postUrl = '';
            let postId = '';
            const timeLink = article.querySelector('a[href*="/p/"] time, a[href*="/reel/"] time');
            if (timeLink) {
                const parentLink = timeLink.closest('a');
                if (parentLink) {
                    postUrl = parentLink.getAttribute('href') || '';
                    const idMatch = postUrl.match(/\\/(?:p|reel)\\/([^/]+)/);
                    if (idMatch) postId = idMatch[1];
                }
            }
            // Fallback: any /p/ link
            if (!postUrl) {
                const pLink = article.querySelector('a[href*="/p/"], a[href*="/reel/"]');
                if (pLink) {
                    postUrl = pLink.getAttribute('href') || '';
                    const idMatch = postUrl.match(/\\/(?:p|reel)\\/([^/]+)/);
                    if (idMatch) postId = idMatch[1];
                }
            }

            // Timestamp
            let timestamp = '';
            const timeEl = article.querySelector('time');
            if (timeEl) {
                timestamp = timeEl.getAttribute('datetime') || timeEl.getAttribute('title') || '';
            }

            if (caption || postId) {
                posts.push({ caption, likes, comments, postUrl, postId, timestamp });
            }
        } catch (e) {}
    }
    return posts;
})()
"""

# ======================================================================
# JS: Grid post links extraction (profile page)
# ======================================================================

GRID_LINKS_JS = r"""
(() => {
    const links = [];
    const anchors = document.querySelectorAll('a[href*="/p/"], a[href*="/reel/"]');
    for (const a of anchors) {
        const href = a.getAttribute('href') || '';
        const match = href.match(/\\/(p|reel)\\/([^/]+)/);
        if (match && !links.includes(href)) {
            links.push(href);
        }
    }
    return links;
})()
"""

# ======================================================================
# JS: Single post detail extraction (when navigated to post page)
# ======================================================================

SINGLE_POST_JS = r"""
(() => {
    const result = {caption: '', likes: '0', comments: '0', timestamp: '', postId: '', isVideo: false};

    // Caption
    const h1 = document.querySelector('h1');
    if (h1) result.caption = h1.innerText.trim();
    if (!result.caption) {
        const span = document.querySelector('article span[dir="auto"]');
        if (span) result.caption = span.innerText.trim();
    }

    // Likes from section
    const sections = document.querySelectorAll('section');
    for (const sec of sections) {
        const text = sec.innerText || '';
        const m = text.match(/([\d.,]+[KMB]?)\\s*(?:like|beğen)/i);
        if (m) { result.likes = m[1]; break; }
    }

    // Fallback: button aria-label
    if (result.likes === '0') {
        const btns = document.querySelectorAll('button');
        for (const btn of btns) {
            const aria = btn.getAttribute('aria-label') || '';
            const m = aria.match(/([\d.,]+[KMB]?)\\s*(?:like|beğen)/i);
            if (m) { result.likes = m[1]; break; }
        }
    }

    // Comments count
    const commentEls = document.querySelectorAll('ul > li, span');
    for (const el of commentEls) {
        const text = el.innerText || '';
        const m = text.match(/(?:View all\\s+)?([\d.,]+[KMB]?)\\s*(?:comment|yorum)/i);
        if (m) { result.comments = m[1]; break; }
    }

    // Timestamp
    const timeEl = document.querySelector('time');
    if (timeEl) {
        result.timestamp = timeEl.getAttribute('datetime') || '';
    }

    // Post ID from URL
    const urlMatch = window.location.pathname.match(/\\/(p|reel)\\/([^/]+)/);
    if (urlMatch) result.postId = urlMatch[2];

    // Video detection
    result.isVideo = !!document.querySelector('video');

    return result;
})()
"""


# ======================================================================
# Helpers
# ======================================================================

def parse_ig_metric(value) -> int:
    """Parse Instagram metric: '72.4K' -> 72400, '1,283' -> 1283"""
    if isinstance(value, (int, float)):
        return int(value)
    if not value:
        return 0

    text = str(value).strip().upper()

    # Turkish: B = Bin (thousand), M = Milyon
    # Remove non-numeric except .,KMB
    cleaned = re.sub(r'[^\d.,KMB]', '', text)
    if not cleaned:
        return 0

    try:
        # Check for suffix
        suffix = ''
        if cleaned.endswith('K') or cleaned.endswith('B'):
            suffix = cleaned[-1]
            cleaned = cleaned[:-1]
        elif cleaned.endswith('M'):
            suffix = 'M'
            cleaned = cleaned[:-1]

        # Handle comma/dot ambiguity
        if ',' in cleaned and '.' in cleaned:
            # Both: determine which is decimal
            if cleaned.rfind(',') > cleaned.rfind('.'):
                cleaned = cleaned.replace('.', '').replace(',', '.')
            else:
                cleaned = cleaned.replace(',', '')
        elif ',' in cleaned:
            parts = cleaned.split(',')
            if len(parts) == 2 and len(parts[1]) <= 2:
                cleaned = cleaned.replace(',', '.')  # TR decimal
            else:
                cleaned = cleaned.replace(',', '')  # EN thousands
        # dots: leave as-is for now

        num = float(cleaned) if cleaned else 0

        if suffix in ('K', 'B'):
            num *= 1_000
        elif suffix == 'M':
            num *= 1_000_000

        return int(num)

    except (ValueError, TypeError):
        return 0


def parse_ig_date(timestamp_str: str) -> Optional[datetime]:
    """Parse Instagram date (ISO format or relative)"""
    if not timestamp_str:
        return None

    ts = timestamp_str.strip()

    # Try ISO formats
    for fmt in [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
    ]:
        try:
            return datetime.strptime(ts, fmt)
        except ValueError:
            continue

    try:
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        return datetime.fromisoformat(ts)
    except (ValueError, TypeError):
        pass

    # Relative dates: "2 days ago", "1 hafta once"
    now = datetime.now()
    ts_lower = ts.lower()

    patterns = [
        (r'(\d+)\s*(?:day|gün)', lambda m: timedelta(days=int(m))),
        (r'(\d+)\s*(?:week|hafta)', lambda m: timedelta(weeks=int(m))),
        (r'(\d+)\s*(?:month|ay)', lambda m: timedelta(days=int(m) * 30)),
        (r'(\d+)\s*(?:hour|saat)', lambda m: timedelta(hours=int(m))),
        (r'(\d+)\s*(?:minute|dakika)', lambda m: timedelta(minutes=int(m))),
    ]
    for pattern, delta_fn in patterns:
        match = re.search(pattern, ts_lower)
        if match:
            return now - delta_fn(match.group(1))

    return None


# ======================================================================
# Mock Data
# ======================================================================

def generate_mock_posts(username: str, count: int = 20) -> List[Dict]:
    """Generate mock Instagram posts for testing"""
    logger.info(f"MOCK MODE: Generating {count} mock posts for @{username}")

    captions = [
        "Belediye calismalarimiz devam ediyor",
        "Yeni park acilisi",
        "Vatandaslarimizla bulustu",
        "Egitim yatirimlarimiz",
        "Spora destek projesi",
        "Altyapi calismasi tamamlandi",
        "Sosyal yardim programi",
        "Kultur etkinligi",
    ]

    posts = []
    now = datetime.now()

    for i in range(count):
        days_ago = random.randint(0, 89)
        post_date = now - timedelta(days=days_ago, hours=random.randint(0, 23))

        posts.append({
            "username": username,
            "post_id": f"mock_{username}_{i}",
            "post_url": f"https://www.instagram.com/p/mock{i}/",
            "caption": f"{random.choice(captions)} @{username}",
            "likes": random.randint(0, 10000),
            "comments": random.randint(0, 500),
            "post_date": post_date.isoformat(),
            "is_video": random.random() < 0.3,
            "scraped_at": now.isoformat(),
        })

    return posts


# ======================================================================
# SQLite Save
# ======================================================================

def save_posts_to_db(posts: List[Dict], politician_id: int, db_path: str = None) -> int:
    """Save Instagram posts to SQLite"""
    if not posts:
        return 0

    db = db_path or DB_PATH
    os.makedirs(os.path.dirname(db), exist_ok=True)

    conn = sqlite3.connect(db)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=OFF")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS instagram_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                politician_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                post_id TEXT UNIQUE,
                post_url TEXT,
                post_text TEXT,
                post_date TEXT,
                likes INTEGER DEFAULT 0,
                comments INTEGER DEFAULT 0,
                is_video BOOLEAN DEFAULT 0,
                scraped_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        saved = 0
        for post in posts:
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO instagram_posts
                    (politician_id, username, post_id, post_url, post_text,
                     post_date, likes, comments, is_video)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    politician_id,
                    post.get("username", ""),
                    post.get("post_id"),
                    post.get("post_url"),
                    post.get("caption", ""),
                    post.get("post_date"),
                    post.get("likes", 0),
                    post.get("comments", 0),
                    1 if post.get("is_video") else 0,
                ))
                saved += 1
            except sqlite3.IntegrityError:
                pass

        conn.commit()
        logger.info(f"Saved {saved} posts to {db}")
        return saved

    finally:
        conn.close()


# ======================================================================
# Main Scraper
# ======================================================================

class InstagramCDPScraper:
    """CDP-based Instagram scraper"""

    def __init__(self, mock: bool = False):
        self.mock = mock
        self.browser: Optional[CDPBrowser] = None
        self._cookies_injected = False

        if not mock:
            self.browser = CDPBrowser()

    def _ensure_session(self) -> None:
        """Ensure browser running with IG cookies (once per session)"""
        self.browser.ensure_running()

        if not self._cookies_injected:
            if os.path.isfile(SESSION_FILE):
                count = self.browser.inject_cookies(SESSION_FILE, ".instagram.com")
                if count > 0:
                    self._cookies_injected = True
                    logger.info(f"Session loaded ({count} cookies)")
            else:
                logger.warning(f"No session file: {SESSION_FILE}")
                logger.warning("Run: python scrapers/session_manager.py capture --platform instagram")

    def scrape_profile(self, username: str) -> Optional[Dict]:
        """Scrape Instagram profile info"""
        if self.mock:
            return {
                "username": username,
                "full_name": f"Mock {username}",
                "bio": "Mock bio",
                "followers": random.randint(1000, 100000),
                "following": random.randint(100, 5000),
                "posts_count": random.randint(50, 500),
                "scrape_date": datetime.now().strftime("%Y-%m-%d"),
            }

        self._ensure_session()

        url = f"https://www.instagram.com/{username}/"
        self.browser.navigate(url)
        time.sleep(random.uniform(3, 5))

        # Check if profile exists
        page_text = self.browser.evaluate("document.body.innerText") or ""
        if "Sorry" in page_text or "isn't available" in page_text or "Üzgünüz" in page_text:
            logger.warning(f"@{username}: Profile not found")
            return None

        raw = self.browser.evaluate(PROFILE_EXTRACT_JS)
        if not raw:
            logger.warning(f"@{username}: Could not extract profile")
            return None

        return {
            "username": username,
            "full_name": raw.get("fullName", ""),
            "bio": raw.get("bio", ""),
            "followers": parse_ig_metric(raw.get("followers", 0)),
            "following": parse_ig_metric(raw.get("following", 0)),
            "posts_count": parse_ig_metric(raw.get("postsCount", 0)),
            "scrape_date": datetime.now().strftime("%Y-%m-%d"),
        }

    def scrape_posts(
        self,
        username: str,
        max_posts: int = 50,
        days_back: int = 90,
    ) -> List[Dict]:
        """
        Scrape Instagram posts by visiting each post individually.

        Strategy:
        1. Go to profile page
        2. Collect post links from grid
        3. Visit each post to get caption, likes, comments
        """
        if self.mock:
            return generate_mock_posts(username, min(max_posts, 30))

        self._ensure_session()

        url = f"https://www.instagram.com/{username}/"
        logger.info(f"Scraping posts: @{username} (max={max_posts}, days={days_back})")

        self.browser.navigate(url)
        time.sleep(random.uniform(3, 5))

        # Collect post links by scrolling profile grid
        all_links: List[str] = []
        seen_links: set = set()
        last_height = self.browser.get_scroll_height()

        for scroll_num in range(50):  # Max 50 scrolls on profile
            links = self.browser.evaluate(GRID_LINKS_JS) or []

            new_count = 0
            for link in links:
                if link not in seen_links:
                    seen_links.add(link)
                    all_links.append(link)
                    new_count += 1

            if len(all_links) >= max_posts * 2:  # Collect extra for date filtering
                break

            if new_count == 0:
                break

            new_height = self.browser.scroll_and_wait(
                scroll_px=600,
                wait_ms_min=1500,
                wait_ms_max=3000,
            )
            if new_height == last_height:
                break
            last_height = new_height

        logger.info(f"Found {len(all_links)} post links")

        # Visit each post to extract details
        posts: List[Dict] = []
        cutoff_date = datetime.now() - timedelta(days=days_back)

        for i, link in enumerate(all_links):
            if len(posts) >= max_posts:
                break

            full_url = f"https://www.instagram.com{link}" if link.startswith("/") else link

            try:
                self.browser.navigate(full_url)
                time.sleep(random.uniform(2, 4))

                raw = self.browser.evaluate(SINGLE_POST_JS, timeout=10)
                if not raw:
                    continue

                post_date = parse_ig_date(raw.get("timestamp", ""))

                # Date filter
                if post_date and post_date < cutoff_date:
                    logger.info(f"Reached {days_back}-day limit at post {i + 1}")
                    break

                posts.append({
                    "username": username,
                    "post_id": raw.get("postId", ""),
                    "post_url": full_url,
                    "caption": raw.get("caption", ""),
                    "likes": parse_ig_metric(raw.get("likes", 0)),
                    "comments": parse_ig_metric(raw.get("comments", 0)),
                    "post_date": post_date.isoformat() if post_date else None,
                    "is_video": raw.get("isVideo", False),
                    "scraped_at": datetime.now().isoformat(),
                })

                if (i + 1) % 10 == 0:
                    logger.info(f"  {i + 1}/{len(all_links)}: {len(posts)} posts collected")

            except Exception as e:
                logger.warning(f"Post {link}: {str(e)[:60]}")
                continue

        logger.info(f"DONE: @{username} - {len(posts)} posts")
        return posts

    def scrape_user_complete(
        self,
        username: str,
        max_posts: int = 50,
        days_back: int = 90,
    ) -> Dict:
        """Scrape profile + posts"""
        profile = self.scrape_profile(username)
        posts = []
        if profile:
            posts = self.scrape_posts(username, max_posts, days_back)
        return {"profile": profile, "posts": posts}

    def scrape_multiple(
        self,
        usernames: List[str],
        max_posts: int = 50,
        days_back: int = 90,
        politician_ids: Optional[Dict[str, int]] = None,
    ) -> Dict[str, Dict]:
        """Scrape multiple users"""
        logger.info(f"BATCH: {len(usernames)} users")

        results = {}
        for i, username in enumerate(usernames, 1):
            logger.info(f"[{i}/{len(usernames)}] @{username}")

            data = self.scrape_user_complete(username, max_posts, days_back)
            results[username] = data

            if politician_ids and username in politician_ids and data.get("posts"):
                save_posts_to_db(data["posts"], politician_ids[username])

            if i < len(usernames):
                time.sleep(random.uniform(3, 6))

        return results

    def close(self) -> None:
        if self.browser:
            self.browser.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


# ======================================================================
# CLI
# ======================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Instagram CDP Scraper v2.0")
    parser.add_argument("--username", "-u", required=True, help="Instagram username")
    parser.add_argument("--politician-id", type=int, default=0, help="Politician DB ID")
    parser.add_argument("--max-posts", type=int, default=50, help="Max posts")
    parser.add_argument("--days", type=int, default=90, help="Days back")
    parser.add_argument("--mock", action="store_true", help="Use mock data")
    parser.add_argument("--profile-only", action="store_true", help="Only scrape profile")
    parser.add_argument("--save-db", action="store_true", help="Save to SQLite")
    parser.add_argument("--output", "-o", help="Output JSON file")

    args = parser.parse_args()

    scraper = InstagramCDPScraper(mock=args.mock)

    try:
        if args.profile_only:
            result = scraper.scrape_profile(args.username)
            if result:
                print(f"\n@{args.username}:")
                print(f"  Followers: {result['followers']:,}")
                print(f"  Following: {result['following']:,}")
                print(f"  Posts: {result['posts_count']:,}")
        else:
            data = scraper.scrape_user_complete(args.username, args.max_posts, args.days)

            if args.save_db and data.get("posts"):
                save_posts_to_db(data["posts"], args.politician_id)

            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

            posts = data.get("posts", [])
            print(f"\n@{args.username}: {len(posts)} posts collected")
            if posts:
                total_likes = sum(p.get("likes", 0) for p in posts)
                total_comments = sum(p.get("comments", 0) for p in posts)
                print(f"  Likes: {total_likes:,} | Comments: {total_comments:,}")

    finally:
        scraper.close()
