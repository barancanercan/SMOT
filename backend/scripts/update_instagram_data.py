#!/usr/bin/env python3
"""
Instagram verilerini guncelle - Selenium ile yorum ve etkilesim verilerini cek
Updated: 2026 - Uses Selenium with embedded JSON extraction
"""
import sys
import os
import time
import random
import argparse

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, date
from app.core.database import session_scope
from app.core.models import Councilor, InstagramPost, InstagramProfile
from app.services.scraping.instagram_scraper import InstagramScraper


def update_existing_posts_engagement(limit: int = 100, delay: float = 2.0):
    """
    Mevcut postlarin yorum/begeni verilerini guncelle (sadece comments=0 olanlar)
    """
    print("=" * 60)
    print("Mevcut Postlari Guncelle (Engagement)")
    print("=" * 60)

    # Get posts without captions (or without comments)
    with session_scope() as session:
        posts = session.query(InstagramPost).filter(
            (InstagramPost.caption == '') | (InstagramPost.caption == None) | (InstagramPost.comments == 0)
        ).order_by(InstagramPost.likes.desc()).limit(limit).all()

        post_data = [(p.id, p.post_url, p.username) for p in posts]

    print(f"Guncellenecek {len(post_data)} post bulundu")
    print()

    if not post_data:
        print("Guncellenecek post yok!")
        return

    # Initialize scraper with manual login
    print("Browser baslatiliyor (manuel login gerekli)...")
    scraper = InstagramScraper(headless=False, require_manual_login=True)

    if not scraper.driver:
        print("HATA: Browser baslatilamadi!")
        return

    if not scraper.logged_in:
        print("HATA: Instagram girisi yapilamadi!")
        scraper.close()
        return

    print()
    print("Post guncelleme basliyor...")
    print("-" * 60)

    updated = 0
    errors = []

    for i, (post_id, post_url, username) in enumerate(post_data, 1):
        print(f"\n[{i}/{len(post_data)}] @{username}")
        print(f"  URL: {post_url}")

        try:
            data = scraper.update_post_engagement(post_url)

            if data and (data['likes'] > 0 or data['comments'] > 0 or data.get('caption')):
                # Update in database
                with session_scope() as session:
                    post = session.query(InstagramPost).filter(
                        InstagramPost.id == post_id
                    ).first()
                    if post:
                        post.likes = data['likes']
                        post.comments = data['comments']
                        if data.get('caption'):
                            post.caption = data['caption']
                        updated += 1
                        caption_preview = data.get('caption', '')[:50] + '...' if data.get('caption') else '(yok)'
                        print(f"  -> {data['likes']} like, {data['comments']} yorum")
                        print(f"  -> Caption: {caption_preview}")
            else:
                print(f"  -> Veri alinamadi")

            # Delay
            if i < len(post_data):
                actual_delay = delay + random.uniform(0, 1)
                time.sleep(actual_delay)

        except Exception as e:
            error_msg = f"Post {post_id}: {str(e)[:50]}"
            errors.append(error_msg)
            print(f"  HATA: {str(e)[:50]}")
            time.sleep(5)

    scraper.close()

    print()
    print("=" * 60)
    print("OZET")
    print("=" * 60)
    print(f"Guncellenen post: {updated}/{len(post_data)}")
    print(f"Hatalar: {len(errors)}")


