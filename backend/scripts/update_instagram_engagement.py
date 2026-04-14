#!/usr/bin/env python3
"""
Instagram Engagement Updater - Instaloader API Based
Updates likes/comments for posts with:
  - 0 likes (failed scrape)
  - Suspicious ratio: many comments but very few likes (likely scraping error)

Uses instaloader which is 100% reliable for engagement data.

Usage:
    python update_instagram_engagement.py              # Only 0-like posts
    python update_instagram_engagement.py --suspicious # Also fix suspicious ratios
    python update_instagram_engagement.py --all        # Both modes
"""
import argparse
import os
import random
import sys
import time

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger("EngagementUpdater")

# Check instaloader
try:
    import instaloader
    from instaloader import Post
    INSTALOADER_AVAILABLE = True
except ImportError:
    INSTALOADER_AVAILABLE = False
    logger.error("instaloader not installed! Run: pip install instaloader")


def get_db_connection():
    """Get SQLite connection"""
    import sqlite3
    db_url = settings.database_url
    if db_url.startswith("sqlite:///"):
        db_path = db_url.replace("sqlite:///", "")
        return sqlite3.connect(db_path)
    raise Exception("Only SQLite supported")


def get_posts_needing_update(conn, limit: int = 100):
    """Get posts with 0 likes (failed scrape)"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, username, post_url, caption, likes, comments
        FROM instagram_posts
        WHERE likes = 0 OR likes IS NULL
        ORDER BY post_date DESC
        LIMIT ?
    """, (limit,))
    return cursor.fetchall()


def get_posts_suspicious_engagement(conn, limit: int = 200):
    """
    Get posts with suspicious engagement ratio:
    comments >> likes suggests likes were not scraped correctly.

    Threshold: comments > likes * 10 AND likes < 50 AND comments >= 5
    (e.g. 66 comments but only 3 likes is clearly wrong)
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, username, post_url, caption, likes, comments
        FROM instagram_posts
        WHERE comments >= 5
          AND (likes IS NULL OR likes < 50)
          AND comments > COALESCE(likes, 0) * 10
        ORDER BY comments DESC, post_date DESC
        LIMIT ?
    """, (limit,))
    return cursor.fetchall()


def extract_shortcode(post_url: str) -> str:
    """Extract shortcode from Instagram URL"""
    # https://www.instagram.com/p/ABC123/ -> ABC123
    # https://www.instagram.com/reel/ABC123/ -> ABC123
    import re
    match = re.search(r'/(?:p|reel)/([A-Za-z0-9_-]+)', post_url)
    return match.group(1) if match else None


def update_engagement_instaloader(loader, shortcode: str) -> dict:
    """
    Get engagement data using instaloader API

    Returns:
        {'likes': int, 'comments': int, 'caption': str} or None
    """
    try:
        post = Post.from_shortcode(loader.context, shortcode)
        return {
            'likes': post.likes,
            'comments': post.comments,
            'caption': post.caption or '',
            'is_video': post.is_video,
        }
    except Exception as e:
        logger.warning(f"  -> Error: {str(e)[:50]}")
        return None


def update_post_in_db(conn, post_id: int, data: dict):
    """Update post engagement in database"""
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE instagram_posts
        SET likes = ?, comments = ?, caption = COALESCE(?, caption)
        WHERE id = ?
    """, (data['likes'], data['comments'], data['caption'], post_id))
    conn.commit()


def process_posts(loader, conn, posts: list, label: str) -> tuple[int, int]:
    """Process a list of posts and update their engagement data. Returns (updated, failed)."""
    if not posts:
        print(f"\nNo {label} found.")
        return 0, 0

    print(f"\nFound {len(posts)} {label}")
    print("-" * 60)

    updated = 0
    failed = 0

    for i, (post_id, username, post_url, _caption, old_likes, old_comments) in enumerate(posts, 1):
        shortcode = extract_shortcode(post_url)
        if not shortcode:
            logger.warning(f"[{i}] Invalid URL: {post_url}")
            failed += 1
            continue

        print(f"[{i}/{len(posts)}] @{username} - {shortcode}  (was: {old_likes} likes, {old_comments} comments)")

        try:
            data = update_engagement_instaloader(loader, shortcode)

            if data:
                update_post_in_db(conn, post_id, data)
                print(f"  -> Updated: {data['likes']} likes, {data['comments']} comments")
                updated += 1
            else:
                failed += 1

        except Exception as e:
            logger.error(f"  -> Error: {e}")
            failed += 1

        # Rate limiting - Instagram is strict
        if i < len(posts):
            delay = random.uniform(2, 4)
            time.sleep(delay)

        # Progress checkpoint every 20 posts
        if i % 20 == 0:
            print(f"\n--- Progress: {i}/{len(posts)} | Updated: {updated} | Failed: {failed} ---\n")

    return updated, failed


def main():
    parser = argparse.ArgumentParser(description="Update Instagram engagement data")
    parser.add_argument("--suspicious", action="store_true",
                        help="Also fix posts with suspicious engagement ratio (high comments, very low likes)")
    parser.add_argument("--all", dest="all_modes", action="store_true",
                        help="Run both 0-likes and suspicious-ratio checks")
    parser.add_argument("--limit", type=int, default=200,
                        help="Max posts to process per mode (default: 200)")
    args = parser.parse_args()

    if not INSTALOADER_AVAILABLE:
        print("ERROR: instaloader not installed!")
        print("Run: pip install instaloader")
        return

    print("=" * 60)
    print("Instagram Engagement Updater")
    print("=" * 60)

    # Initialize instaloader
    loader = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False,
        post_metadata_txt_pattern='',
        request_timeout=30,
    )

    print("\nInstaloader initialized (no login = public posts only)")
    print("For private accounts, you need to login first.")

    # Get database connection
    conn = get_db_connection()

    total_updated = 0
    total_failed = 0

    # Mode 1: 0-likes posts (always run)
    posts_zero = get_posts_needing_update(conn, limit=args.limit)
    u, f = process_posts(loader, conn, posts_zero, "posts with 0 likes (failed scrape)")
    total_updated += u
    total_failed += f

    # Mode 2: suspicious engagement ratio (opt-in)
    if args.suspicious or args.all_modes:
        print("\n" + "=" * 60)
        print("Checking suspicious engagement ratios (high comments, very low likes)...")
        posts_suspicious = get_posts_suspicious_engagement(conn, limit=args.limit)
        u, f = process_posts(loader, conn, posts_suspicious, "posts with suspicious engagement ratio")
        total_updated += u
        total_failed += f
    else:
        # Show hint about suspicious posts
        suspicious = get_posts_suspicious_engagement(conn, limit=args.limit)
        if suspicious:
            print(f"\nHint: Found {len(suspicious)} posts with suspicious engagement ratio")
            print("      (e.g. many comments but very few likes — likely scraping error)")
            print("      Run with --suspicious to fix these too.")

    conn.close()

    print("\n" + "=" * 60)
    print(f"DONE: Updated {total_updated}, Failed {total_failed}")
    print("=" * 60)


if __name__ == "__main__":
    main()
