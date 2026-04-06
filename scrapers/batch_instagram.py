#!/usr/bin/env python3
"""
Batch Instagram Scraper (CDP) - Tum meclis uyelerinin Instagram postlarini ceker.
1 Ocak 2026'dan itibaren tum verileri toplar.

Brave/Chrome CDP uzerinden calisir (port 9223).
Twitter scraper port 9222 kullanir, cakismaz.

Kullanim:
    1. Brave'i CDP modunda ac (port 9223):
       Start-Process "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe" -ArgumentList "--remote-debugging-port=9223","--remote-allow-origins=*","--user-data-dir=C:\\tmp\\chrome-ig"

    2. Acilan Brave'da instagram.com'a git ve giris yap

    3. Cookie kaydet:
       python -m scrapers.session_manager capture --platform instagram

    4. Batch baslat:
       python -m scrapers.batch_instagram
"""

import sqlite3
import os
import sys
import time
import random
import logging
import json
from datetime import datetime, timedelta, timezone

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from scrapers.cdp_browser import CDPBrowser

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
)
logger = logging.getLogger("BatchInstagram")

DB_PATH = os.path.join(PROJECT_ROOT, "data", "smot.db")
IG_SESSION = os.path.join(PROJECT_ROOT, "ig_session.json")

START_DATE = datetime(2026, 1, 1)
DAYS_BACK = (datetime.now() - START_DATE).days + 1
MAX_POSTS_PER_USER = 500

# Instagram CDP port (Twitter uses 9222)
IG_CDP_PORT = 9226


# JS: Extract post links from profile grid
GRID_LINKS_JS = """
(() => {
    const links = [];
    const anchors = document.querySelectorAll('a[href*="/p/"], a[href*="/reel/"]');
    for (const a of anchors) {
        const href = a.getAttribute('href') || '';
        if (href && !links.includes(href)) links.push(href);
    }
    return links;
})()
"""

# JS: Extract post details from individual post page
# Instagram SPA: caption is in first section, likes in a standalone section with just a number
POST_DETAIL_JS = """
(() => {
    const r = {caption:'', likes:'0', comments:'0', timestamp:'', postId:'', isVideo:false};

    // Timestamp (most reliable)
    const timeEl = document.querySelector('time');
    if (timeEl) r.timestamp = timeEl.getAttribute('datetime') || '';

    // Post ID from URL
    const urlM = window.location.pathname.match(/\\/(p|reel)\\/([^/]+)/);
    if (urlM) r.postId = urlM[2];

    // Video
    r.isVideo = !!document.querySelector('video');

    // Sections contain the data
    const sections = document.querySelectorAll('section');
    for (const sec of sections) {
        const text = sec.innerText.trim();

        // Pure number section = likes count
        if (/^[0-9][0-9.,]*[KMB]?\\s*(be|lik|$)/i.test(text) || /^[0-9][0-9.,]*$/.test(text)) {
            r.likes = text.replace(/[^0-9.,KMB]/gi, '');
            continue;
        }

        // Section with "like" or "begeni" text
        const likeM = text.match(/([0-9][0-9.,KMB]*)\\s*(?:like|be)/i);
        if (likeM && r.likes === '0') {
            r.likes = likeM[1];
        }

        // Long section = has caption (username + post text + comments)
        if (text.length > 50 && !r.caption) {
            const lines = text.split('\\n');
            const captionLines = [];
            let foundContent = false;
            const skipPatterns = /^(Takip|Follow|Orijinal|Original|\\d+[hdswy]|\\.\\.\\.|Be.en|Like|Yan.t|Reply|G.nder|Send|Kaydet|Save|\\u2022|View|T.m)/i;
            for (const line of lines) {
                const l = line.trim();
                if (!l) continue;
                if (!foundContent) {
                    if (l.length < 3 || skipPatterns.test(l)) continue;
                    if (l.length < 25 && !l.includes(' ')) continue;
                    foundContent = true;
                }
                if (foundContent) {
                    // Stop at comments section (username + timestamp pattern)
                    if (captionLines.length > 0 && /^\\d+[hdswy]$/.test(l)) break;
                    if (captionLines.length > 2 && l.length < 20 && !l.includes(' ')) break;
                    captionLines.push(l);
                }
            }
            r.caption = captionLines.join('\\n').substring(0, 2000);
        }
    }

    // Fallback caption: h1 or span[dir=auto]
    if (!r.caption) {
        const h1 = document.querySelector('h1');
        if (h1 && h1.innerText.trim().length > 10) r.caption = h1.innerText.trim();
    }
    if (!r.caption) {
        const sp = document.querySelector('span[dir="auto"]');
        if (sp && sp.innerText.trim().length > 10) r.caption = sp.innerText.trim();
    }

    // Comments from "View all X comments" or "X yorum"
    const allEls = document.querySelectorAll('span, a');
    for (const el of allEls) {
        const t = el.innerText || '';
        const m = t.match(/(?:View all|T.m.n.)?\\s*([0-9][0-9,.KMB]*)\\s*(?:comment|yorum)/i);
        if (m) { r.comments = m[1]; break; }
    }

    // Hashtags and mentions from caption
    const cap = r.caption || '';
    r.hashtags = (cap.match(/#[\\w\\u00C0-\\u024F\\u1E00-\\u1EFF]+/g) || []).slice(0, 30);
    r.mentions = (cap.match(/@[\\w.]+/g) || []).slice(0, 20);

    // Post type
    r.postType = window.location.pathname.includes('/reel/') ? 'reel' : (r.isVideo ? 'video' : 'photo');

    // Shortcode
    const scm = window.location.pathname.match(/\\/(p|reel)\\/([^\\/]+)/);
    r.shortcode = scm ? scm[2] : '';

    // Video views (reels/videos)
    r.videoViews = '0';
    for (const el of document.querySelectorAll('span')) {
        const t = el.innerText.trim();
        if (/^[\\d.,]+[KMB]?\\s*(view|izlenme)/i.test(t)) { r.videoViews = t.replace(/[^0-9.,KMB]/gi,''); break; }
    }

    return r;
})()
"""


