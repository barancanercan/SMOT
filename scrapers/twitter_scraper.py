#!/usr/bin/env python3
"""
Twitter/X CDP Scraper v4.0 - CDP-based tweet collection

- CDPBrowser singleton kullanir (Selenium/Playwright degil)
- Tweet ID bazli deduplication (text[:60] yerine)
- Random 1500-3000ms scroll delay (bot detection onleme)
- Gelistirilmis views parse (birden fazla selector)
- Robust tarih parse (ISO + fallback)
- Mock mod: --mock flag ile gercek Chrome olmadan test
- SQLite kayit: PRAGMA WAL + synchronous=OFF zorunlu
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

logger = logging.getLogger("TwitterScraper")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(levelname)s: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Project root for session/data files
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
SESSION_FILE = os.path.join(PROJECT_ROOT, "x_session.json")
DB_PATH = os.path.join(DATA_DIR, "politicians.db")


# ======================================================================
# JS: Tweet extraction script injected into page
# ======================================================================

TWEET_EXTRACT_JS = """
(() => {
    const articles = document.querySelectorAll('article[data-testid="tweet"]');
    const results = [];

    for (const article of articles) {
        try {
            // Tweet text
            const textEl = article.querySelector('[data-testid="tweetText"]');
            const text = textEl ? textEl.innerText.trim() : '';
            if (!text || text.length < 5) continue;

            // Tweet ID from status link
            let tweetId = null;
            let tweetUrl = null;
            const statusLinks = article.querySelectorAll('a[href*="/status/"]');
            for (const link of statusLinks) {
                const href = link.getAttribute('href') || '';
                const match = href.match(/status\\/([0-9]+)/);
                if (match) {
                    tweetId = match[1];
                    tweetUrl = 'https://x.com' + href.split('?')[0];
                    break;
                }
            }

            // Timestamp
            const timeEl = article.querySelector('time');
            const timestamp = timeEl ? timeEl.getAttribute('datetime') : null;

            // Author (for RT detection)
            const authorLink = article.querySelector('[data-testid="User-Name"] a[href*="/"]');
            const authorHref = authorLink ? (authorLink.getAttribute('href') || '') : '';
            const author = authorHref.split('/').pop() || '';

            // Engagement - likes
            let likes = 0;
            const likeBtn = article.querySelector('[data-testid="like"]');
            if (likeBtn) {
                const aria = likeBtn.getAttribute('aria-label') || '';
                const m = aria.match(/([0-9][0-9,.KMB]*)/i);
                if (m) likes = m[1];
            }

            // Replies
            let replies = 0;
            const replyBtn = article.querySelector('[data-testid="reply"]');
            if (replyBtn) {
                const aria = replyBtn.getAttribute('aria-label') || '';
                const m = aria.match(/([0-9][0-9,.KMB]*)/i);
                if (m) replies = m[1];
            }

            // Retweets
            let retweets = 0;
            const rtBtn = article.querySelector('[data-testid="retweet"]');
            if (rtBtn) {
                const aria = rtBtn.getAttribute('aria-label') || '';
                const m = aria.match(/([0-9][0-9,.KMB]*)/i);
                if (m) retweets = m[1];
            }

            // Views - multiple selector strategies
            let views = 0;
            // Strategy 1: aria-label with "view" / "goruntuleme"
            let viewsEl = article.querySelector('a[aria-label*="view" i], a[aria-label*="g\\u00f6r\\u00fcnt\\u00fclenme" i]');
            if (viewsEl) {
                const aria = viewsEl.getAttribute('aria-label') || '';
                const m = aria.match(/([0-9][0-9,.KMB]*)/i);
                if (m) views = m[1];
            }
            // Strategy 2: analytics link
            if (!views || views === '0') {
                viewsEl = article.querySelector('a[href*="/analytics"]');
                if (viewsEl) {
                    const aria = viewsEl.getAttribute('aria-label') || '';
                    const m = aria.match(/([0-9][0-9,.KMB]*)/i);
                    if (m) views = m[1];
                }
            }
            // Strategy 3: last metric group span (views is always last in the row)
            if (!views || views === '0') {
                const metricGroup = article.querySelector('[role="group"]');
                if (metricGroup) {
                    const spans = metricGroup.querySelectorAll('a[role="link"] span span');
                    if (spans.length > 0) {
                        const lastText = spans[spans.length - 1].innerText.trim();
                        if (lastText && /[0-9]/.test(lastText)) {
                            views = lastText;
                        }
                    }
                }
            }

            // Media type
            let mediaType = 'none';
            if (article.querySelector('[data-testid="videoPlayer"]')) mediaType = 'video';
            else if (article.querySelector('[data-testid="tweetPhoto"]')) mediaType = 'photo';
            else if (article.querySelector('[data-testid="card.wrapper"]')) mediaType = 'card';

            // Language
            const langEl = article.querySelector('[data-testid="tweetText"]');
            const language = langEl ? (langEl.getAttribute('lang') || 'tr') : 'tr';

            // Hashtags
            const hashtagEls = article.querySelectorAll('a[href*="/hashtag/"]');
            const hashtags = Array.from(hashtagEls).map(el => el.innerText.replace('#','').trim()).filter(Boolean);

            // Mentions
            const mentionEls = Array.from(article.querySelectorAll('[data-testid="tweetText"] a')).filter(el => el.innerText.startsWith('@'));
            const mentions = mentionEls.map(el => el.innerText.replace('@','').trim()).filter(Boolean);

            // Media URLs
            const mediaImgs = article.querySelectorAll('img[src*="twimg.com/media"]');
            const mediaUrls = Array.from(mediaImgs).map(el => el.src).filter(Boolean);
            const mediaCount = mediaUrls.length;

            // Bookmarks
            let bookmarks = 0;
            const bkBtn = article.querySelector('[data-testid="bookmark"]');
            if (bkBtn) { const bkAria = bkBtn.getAttribute('aria-label') || ''; const bm = bkAria.match(/([0-9][0-9,.KMB]*)/i); if (bm) bookmarks = bm[1]; }

            // Quote tweet ID (second status link)
            let quoteTweetId = null;
            const statusLinks2 = article.querySelectorAll('a[href*="/status/"]');
            if (statusLinks2.length > 1) { const qh = statusLinks2[1].getAttribute('href') || ''; const qm = qh.match(/status\/([0-9]+)/); if (qm && qm[1] !== tweetId) quoteTweetId = qm[1]; }

            results.push({
                text, tweetId, tweetUrl, timestamp, author,
                likes, replies, retweets, views,
                mediaType, language,
                hashtags, mentions, mediaUrls, mediaCount, bookmarks, quoteTweetId
            });
        } catch (e) {
            // Skip malformed tweets
        }
    }
    return results;
})()
"""


# ======================================================================
# Helper Functions
# ======================================================================

def parse_metric(value) -> int:
    """Parse engagement metrics: '1.2K' -> 1200, '5.5M' -> 5500000"""
    if isinstance(value, (int, float)):
        return int(value)
    if not value:
        return 0

    text = str(value).strip().upper()
    text = "".join(c for c in text if c.isdigit() or c in ".KMB")

    try:
        if "K" in text:
            return int(float(text.replace("K", "")) * 1_000)
        elif "M" in text:
            return int(float(text.replace("M", "")) * 1_000_000)
        elif "B" in text:
            return int(float(text.replace("B", "")) * 1_000_000_000)
        else:
            return int(float(text)) if text else 0
    except (ValueError, TypeError):
        return 0


def parse_tweet_date(timestamp_str: str) -> Optional[datetime]:
    """
    Parse tweet date - robust ISO format handling.
    Handles: 2024-01-15T12:00:00.000Z, 2024-01-15T12:00:00+00:00, etc.
    """
    if not timestamp_str:
        return None

    # Clean up
    ts = timestamp_str.strip()

    # Try standard ISO formats
    for fmt in [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
    ]:
        try:
            return datetime.strptime(ts, fmt)
        except ValueError:
            continue

    # Python fromisoformat (handles +00:00 style)
    try:
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        return datetime.fromisoformat(ts)
    except (ValueError, TypeError):
        pass

    logger.debug(f"Could not parse date: {timestamp_str}")
    return None


def is_within_days(tweet_date: Optional[datetime], days_back: int) -> bool:
    """Check if tweet is within last N days"""
    if not tweet_date:
        return True  # Unknown date -> include

    try:
        cutoff = datetime.now(tweet_date.tzinfo) - timedelta(days=days_back)
        return tweet_date >= cutoff
    except Exception:
        return True


# ======================================================================
# Mock Data Generator
# ======================================================================

def generate_mock_tweets(username: str, count: int = 20) -> List[Dict]:
    """Generate mock tweets for testing without Chrome"""
    logger.info(f"MOCK MODE: Generating {count} mock tweets for @{username}")

    topics = [
        "Belediye hizmetleri devam ediyor",
        "Yeni metro hatti acildi",
        "Egitim yatirimlari artti",
        "Sosyal destek programi basladi",
        "Cevre duzenlemesi tamamlandi",
        "Saglik yatirimi yapildi",
        "Ulasim projesi tamamlandi",
        "Kultur merkezi acildi",
        "Spor tesisi hizmete girdi",
        "Altyapi calismasi bitti",
    ]

    tweets = []
    now = datetime.now()

    for i in range(count):
        days_ago = random.randint(0, 89)
        tweet_date = now - timedelta(days=days_ago, hours=random.randint(0, 23))
        is_rt = random.random() < 0.2

        tweets.append({
            "text": f"{random.choice(topics)} #{username} #{i + 1}",
            "tweet_id": str(1800000000000000000 + random.randint(0, 999999999)),
            "tweet_url": f"https://x.com/{username}/status/{1800000000000000000 + i}",
            "timestamp": tweet_date.isoformat(),
            "username": username,
            "is_retweet": is_rt,
            "retweet_from": f"user_{random.randint(1, 100)}" if is_rt else None,
            "likes": random.randint(0, 5000),
            "replies": random.randint(0, 200),
            "retweets": random.randint(0, 1000),
            "views": random.randint(100, 500000),
            "media_type": random.choice(["none", "photo", "video", "none", "none"]),
            "language": "tr",
        })

    return tweets


# ======================================================================
# SQLite Save
# ======================================================================

def save_to_db(tweets: List[Dict], politician_id: int, db_path: str = None) -> int:
    """
    Save tweets to SQLite. PRAGMA WAL + synchronous=OFF zorunlu.
    Returns number of new tweets saved.
    """
    if not tweets:
        return 0

    db = db_path or DB_PATH
    os.makedirs(os.path.dirname(db), exist_ok=True)

    conn = sqlite3.connect(db)
    try:
        # ZORUNLU: WAL mode + synchronous OFF
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=OFF")

        # Create table if not exists
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tweets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                politician_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                tweet_id TEXT UNIQUE,
                tweet_url TEXT,
                text TEXT NOT NULL,
                timestamp TEXT,
                is_retweet BOOLEAN DEFAULT 0,
                retweet_from TEXT,
                likes INTEGER DEFAULT 0,
                replies INTEGER DEFAULT 0,
                retweets INTEGER DEFAULT 0,
                views INTEGER DEFAULT 0,
                media_type TEXT DEFAULT 'none',
                language TEXT DEFAULT 'tr',
                scraped_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        saved = 0
        for tweet in tweets:
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO tweets
                    (politician_id, username, tweet_id, tweet_url, text, timestamp,
                     is_retweet, retweet_from, likes, replies, retweets, views,
                     media_type, language)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    politician_id,
                    tweet.get("username", ""),
                    tweet.get("tweet_id"),
                    tweet.get("tweet_url"),
                    tweet["text"],
                    tweet.get("timestamp"),
                    1 if tweet.get("is_retweet") else 0,
                    tweet.get("retweet_from"),
                    tweet.get("likes", 0),
                    tweet.get("replies", 0),
                    tweet.get("retweets", 0),
                    tweet.get("views", 0),
                    tweet.get("media_type", "none"),
                    tweet.get("language", "tr"),
                ))
                if conn.total_changes:
                    saved += 1
            except sqlite3.IntegrityError:
                pass  # Duplicate tweet_id

        conn.commit()
        logger.info(f"Saved {saved} new tweets to {db}")
        return saved

    finally:
        conn.close()


# ======================================================================
# Main Scraper
# ======================================================================

class TwitterCDPScraper:
    """CDP-based Twitter scraper with tweet_id dedup and random delays"""

    def __init__(self, mock: bool = False):
        self.mock = mock
        self.browser: Optional[CDPBrowser] = None
        self._cookies_injected = False

        if not mock:
            self.browser = CDPBrowser()

    def _ensure_session(self) -> None:
        """Ensure browser is running with cookies injected (once per session)"""
        self.browser.ensure_running()

        if not self._cookies_injected:
            if os.path.isfile(SESSION_FILE):
                count = self.browser.inject_cookies(SESSION_FILE, ".x.com")
                if count > 0:
                    self._cookies_injected = True
                    logger.info(f"Session loaded ({count} cookies)")
            else:
                logger.warning(f"No session file: {SESSION_FILE}")
                logger.warning("Run: python scrapers/session_manager.py capture --platform twitter")

    def scrape_tweets(
        self,
        username: str,
        max_tweets: int = 500,
        days_back: int = 90,
    ) -> List[Dict]:
        """
        Scrape tweets for a user.

        Deduplication: tweet_id (not text[:60])
        Scroll delay: random 1500-3000ms
        Stops when: max_tweets reached OR 15 consecutive old tweets OR 20 scrolls with no new
        """
        if self.mock:
            return generate_mock_tweets(username, min(max_tweets, 50))

        self._ensure_session()

        url = f"https://x.com/{username}"
        logger.info(f"Scraping: @{username} (max={max_tweets}, days={days_back})")

        self.browser.navigate(url)
        time.sleep(random.uniform(3, 5))

        # Check profile exists
        exists = self.browser.evaluate(
            "!document.querySelector('span') || "
            "!document.querySelector('span').innerText.includes('does not exist')"
        )
        if not exists:
            logger.warning(f"@{username} not found")
            return []

        # Wait for tweets to load (Twitter lazy loads — need 8-10s)
        for wait_attempt in range(5):
            tweet_count = self.browser.evaluate(
                "document.querySelectorAll('article[data-testid=\"tweet\"]').length"
            ) or 0
            if tweet_count > 0:
                logger.info(f"Page loaded: {tweet_count} tweets visible")
                break
            logger.info(f"Waiting for tweets to load... ({(wait_attempt + 1) * 2}s)")
            time.sleep(2)
        else:
            logger.warning("No tweets visible after 10s wait — page may not have loaded")

        tweets: List[Dict] = []
        seen_ids: set = set()  # tweet_id based dedup
        seen_texts: set = set()  # fallback text dedup (if no ID)
        last_height = self.browser.get_scroll_height()
        consecutive_no_new = 0
        consecutive_old = 0
        max_scrolls = 500
        max_no_new = 8  # 8 scrolls with zero new tweets = stop
        max_old = 15

        for scroll_num in range(max_scrolls):
            if len(tweets) >= max_tweets:
                break

            # Extract tweets from current DOM
            raw_tweets = self.browser.evaluate(TWEET_EXTRACT_JS, timeout=15)
            if not raw_tweets:
                raw_tweets = []

            old_count = len(tweets)

            for raw in raw_tweets:
                if len(tweets) >= max_tweets:
                    break

                tweet_id = raw.get("tweetId")
                text = raw.get("text", "").strip()

                # Dedup: prefer tweet_id, fallback to text
                if tweet_id:
                    if tweet_id in seen_ids:
                        continue
                    seen_ids.add(tweet_id)
                else:
                    text_key = text[:80]
                    if text_key in seen_texts:
                        continue
                    seen_texts.add(text_key)

                if not text or len(text) < 5:
                    continue

                # Parse date
                tweet_date = parse_tweet_date(raw.get("timestamp"))

                # RT detection
                author = raw.get("author", "").lower()
                is_rt = author != "" and author != username.lower()
                if not is_rt and text.startswith("RT @"):
                    is_rt = True

                # Time filter (only original tweets, RTs show original date)
                if not is_rt and tweet_date and not is_within_days(tweet_date, days_back):
                    consecutive_old += 1
                    if consecutive_old >= max_old:
                        logger.info(f"Reached {days_back}-day boundary after {scroll_num} scrolls")
                        break
                    continue
                elif not is_rt:
                    consecutive_old = 0

                # Build tweet dict
                tweets.append({
                    "text": text,
                    "tweet_id": tweet_id,
                    "tweet_url": raw.get("tweetUrl"),
                    "timestamp": tweet_date.isoformat() if tweet_date else None,
                    "username": username,
                    "is_retweet": is_rt,
                    "retweet_from": raw.get("author") if is_rt else None,
                    "likes": parse_metric(raw.get("likes", 0)),
                    "replies": parse_metric(raw.get("replies", 0)),
                    "retweets": parse_metric(raw.get("retweets", 0)),
                    "views": parse_metric(raw.get("views", 0)),
                    "media_type": raw.get("mediaType", "none"),
                    "language": raw.get("language", "tr"),
                })

            # Check for date boundary break
            if consecutive_old >= max_old:
                break

            # Stale detection: only count scrolls where zero new tweets found
            if len(tweets) == old_count:
                consecutive_no_new += 1
                if consecutive_no_new >= max_no_new:
                    # Double-check: also verify height stopped growing
                    final_height = self.browser.get_scroll_height()
                    if final_height == last_height:
                        logger.info(f"No new tweets for {max_no_new} scrolls + page end, stopping")
                        break
                    else:
                        # Height still growing — keep scrolling but warn
                        consecutive_no_new = max_no_new // 2
                        last_height = final_height
            else:
                consecutive_no_new = 0

            # Scroll: 1 viewport height (Twitter virtualizes DOM — smaller = safer)
            self.browser.evaluate("window.scrollBy(0, window.innerHeight)")
            delay = random.uniform(1.5, 3.0)
            time.sleep(delay)

            new_height = self.browser.get_scroll_height()
            if new_height != last_height:
                last_height = new_height

            # Progress log every 10 scrolls
            if (scroll_num + 1) % 10 == 0:
                logger.info(f"  Scroll {scroll_num + 1}: {len(tweets)} tweets")

        logger.info(f"DONE: @{username} - {len(tweets)} tweets")
        return tweets

    def scrape_multiple(
        self,
        usernames: List[str],
        max_tweets: int = 500,
        days_back: int = 90,
        politician_ids: Optional[Dict[str, int]] = None,
    ) -> Dict[str, List[Dict]]:
        """Scrape multiple users, optionally save to DB"""
        logger.info(f"BATCH: {len(usernames)} users, {days_back} days")

        results = {}
        for i, username in enumerate(usernames, 1):
            logger.info(f"[{i}/{len(usernames)}] @{username}")

            tweets = self.scrape_tweets(username, max_tweets, days_back)
            if tweets:
                results[username] = tweets

                # Save to DB if politician_id provided
                if politician_ids and username in politician_ids:
                    save_to_db(tweets, politician_ids[username])

            # Inter-user delay (2-5s)
            if i < len(usernames):
                time.sleep(random.uniform(2, 5))

        total = sum(len(t) for t in results.values())
        logger.info(f"BATCH DONE: {total} total tweets from {len(results)} users")
        return results

    def close(self) -> None:
        """Close browser (only if we own it)"""
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
    parser = argparse.ArgumentParser(description="Twitter CDP Scraper v4.0")
    parser.add_argument("--username", "-u", required=True, help="Twitter username")
    parser.add_argument("--politician-id", type=int, default=0, help="Politician DB ID")
    parser.add_argument("--max-tweets", type=int, default=500, help="Max tweets to collect")
    parser.add_argument("--days", type=int, default=90, help="Days back")
    parser.add_argument("--mock", action="store_true", help="Use mock data (no Chrome)")
    parser.add_argument("--save-db", action="store_true", help="Save to SQLite")
    parser.add_argument("--output", "-o", help="Output JSON file")

    args = parser.parse_args()

    scraper = TwitterCDPScraper(mock=args.mock)

    try:
        tweets = scraper.scrape_tweets(args.username, args.max_tweets, args.days)

        if args.save_db and tweets:
            save_to_db(tweets, args.politician_id)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(tweets, f, ensure_ascii=False, indent=2)
            print(f"Saved {len(tweets)} tweets to {args.output}")

        print(f"\nCollected {len(tweets)} tweets for @{args.username}")
        if tweets:
            print(f"  Date range: {tweets[-1].get('timestamp', '?')} -> {tweets[0].get('timestamp', '?')}")
            total_likes = sum(t.get("likes", 0) for t in tweets)
            total_views = sum(t.get("views", 0) for t in tweets)
            print(f"  Total likes: {total_likes:,} | Total views: {total_views:,}")
            rts = sum(1 for t in tweets if t.get("is_retweet"))
            print(f"  Original: {len(tweets) - rts} | Retweets: {rts}")

    finally:
        scraper.close()