def scrape_fresh_data(max_posts_per_user: int = 50, delay_between_users: float = 3.0, test_mode: bool = False):
    """
    Tum Instagram hesaplarini bastan scrape et (Selenium)
    """
    print("=" * 60)
    print("Instagram Veri Scraping (Selenium)")
    print("=" * 60)

    # Get all members with Instagram accounts
    with session_scope() as session:
        members = session.query(Councilor).filter(
            Councilor.instagram_username != None,
            Councilor.instagram_username != ''
        ).all()

        usernames = [(m.instagram_username, m.username, m.name) for m in members]

    if test_mode:
        usernames = usernames[:3]
        print(f"TEST MODU: Sadece {len(usernames)} kullanici")

    print(f"Toplam {len(usernames)} Instagram hesabi bulundu")
    print()

    # Initialize scraper with manual login
    print("Browser baslatiliyor (manuel login gerekli)...")
    scraper = InstagramScraper(headless=False, require_manual_login=True)

    if not scraper.driver:
        print("HATA: Browser baslatilamadi!")
        return

    if not scraper.logged_in:
        print("HATA: Instagram girisi yapilamadi!")
        scraper.close()
        return

    print()
    print("Scraping basliyor...")
    print("-" * 60)

    total_posts = 0
    total_profiles = 0
    errors = []

    for i, (ig_username, twitter_username, name) in enumerate(usernames, 1):
        print(f"\n[{i}/{len(usernames)}] @{ig_username} ({name})")

        try:
            # Scrape profile
            profile = scraper.scrape_profile(ig_username)

            if profile:
                # Save/Update profile
                with session_scope() as session:
                    # Convert scrape_date string to date object for comparison
                    scrape_date_for_query = profile['scrape_date']
                    if isinstance(scrape_date_for_query, str):
                        scrape_date_for_query = datetime.strptime(scrape_date_for_query, '%Y-%m-%d').date()

                    existing = session.query(InstagramProfile).filter(
                        InstagramProfile.username == ig_username,
                        InstagramProfile.scrape_date == scrape_date_for_query
                    ).first()

                    if not existing:
                        # Convert scrape_date string to date object
                        scrape_date_val = profile['scrape_date']
                        if isinstance(scrape_date_val, str):
                            scrape_date_val = datetime.strptime(scrape_date_val, '%Y-%m-%d').date()

                        new_profile = InstagramProfile(
                            username=ig_username,
                            full_name=profile.get('full_name', ''),
                            bio=profile.get('bio', ''),
                            followers_count=profile.get('followers', 0),
                            following_count=profile.get('following', 0),
                            posts_count=profile.get('posts_count', 0),
                            scrape_date=scrape_date_val
                        )
                        session.add(new_profile)
                        total_profiles += 1
                        print(f"  Profil: {profile.get('followers', 0):,} takipci")

            # Scrape posts
            posts = scraper.scrape_posts(ig_username, max_posts=max_posts_per_user, days_back=90)

            if posts:
                # Save/Update posts
                with session_scope() as session:
                    new_count = 0
                    updated_count = 0

                    for post in posts:
                        existing = session.query(InstagramPost).filter(
                            InstagramPost.username == ig_username,
                            InstagramPost.post_url == post['post_url']
                        ).first()

                        if existing:
                            # Update existing post with new engagement data
                            existing.likes = post.get('likes', 0)
                            existing.comments = post.get('comments', 0)
                            updated_count += 1
                        else:
                            # Create new post
                            post_date = post.get('post_date')
                            if post_date:
                                if isinstance(post_date, str):
                                    try:
                                        post_date = datetime.fromisoformat(post_date.replace('Z', '+00:00'))
                                    except:
                                        post_date = datetime.now()
                            else:
                                post_date = datetime.now()

                            new_post = InstagramPost(
                                username=ig_username,
                                caption=post.get('caption', '')[:2500],
                                post_date=post_date,
                                post_url=post['post_url'],
                                likes=post.get('likes', 0),
                                comments=post.get('comments', 0),
                                is_video=post.get('is_video', False)
                            )
                            session.add(new_post)
                            new_count += 1

                    total_posts += new_count
                    print(f"  Postlar: {new_count} yeni, {updated_count} guncellendi")

                    # Show sample
                    if posts:
                        sample = posts[0]
                        print(f"  Ornek: {sample.get('likes', 0)} like, {sample.get('comments', 0)} yorum")

            # Delay between users
            if i < len(usernames):
                delay = delay_between_users + random.uniform(0, 2)
                print(f"  Bekleniyor: {delay:.1f}s...")
                time.sleep(delay)

        except Exception as e:
            error_msg = f"@{ig_username}: {str(e)[:50]}"
            errors.append(error_msg)
            print(f"  HATA: {str(e)[:50]}")
            time.sleep(5)

    scraper.close()

    print()
    print("=" * 60)
    print("OZET")
    print("=" * 60)
    print(f"Toplam profil guncellendi: {total_profiles}")
    print(f"Toplam yeni post: {total_posts}")
    print(f"Hatalar: {len(errors)}")

    if errors:
        print("\nHatalar:")
        for err in errors:
            print(f"  - {err}")

    # Verify
    print("\nYorum verileri kontrol ediliyor...")
    with session_scope() as session:
        from sqlalchemy import func
        total_comments = session.query(func.sum(InstagramPost.comments)).scalar() or 0
        posts_with_comments = session.query(InstagramPost).filter(InstagramPost.comments > 0).count()
        print(f"  Toplam yorum: {total_comments:,}")
        print(f"  Yorumlu post sayisi: {posts_with_comments}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Instagram verilerini guncelle (Selenium)")

    subparsers = parser.add_subparsers(dest='command', help='Komutlar')

    # Update existing posts
    update_parser = subparsers.add_parser('update', help='Mevcut postlarin engagement verilerini guncelle')
    update_parser.add_argument("--limit", type=int, default=100, help="Guncellenecek max post sayisi")
    update_parser.add_argument("--delay", type=float, default=2.0, help="Postlar arasi bekleme (saniye)")

    # Fresh scrape
    scrape_parser = subparsers.add_parser('scrape', help='Tum verileri bastan cek')
    scrape_parser.add_argument("--max-posts", type=int, default=50, help="Kullanici basina max post")
    scrape_parser.add_argument("--delay", type=float, default=3.0, help="Kullanicilar arasi bekleme (saniye)")
    scrape_parser.add_argument("--test", action="store_true", help="Sadece 3 kullanici ile test")

    args = parser.parse_args()

    if args.command == 'update':
        update_existing_posts_engagement(
            limit=args.limit,
            delay=args.delay
        )
    elif args.command == 'scrape':
        scrape_fresh_data(
            max_posts_per_user=args.max_posts,
            delay_between_users=args.delay,
            test_mode=args.test
        )
    else:
        print("Kullanim:")
        print("  python update_instagram_data.py update --limit 100  # Mevcut postlari guncelle")
        print("  python update_instagram_data.py scrape --test       # Test modunda scrape")
        print("  python update_instagram_data.py scrape              # Tum verileri scrape")
        print()
        print("Detaylar icin: python update_instagram_data.py --help")