def parse_ig_metric(value) -> int:
    """Parse: '72.4K' -> 72400"""
    import re
    if isinstance(value, (int, float)):
        return int(value)
    if not value:
        return 0
    text = str(value).strip().upper()
    cleaned = re.sub(r'[^\d.,KMB]', '', text)
    if not cleaned:
        return 0
    try:
        suffix = ''
        if cleaned[-1] in 'KMB':
            suffix = cleaned[-1]
            cleaned = cleaned[:-1]
        if ',' in cleaned and '.' in cleaned:
            if cleaned.rfind(',') > cleaned.rfind('.'):
                cleaned = cleaned.replace('.', '').replace(',', '.')
            else:
                cleaned = cleaned.replace(',', '')
        elif ',' in cleaned:
            parts = cleaned.split(',')
            if len(parts) == 2 and len(parts[1]) <= 2:
                cleaned = cleaned.replace(',', '.')
            else:
                cleaned = cleaned.replace(',', '')
        num = float(cleaned) if cleaned else 0
        if suffix in ('K', 'B'):
            num *= 1000
        elif suffix == 'M':
            num *= 1000000
        return int(num)
    except:
        return 0


def get_all_instagram_users() -> list:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT id, instagram_username, name FROM councilors "
        "WHERE instagram_username IS NOT NULL AND instagram_username != '' ORDER BY id"
    ).fetchall()
    conn.close()
    return [(r[0], r[1], r[2]) for r in rows]


