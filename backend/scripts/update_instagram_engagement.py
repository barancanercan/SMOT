#!/usr/bin/env python3
"""
Instagram Engagement Updater - Instaloader API Based
Updates likes/comments for posts with missing engagement data (0 likes)

Uses instaloader which is 100% reliable for engagement data.
"""
import os
import sys
import time
import random
from datetime import datetime

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


def main():
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

    # Get posts needing update
    posts = get_posts_needing_update(conn, limit=200)

    if not posts:
        print("\nNo posts with 0 likes found. Database is up to date!")
        return

    print(f"\nFound {len(posts)} posts with missing engagement data")
    print("-" * 60)

    updated = 0
    failed = 0

    for i, (post_id, username, post_url, caption, old_likes, old_comments) in enumerate(posts, 1):
        shortcode = extract_shortcode(post_url)
        if not shortcode:
            logger.warning(f"[{i}] Invalid URL: {post_url}")
            failed += 1
            continue

        print(f"[{i}/{len(posts)}] @{username} - {shortcode}")

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

    conn.close()

    print("\n" + "=" * 60)
    print(f"DONE: Updated {updated}, Failed {failed}")
    print("=" * 60)


if __name__ == "__main__":
    main()
