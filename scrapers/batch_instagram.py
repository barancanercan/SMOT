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

from scrapers.cdp_browser import CDPBrowser  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
)
logger = logging.getLogger("BatchInstagram")

DB_PATH = os.path.join(PROJECT_ROOT, "data", "sam.db")
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

    // ── Timestamp ────────────────────────────────────────────
    const timeEl = document.querySelector('time');
    if (timeEl) r.timestamp = timeEl.getAttribute('datetime') || '';

    // ── Post ID / shortcode ──────────────────────────────────
    const urlM = window.location.pathname.match(/\\/(p|reel)\\/([^/]+)/);
    if (urlM) r.postId = urlM[2];

    // ── Video ────────────────────────────────────────────────
    r.isVideo = !!document.querySelector('video');

    // ── LIKES — 6 strateji ──────────────────────────────────
    const parseLikeNum = t => t ? t.replace(/[^0-9.,KMB]/gi,'').trim() : '0';

    // S0: section > div > span[role="button"]
    // roleSpans[0] = begeni, roleSpans[1] = yorum
    // parseLikeNum ile normalize et (\xa0 ve diger unicode bosluk temizlenir)
    if (r.likes === '0') {
        for (const sec of document.querySelectorAll('section')) {
            let found = false;
            for (const div of sec.children) {
                if (div.tagName !== 'DIV') continue;
                const roleSpans = div.querySelectorAll(':scope > span[role="button"]');
                if (roleSpans.length >= 1) {
                    const t = parseLikeNum(roleSpans[0].innerText);  // normalize: '2,8\xa0B' → '2,8B'
                    if (t && /^[0-9][0-9,.]*[KMB]?$/.test(t)) {
                        r.likes = t; found = true;
                        if (roleSpans.length >= 2) {
                            const tc = parseLikeNum(roleSpans[1].innerText);
                            if (tc && /^[0-9][0-9,.]*[KMB]?$/.test(tc)) r.comments = tc;
                        }
                        break;
                    }
                }
                if (found) break;
            }
            if (found) break;
        }
    }

    // S1: aria-label "X beğenme" veya "X likes" (buton / link)
    if (r.likes === '0') {
        for (const el of document.querySelectorAll('[aria-label]')) {
            const a = el.getAttribute('aria-label') || '';
            if (/beğen|like/i.test(a)) {
                const m = a.match(/([0-9][0-9,.]*[KMB]?)/i);
                if (m) { r.likes = parseLikeNum(m[1]); break; }
            }
        }
    }

    // S2: "X beğenme" veya "X likes" text içinde geçen span/a
    if (r.likes === '0') {
        for (const el of document.querySelectorAll('span, a, button')) {
            const t = (el.innerText || '').trim();
            const m = t.match(/^([0-9][0-9,.]*[KMB]?)\\s*(?:beğenme|beğeni|likes?)$/i);
            if (m) { r.likes = parseLikeNum(m[1]); break; }
        }
    }

    // S3: section icinde salt sayi veya "X be/lik" kalıbı
    if (r.likes === '0') {
        for (const sec of document.querySelectorAll('section')) {
            const text = sec.innerText.trim();
            if (/^[0-9][0-9.,]*[KMB]?\\s*(beğen|like|be\\b|lik)/i.test(text) ||
                /^[0-9][0-9.,]*[KMB]?$/.test(text)) {
                r.likes = parseLikeNum(text.split('\\n')[0]);
                break;
            }
        }
    }

    // S4: Kalp SVG'nin yanındaki span (buton parent)
    if (r.likes === '0') {
        const hearts = document.querySelectorAll('svg[aria-label*="Like" i], svg[aria-label*="Beğen" i], svg[aria-label*="beğen" i]');
        for (const svg of hearts) {
            const btn = svg.closest('button, a, div[role]');
            if (!btn) continue;
            const next = btn.nextElementSibling;
            if (next) {
                const t = (next.innerText || next.textContent || '').trim();
                if (/^[0-9]/.test(t)) { r.likes = parseLikeNum(t); break; }
            }
            // Kardeş span
            const spans = btn.parentElement ? btn.parentElement.querySelectorAll('span') : [];
            for (const s of spans) {
                const t = s.innerText.trim();
                if (/^[0-9][0-9.,]*[KMB]?$/.test(t)) { r.likes = parseLikeNum(t); break; }
            }
        }
    }

    // S5: Tüm sayfada "X beğenme" geçiyor mu?
    if (r.likes === '0') {
        const bodyText = document.body.innerText || '';
        const m = bodyText.match(/([0-9][0-9,.]*[KMB]?)\\s*beğenme/i) ||
                  bodyText.match(/([0-9][0-9,.]*[KMB]?)\\s*likes?\\b/i);
        if (m) r.likes = parseLikeNum(m[1]);
    }

    // ── CAPTION — tam metin, limit yok ──────────────────────
    // Yardimci: bilinen UI metinlerini ve yorum izlerini temizle
    const UI_NOISE = [
        'Henüz yorum yok.', 'No comments yet.',
        'Konuşmayı başlat.', 'Be the first to comment.', 'Start a conversation.',
        'Senin için', 'For you', 'Suggested for you',
    ];
    function cleanCaption(text) {
        if (!text) return '';
        // Bilinen UI stringinden itibaren kes
        for (const s of UI_NOISE) {
            const idx = text.indexOf(s);
            if (idx !== -1) text = text.substring(0, idx);
        }
        // Son satirlardaki zaman damgasi (1g, 2h, 3d...) ve username satirlarini kaldir
        const lines = text.split('\\n');
        while (lines.length > 0) {
            const last = lines[lines.length - 1].trim();
            if (/^\\d+\\s*[ghdwsmyGHDWSMY]$/.test(last)) { lines.pop(); continue; }  // "1g", "2h"
            if (/^(Senin için|For you)$/i.test(last)) { lines.pop(); continue; }
            break;
        }
        // Son satir sadece username (bosluk ve ozel karakter yok, <= 30 karakter) → kaldir
        while (lines.length > 0) {
            const last = lines[lines.length - 1].trim();
            if (/^[a-zA-Z0-9_.-]{1,30}$/.test(last)) { lines.pop(); } else break;
        }
        return lines.join('\\n').trim();
    }

    // Oncelik 1: article ul li:first-child span[dir="auto"]
    // Instagram caption+yorumlari tek ul icinde tutar; ilk li = caption
    const captionLiSpan = document.querySelector('article ul li:first-child span[dir="auto"]');
    if (captionLiSpan) {
        const t = cleanCaption(captionLiSpan.innerText.trim());
        if (t) r.caption = t;
    }

    // Oncelik 2: article h1 (bazi Instagram versiyonlari h1 kullanir)
    if (!r.caption) {
        const h1El = document.querySelector('article h1');
        if (h1El) {
            const t = cleanCaption(h1El.innerText.trim());
            if (t) r.caption = t;
        }
    }

    // Oncelik 3: ul ve form disindaki span[dir="auto"], zaman damgasi icermeyen konteyner
    if (!r.caption) {
        const article = document.querySelector('article');
        if (article) {
            for (const span of article.querySelectorAll('span[dir="auto"]')) {
                if (span.closest('ul, form')) continue;  // yorum listesi / input alani
                const container = span.closest('div');
                if (container && container.querySelector('time, [datetime]')) continue;  // yorum preview
                const t = cleanCaption(span.innerText.trim());
                if (t) { r.caption = t; break; }
            }
        }
    }

    // Fallback: section tarama
    if (!r.caption) {
        const skipPat = /^(Takip|Follow|Orijinal|Original|\\d+[hdswy]|\\.\\.\\.|Beğen|Like|Yanıt|Reply|Gönder|Send|Kaydet|Save|\\u2022|View|Tüm|Hepsini)/i;
        for (const sec of document.querySelectorAll('section')) {
            const text = sec.innerText.trim();
            if (text.length > 50 && !r.caption) {
                const lines = text.split('\\n');
                const captionLines = [];
                let foundContent = false;
                for (const line of lines) {
                    const l = line.trim();
                    if (!l) continue;
                    if (!foundContent) {
                        if (l.length < 3 || skipPat.test(l)) continue;
                        if (l.length < 25 && !l.includes(' ')) continue;
                        foundContent = true;
                    }
                    if (foundContent) {
                        if (captionLines.length > 0 && /^\\d+[hdswy]$/.test(l)) break;
                        if (captionLines.length > 2 && l.length < 20 && !l.includes(' ')) break;
                        captionLines.push(l);
                    }
                }
                r.caption = cleanCaption(captionLines.join('\\n'));
            }
        }
    }

    // ── COMMENTS ─────────────────────────────────────────────
    // "Tüm X yorumu görüntüle" veya "X yorum" veya "X comments"
    for (const el of document.querySelectorAll('a, span, button')) {
        const t = (el.innerText || '').trim();
        const m = t.match(/^(?:Tüm\\s+)?([0-9][0-9,.KMB]*)\\s*yorum/i) ||
                  t.match(/^View(?:\\s+all)?\\s+([0-9][0-9,.KMB]*)\\s+comment/i) ||
                  t.match(/^([0-9][0-9,.KMB]*)\\s*comment/i);
        if (m) { r.comments = m[1]; break; }
    }
    // Not: S0 stratejisi comments'i roleSpans[1]'den zaten aldı

    // ── HASHTAGS & MENTIONS (caption'dan) ────────────────────
    const cap = r.caption || '';
    r.hashtags = (cap.match(/#[\\w\\u00C0-\\u024F\\u1E00-\\u1EFF]+/g) || []).slice(0, 30);
    r.mentions = (cap.match(/@[\\w.]+/g) || []).slice(0, 20);

    // ── POST TYPE ────────────────────────────────────────────
    r.postType = window.location.pathname.includes('/reel/') ? 'reel' : (r.isVideo ? 'video' : 'photo');

    // ── SHORTCODE ────────────────────────────────────────────
    const scm = window.location.pathname.match(/\\/(p|reel)\\/([^\\/]+)/);
    r.shortcode = scm ? scm[2] : '';

    // ── VIDEO VIEWS ──────────────────────────────────────────
    r.videoViews = '0';
    const viewPat = /^[\\d.,]+[KMB]?\\s*(görüntülenme|görüntüleme|view|izlenme|kez oynand|plays)/i;
    for (const el of document.querySelectorAll('span, [aria-label]')) {
        const t = (el.innerText || el.getAttribute('aria-label') || '').trim();
        if (viewPat.test(t)) {
            r.videoViews = t.replace(/[^0-9.,KMB]/gi,'');
            break;
        }
    }
    // Reel: meta etiketinden izlenme sayisi
    if (r.videoViews === '0' && r.postType === 'reel') {
        const metaViews = document.querySelector('meta[property="og:video:view_count"], meta[name="twitter:data1"]');
        if (metaViews) {
            const v = metaViews.getAttribute('content') || '';
            if (/^\\d+$/.test(v.trim())) r.videoViews = v.trim();
        }
    }

    // ── DEBUG: action section role=button spans ───────────────
    r._roleButtonSpans = [];
    for (const sec of document.querySelectorAll('section')) {
        for (const span of sec.querySelectorAll('span[role="button"]')) {
            const t = span.innerText.trim();
            if (t) r._roleButtonSpans.push(t);
        }
        if (r._roleButtonSpans.length > 0) break;
    }

    return r;
})()
"""


IG_PROFILE_JS = """
(() => {
    const r = {bio: '', followers: '0', following: '0', postCount: '0'};

    // Followers — link href contains /followers/
    const fwrA = document.querySelector('a[href*="/followers/"]');
    if (fwrA) {
        const titleSpan = fwrA.querySelector('span[title]');
        if (titleSpan) {
            r.followers = titleSpan.getAttribute('title').replace(/[^0-9]/g, '');
        } else {
            const s = fwrA.querySelector('span');
            if (s) r.followers = s.innerText.trim();
        }
    }

    // Following — title attribute varsa tam sayi, yoksa numerik bolum
    const fwgA = document.querySelector('a[href*="/following/"]');
    if (fwgA) {
        const titleSpan = fwgA.querySelector('span[title]');
        if (titleSpan) {
            r.following = titleSpan.getAttribute('title').replace(/[^0-9]/g, '');
        } else {
            // Sadece rakam/nokta/virgul iceren span bul
            const spans = fwgA.querySelectorAll('span');
            for (const s of spans) {
                const t = s.innerText.trim();
                if (/^[0-9][0-9.,]*[KMB]?$/.test(t)) { r.following = t; break; }
            }
            if (!r.following || r.following === '0') {
                // Fallback: link iceriginden numerik kismi cek
                const raw = fwgA.innerText.trim();
                const m = raw.match(/^([0-9][0-9.,]*[KMB]?)/);
                if (m) r.following = m[1];
            }
        }
    }

    // Followers/Following fallback — sayfa metni üzerinden (gizli hesaplar için)
    // "N gönderi  M takipçi  K takip" sırası her zaman sabit
    if (r.followers === '0' || r.following === '0') {
        const bodyText = document.body.innerText || '';
        if (r.followers === '0') {
            const fm = bodyText.match(/([0-9][0-9.,]*[KMB]?)[\s\u00a0]*takipçi/i) ||
                       bodyText.match(/([0-9][0-9.,]*[KMB]?)[\s\u00a0]*followers?/i);
            if (fm) r.followers = fm[1];
        }
        if (r.following === '0') {
            // "takip" eşleşmesi, "takipçi" ile karışmasın diye negatif lookahead
            const fm = bodyText.match(/([0-9][0-9.,]*[KMB]?)[\s\u00a0]*takip(?!çi|ci)/i) ||
                       bodyText.match(/([0-9][0-9.,]*[KMB]?)[\s\u00a0]*following/i);
            if (fm) r.following = fm[1];
        }
    }

    // Post count & bio from header
    const header = document.querySelector('header') || document.querySelector('main');
    if (header) {
        const text = header.innerText || '';
        const pm = text.match(/([0-9][0-9,.KMB]*)\\s*(?:posts?|gönderi)/i);
        if (pm) r.postCount = pm[1];
    }
    // Post count fallback — body text
    if (!r.postCount || r.postCount === '0') {
        const bodyText = document.body.innerText || '';
        const pm = bodyText.match(/([0-9][0-9.,]*[KMB]?)[\s\u00a0]*gönderi/i) ||
                   bodyText.match(/([0-9][0-9.,]*[KMB]?)[\s\u00a0]*posts?(?!\s*gönderi)/i);
        if (pm) r.postCount = pm[1];
    }

    // Display name — h1/h2 icerigini bio ile karistirma
    const dnEl = document.querySelector('header h2, header h1, section h2');
    const displayName = dnEl ? dnEl.innerText.trim() : '';

    // Bio — header icindeki span[dir="auto"], display name + stat metinlerini atla
    const hdr = document.querySelector('header');
    if (hdr) {
        const bioSpans = hdr.querySelectorAll('span[dir="auto"], span._ap3a');
        let skipped = 0;
        for (const span of bioSpans) {
            const t = span.innerText.trim();
            if (t.length < 3) continue;
            // Bilinen UI metinlerini atla
            if (/^(Ana Sayfa|Home|Explore|Kesif|Reels|Search|Ara|Öne Çıkanlar|Highlights|Takip Et|Follow|Mesaj|Message|İletişim|Contact|Profili Düzenle|Edit Profile|Reklam Ver|Promote)$/i.test(t)) continue;
            if (!/[a-zA-ZğüşıöçĞÜŞİÖÇ0-9]/.test(t)) continue;
            // Stat metinlerini atla: "1.618 gönderi", "5.027 takipçi", "642 takip", vb.
            if (/^[0-9][0-9.,]*[KMB]?\\s*(gönderi|takipçi|takip|post|follower|following)\\b/i.test(t)) continue;
            // Ilk kisa, tek satirli, #/@ icermeyen span = muhtemelen display name → atla
            if (skipped < 1 && t.length < 50 && !t.includes('\\n') && !/[#@]/.test(t)) {
                skipped++;
                continue;
            }
            r.bio = t.substring(0, 1000);
            break;
        }
    }
    // Fallback: meta description'dan al
    if (!r.bio) {
        const meta = document.querySelector('meta[name="description"]');
        if (meta) {
            const content = meta.getAttribute('content') || '';
            const parts = content.split(' - ');
            if (parts.length > 1 && !/^\\d/.test(parts[0])) {
                r.bio = parts[0].trim().substring(0, 500);
            }
        }
    }

    return r;
})()
"""


def parse_ig_metric(value) -> int:
    """
    Instagram metrik stringini tam integer'a çevirir. Daima tam sayı döner.

    Örnekler:
      '2,8B'    → 2800   (Türkçe: B = Bin = 1.000)
      '72,4K'   → 72400
      '1,2M'    → 1200000
      '1.680'   → 1680   (Türkçe binlik nokta)
      '29.153'  → 29153
      '1.234.567' → 1234567
      '151'     → 151
    """
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
        if cleaned and cleaned[-1] in 'KMB':
            suffix = cleaned[-1]
            cleaned = cleaned[:-1]

        if ',' in cleaned and '.' in cleaned:
            # Her ikisi varsa: sondaki hangisi decimal separator
            if cleaned.rfind(',') > cleaned.rfind('.'):
                # Türkçe/Avrupa: 1.234,56 → nokta=binlik, virgül=ondalık
                cleaned = cleaned.replace('.', '').replace(',', '.')
            else:
                # İngilizce: 1,234.56 → virgül=binlik, nokta=ondalık
                cleaned = cleaned.replace(',', '')
        elif ',' in cleaned:
            parts = cleaned.split(',')
            if len(parts) == 2 and len(parts[1]) <= 2:
                cleaned = cleaned.replace(',', '.')   # ondalık virgül: 1,5 → 1.5
            else:
                cleaned = cleaned.replace(',', '')     # binlik virgül: 1,234 → 1234
        elif '.' in cleaned:
            parts = cleaned.split('.')
            if len(parts) == 2 and len(parts[1]) == 3:
                # Türkçe binlik nokta: 1.680 → 1680, 29.153 → 29153
                cleaned = cleaned.replace('.', '')
            elif len(parts) > 2:
                # Birden fazla binlik nokta: 1.234.567 → 1234567
                cleaned = cleaned.replace('.', '')
            # else: ondalık nokta: 1.5K → olduğu gibi bırak

        num = float(cleaned) if cleaned else 0.0

        # Türkçe Instagram kısaltmaları: K=1K, B=Bin=1K, M=Milyon=1M
        if suffix == 'K' or suffix == 'B':
            num *= 1_000
        elif suffix == 'M':
            num *= 1_000_000

        return int(num)
    except Exception:
        return 0


def save_ig_profile(ig_username: str, profile: dict) -> None:
    """Update councilor's Instagram profile stats."""
    if not profile:
        return
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        conn.execute("""
            UPDATE councilors
            SET instagram_followers=?, instagram_following=?, instagram_posts_count=?,
                instagram_updated_at=CURRENT_TIMESTAMP
            WHERE instagram_username=?
        """, (
            parse_ig_metric(profile.get("followers", "0")),
            parse_ig_metric(profile.get("following", "0")),
            parse_ig_metric(profile.get("postCount", "0")),
            ig_username,
        ))
        # Also update bio if not already set
        if profile.get("bio"):
            conn.execute("""
                UPDATE councilors SET bio=?
                WHERE instagram_username=? AND (bio IS NULL OR bio='')
            """, (profile.get("bio", ""), ig_username))
        conn.commit()
    except Exception as e:
        logger.debug(f"IG profile save error: {e}")
    finally:
        conn.close()


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
            "SELECT id, likes FROM instagram_posts WHERE post_url = ?", (post_url,)
        ).fetchone()

        if existing:
            existing_id, existing_likes = existing
            new_likes = post.get("likes", 0)
            # Never overwrite a higher like count with a lower scraped value.
            # CDP sometimes returns 1-3 likes when the page hasn't fully rendered;
            # keeping MAX ensures previously verified data isn't corrupted.
            final_likes = max(new_likes, existing_likes or 0)
            conn.execute("""
                UPDATE instagram_posts
                SET likes=?, comments=?, video_views=?, post_type=?
                WHERE id=?
            """, (
                final_likes, post.get("comments", 0),
                post.get("video_views", 0), post.get("post_type", "photo"),
                existing_id
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
    """
    Navigate via CDP Page.navigate (proper tab-level navigation).
    Falls back to window.location.href if Page.navigate times out.
    """
    try:
        browser._send("Page.enable")
        browser._send("Page.navigate", {"url": url})
        # Wait up to 12s for loadEventFired
        browser._wait_for_event("Page.loadEventFired", timeout=12)
    except Exception as e:
        logger.debug(f"Page.navigate/loadEventFired: {e} — falling back to href")
        try:
            safe_url = url.replace("'", "\\'")
            browser.evaluate(f"window.location.href = '{safe_url}'")
        except Exception:
            pass
    time.sleep(wait)


def _wait_for_links(browser: CDPBrowser, max_wait: float = 10.0) -> list:
    """Poll for Instagram post/reel grid links to appear (SPA is slow)."""
    deadline = time.time() + max_wait
    while time.time() < deadline:
        links = browser.evaluate(GRID_LINKS_JS) or []
        if links:
            return links
        time.sleep(1.0)
    return []


def scrape_user_posts(browser: CDPBrowser, ig_username: str, max_posts: int, days_back: int) -> tuple:
    """Tek kullanicinin postlarini ve profil bilgilerini cek. (posts, profile) tuple dondurur."""
    url = f"https://www.instagram.com/{ig_username}/"
    _go_to(browser, url, wait=6)

    # Sayfa icerigini logla (debug)
    page_text = browser.evaluate("document.body.innerText.substring(0, 400)") or ""
    logger.info(f"  Sayfa: {page_text[:120].replace(chr(10),' ')!r}")

    # Profil var mi? / Giris gerektiriyor mu?
    if ("Sorry" in page_text or "isn't available" in page_text or "mevcut de" in page_text):
        logger.warning(f"  Profil mevcut degil: @{ig_username}")
        return [], {}
    if ("Log in" in page_text or "Giriş yap" in page_text or "Hesabına giriş" in page_text
            or "Create an account" in page_text or "Sign up" in page_text):
        logger.error(f"  GIRIS DUVARI! Cookie gecersiz olmus olabilir. @{ig_username}")
        return [], {}

    # Profil bilgilerini cek (sayfa yuklu iken)
    profile = {}
    try:
        profile = browser.evaluate(IG_PROFILE_JS, timeout=10) or {}
        if profile:
            logger.info(
                f"  Profil: {profile.get('followers','?')} takipci, "
                f"{profile.get('postCount','?')} post"
            )
    except Exception as e:
        logger.debug(f"Profil cekme hatasi: {e}")

    # Grid'den post linklerini topla — once polling ile bekle
    first_links = _wait_for_links(browser, max_wait=12)
    all_links = list(first_links)
    seen = set(all_links)

    if not all_links:
        logger.warning(f"  Grid linkleri bulunamadi. URL: {browser.evaluate('window.location.href')}")
        return [], profile

    last_h = browser.get_scroll_height()

    for _ in range(30):
        if len(all_links) >= max_posts * 2:
            break

        browser.evaluate("window.scrollBy(0, window.innerHeight)")
        time.sleep(random.uniform(1.5, 2.5))

        links = browser.evaluate(GRID_LINKS_JS) or []
        for link in links:
            if link not in seen:
                seen.add(link)
                all_links.append(link)

        new_h = browser.get_scroll_height()
        if new_h == last_h:
            break
        last_h = new_h

    logger.info(f"  Grid: {len(all_links)} link bulundu")

    if not all_links:
        return [], profile

    # Her posta git, detay cek
    posts = []
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days_back)

    for link in all_links:  # Tum linkleri dene, max_posts kadar post topla
        if len(posts) >= max_posts:
            break

        full_url = f"https://www.instagram.com{link}" if link.startswith("/") else link

        try:
            _go_to(browser, full_url, wait=5)

            # Wait for content to render (Instagram SPA is slow)
            raw = None
            for attempt in range(3):
                raw = browser.evaluate(POST_DETAIL_JS, timeout=12)
                likes_val = parse_ig_metric(raw.get("likes", "0")) if raw else 0
                comments_val = parse_ig_metric(raw.get("comments", "0")) if raw else 0
                # Consider data "real" only when:
                # - timestamp present, OR
                # - likes > 5, OR
                # - comments > 0 AND likes > 0 (page partially loaded)
                # Avoids accepting likes=1/2 from DOM placeholders before page renders
                page_ready = raw and (
                    raw.get("timestamp") or
                    likes_val > 5 or
                    (comments_val > 0 and likes_val > 0)
                )
                if page_ready:
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
                except Exception:
                    pass

            if post_date and post_date < cutoff:
                continue  # Eski post, atla ama devam et (grid sırası kronolojik değil)

            posts.append({
                "post_id":            raw.get("postId", ""),
                "post_url":           full_url,
                "caption":            raw.get("caption", ""),
                "likes":              parse_ig_metric(raw.get("likes", 0)),
                "comments":           parse_ig_metric(raw.get("comments", 0)),
                "post_date":          post_date.isoformat() if post_date else "",
                "is_video":           raw.get("isVideo", False),
                "video_views":        parse_ig_metric(raw.get("videoViews", 0)),
                "hashtags":           raw.get("hashtags", []),
                "mentions":           raw.get("mentions", []),
                "post_type":          raw.get("postType", "photo"),
                "shortcode":          raw.get("shortcode", ""),
                "_roleButtonSpans":   raw.get("_roleButtonSpans", []),
            })

        except Exception as e:
            logger.debug(f"Post error: {e}")
            continue

    return posts, profile


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
        logger.error("Brave'i su sekilde baslat:")
        logger.error(f'  Start-Process "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe" -ArgumentList "--remote-debugging-port={IG_CDP_PORT}","--remote-allow-origins=*","--user-data-dir=C:\\tmp\\chrome-ig"')
        logger.error("Sonra instagram.com'a giris yap ve tekrar calistir.")
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
            posts, profile = scrape_user_posts(browser, ig_user, MAX_POSTS_PER_USER, DAYS_BACK)

            # Profil kaydet
            if profile:
                save_ig_profile(ig_user, profile)

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
                logger.warning("  SKIP: 0 post")

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
    logger.info("BATCH TAMAMLANDI")
    logger.info(f"  Basarili: {success}/{len(users)}")
    logger.info(f"  Skip: {skip}")
    logger.info(f"  Hata: {fail}")
    logger.info(f"  Toplam post: {total_posts:,}")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    main()