def save_post_to_db(post: dict, ig_username: str) -> bool:
    """Tek post kaydet/guncelle"""
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=OFF")

        post_url = post.get("post_url", "")
        existing = conn.execute(
            "SELECT id FROM instagram_posts WHERE post_url = ?", (post_url,)
        ).fetchone()

        if existing:
            conn.execute("""
                UPDATE instagram_posts
                SET likes=?, comments=?, video_views=?, post_type=?
                WHERE id=?
            """, (
                post.get("likes", 0), post.get("comments", 0),
                post.get("video_views", 0), post.get("post_type", "photo"),
                existing[0]
            ))
            conn.commit()
            return False  # Updated, not new
        else:
            conn.execute("""
                INSERT INTO instagram_posts
                (username, caption, post_date, post_url, likes, comments, is_video,
                 video_views, hashtags, mentions, post_type, shortcode, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                ig_username,
                post.get("caption", ""),
                post.get("post_date", ""),
                post_url,
                post.get("likes", 0),
                post.get("comments", 0),
                1 if post.get("is_video") else 0,
                post.get("video_views", 0),
                json.dumps(post.get("hashtags", []), ensure_ascii=False),
                json.dumps(post.get("mentions", []), ensure_ascii=False),
                post.get("post_type", "photo"),
                post.get("shortcode", ""),
            ))
            conn.commit()
            return True  # New
    except Exception as e:
        logger.debug(f"DB error: {e}")
        return False
    finally:
        conn.close()


def _go_to(browser: CDPBrowser, url: str, wait: float = 5):
    """Navigate via JS (avoids SPA Page.loadEventFired issues)"""
    # Escape single quotes in URL
    safe_url = url.replace("'", "\\'")
    browser.evaluate(f"window.location.href = '{safe_url}'")
    time.sleep(wait)


def scrape_user_posts(browser: CDPBrowser, ig_username: str, max_posts: int, days_back: int) -> list:
    """Tek kullanicinin postlarini cek"""
    url = f"https://www.instagram.com/{ig_username}/"
    _go_to(browser, url, wait=5)

    # Profil var mi?
    page_text = browser.evaluate("document.body.innerText.substring(0, 500)") or ""
    if "Sorry" in page_text or "isn't available" in page_text or "mevcut de" in page_text:
        return []

    # Grid'den post linklerini topla
    all_links = []
    seen = set()
    last_h = browser.get_scroll_height()

    for _ in range(30):
        links = browser.evaluate(GRID_LINKS_JS) or []
        for link in links:
            if link not in seen:
                seen.add(link)
                all_links.append(link)

        if len(all_links) >= max_posts * 2:
            break

        browser.evaluate("window.scrollBy(0, window.innerHeight)")
        time.sleep(random.uniform(1.5, 2.5))

        new_h = browser.get_scroll_height()
        if new_h == last_h:
            break
        last_h = new_h

    if not all_links:
        return []

    # Her posta git, detay cek
    posts = []
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days_back)

    for link in all_links[:max_posts]:
        if len(posts) >= max_posts:
            break

        full_url = f"https://www.instagram.com{link}" if link.startswith("/") else link

        try:
            _go_to(browser, full_url, wait=4)

            # Wait for content to render (Instagram SPA is slow)
            raw = None
            for attempt in range(3):
                raw = browser.evaluate(POST_DETAIL_JS, timeout=10)
                if raw and (raw.get("timestamp") or raw.get("likes") != "0"):
                    break  # Got real data
                time.sleep(2)  # Wait more for SPA render

            if not raw:
                continue
            # Skip if page didn't load (got footer/error text)
            caption = raw.get("caption", "")
            if "Gizlilik" in caption or "Bu sayfa" in caption or "API" in caption:
                raw["caption"] = ""

            # Parse date
            post_date = None
            ts = raw.get("timestamp", "")
            if ts:
                try:
                    if ts.endswith("Z"):
                        ts = ts[:-1] + "+00:00"
                    post_date = datetime.fromisoformat(ts)
                    # Ensure timezone-aware for comparison with UTC cutoff
                    if post_date.tzinfo is None:
                        post_date = post_date.replace(tzinfo=timezone.utc)
                except:
                    pass

            if post_date and post_date < cutoff:
                continue  # Eski post, atla ama devam et (grid sırası kronolojik değil)

            posts.append({
                "post_id":     raw.get("postId", ""),
                "post_url":    full_url,
                "caption":     raw.get("caption", ""),
                "likes":       parse_ig_metric(raw.get("likes", 0)),
                "comments":    parse_ig_metric(raw.get("comments", 0)),
                "post_date":   post_date.isoformat() if post_date else "",
                "is_video":    raw.get("isVideo", False),
                "video_views": parse_ig_metric(raw.get("videoViews", 0)),
                "hashtags":    raw.get("hashtags", []),
                "mentions":    raw.get("mentions", []),
                "post_type":   raw.get("postType", "photo"),
                "shortcode":   raw.get("shortcode", ""),
            })

        except Exception as e:
            logger.debug(f"Post error: {e}")
            continue

    return posts


def main():
    users = get_all_instagram_users()

    logger.info(f"{'='*60}")
    logger.info(f"BATCH INSTAGRAM SCRAPER (CDP - port {IG_CDP_PORT})")
    logger.info(f"Profil sayisi: {len(users)}")
    logger.info(f"Tarih araligi: {START_DATE.strftime('%Y-%m-%d')} -> bugun ({DAYS_BACK} gun)")
    logger.info(f"{'='*60}")

    # CDPBrowser singleton'i sifirla (Twitter'inki 9222'de, biz 9223'te)
    CDPBrowser._instance = None

    browser = CDPBrowser(chrome_port=IG_CDP_PORT)

    try:
        browser.ensure_running()
    except Exception as e:
        logger.error(f"Chrome baglantisi kurulamadi: {e}")
        logger.error(f"Brave'i su sekilde baslat:")
        logger.error(f'  Start-Process "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe" -ArgumentList "--remote-debugging-port={IG_CDP_PORT}","--remote-allow-origins=*","--user-data-dir=C:\\tmp\\chrome-ig"')
        logger.error(f"Sonra instagram.com'a giris yap ve tekrar calistir.")
        return

    # Cookie inject
    if os.path.isfile(IG_SESSION):
        browser.inject_cookies(IG_SESSION, ".instagram.com")
        logger.info("Instagram session yuklendi")

    total_posts = 0
    success = 0
    skip = 0
    fail = 0

    for i, (pid, ig_user, name) in enumerate(users, 1):
        logger.info(f"\n[{i}/{len(users)}] @{ig_user} ({name})")

        try:
            posts = scrape_user_posts(browser, ig_user, MAX_POSTS_PER_USER, DAYS_BACK)

            if posts:
                new_count = 0
                for p in posts:
                    if save_post_to_db(p, ig_user):
                        new_count += 1
                total_posts += len(posts)
                success += 1
                total_likes = sum(p.get("likes", 0) for p in posts)
                logger.info(f"  OK: {len(posts)} post ({new_count} yeni) | {total_likes:,} like")
            else:
                skip += 1
                logger.warning(f"  SKIP: 0 post")

            if i < len(users):
                time.sleep(random.uniform(3, 6))

        except KeyboardInterrupt:
            logger.info("\nDurduruldu (Ctrl+C)")
            break
        except Exception as e:
            fail += 1
            logger.error(f"  HATA: {str(e)[:80]}")
            time.sleep(5)

    logger.info(f"\n{'='*60}")
    logger.info(f"BATCH TAMAMLANDI")
    logger.info(f"  Basarili: {success}/{len(users)}")
    logger.info(f"  Skip: {skip}")
    logger.info(f"  Hata: {fail}")
    logger.info(f"  Toplam post: {total_posts:,}")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    main()
