#!/usr/bin/env python3
"""
Update Worker v1.0 - Haftalik Guncelleme

Gorevler:
1. Profil bilgilerini guncelle (takipci/takip sayisi)
2. Tweet embedding'lerini guncelle
3. Cache'i temizle
"""

import sqlite3
from datetime import datetime


from app.core.config import settings
from app.core.database import init_database, clear_expired_cache


def get_all_usernames():
    """Veritabanindaki tum kullanicilari getir"""
    conn = sqlite3.connect(settings.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT username FROM tweets")
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users


def update_profiles(usernames=None):
    """
    Profil bilgilerini guncelle

    Args:
        usernames: Guncellenecek kullanicilar (None = hepsi)
    """
    from app.services.scraping.profile_scraper import ProfileScraper

    if usernames is None:
        usernames = get_all_usernames()

    if not usernames:
        print("Guncellenecek kullanici yok")
        return 0

    print(f"\n{'='*60}")
    print("PROFIL GUNCELLEME")
    print(f"{'='*60}")
    print(f"Kullanici sayisi: {len(usernames)}")

    try:
        with ProfileScraper() as scraper:
            saved = scraper.scrape_and_save(usernames)
            return saved
    except Exception as e:
        print(f"Profil guncelleme hatasi: {e}")
        return 0


def update_embeddings(usernames=None):
    """
    Tweet embedding'lerini guncelle

    Args:
        usernames: Guncellenecek kullanicilar (None = hepsi)
    """
    from app.services.analysis.vector_db import rebuild_index

    print(f"\n{'='*60}")
    print("EMBEDDING GUNCELLEME")
    print(f"{'='*60}")

    if usernames:
        total = 0
        for username in usernames:
            print(f"\n@{username}:")
            count = rebuild_index(username)
            total += count
        return total
    else:
        return rebuild_index()


def clear_caches():
    """Suresi dolmus cache'leri temizle"""
    print(f"\n{'='*60}")
    print("CACHE TEMIZLEME")
    print(f"{'='*60}")

    deleted = clear_expired_cache()
    print(f"Silinen cache kaydi: {deleted}")
    return deleted


def run_full_update(usernames=None, skip_profiles=False, skip_embeddings=False):
    """
    Tam guncelleme calistir

    Args:
        usernames: Guncellenecek kullanicilar (None = hepsi)
        skip_profiles: Profil guncellemesini atla
        skip_embeddings: Embedding guncellemesini atla
    """
    print("\n" + "="*60)
    print("HAFTALIK GUNCELLEME BASLIYOR")
    print(f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*60)

    # Database kontrol
    init_database()

    results = {
        'profiles_updated': 0,
        'embeddings_updated': 0,
        'caches_cleared': 0
    }

    # 1. Profil guncelleme
    if not skip_profiles:
        results['profiles_updated'] = update_profiles(usernames)
    else:
        print("\nProfil guncellemesi atlandi")

    # 2. Embedding guncelleme
    if not skip_embeddings:
        results['embeddings_updated'] = update_embeddings(usernames)
    else:
        print("\nEmbedding guncellemesi atlandi")

    # 3. Cache temizleme
    results['caches_cleared'] = clear_caches()

    # Ozet
    print("\n" + "="*60)
    print("GUNCELLEME TAMAMLANDI")
    print("="*60)
    print(f"Profil: {results['profiles_updated']} guncellendi")
    print(f"Embedding: {results['embeddings_updated']} indexlendi")
    print(f"Cache: {results['caches_cleared']} temizlendi")
    print("="*60 + "\n")

    return results


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Haftalik Guncelleme Worker")
    parser.add_argument("--users", nargs="+", help="Belirli kullanicilar")
    parser.add_argument("--profiles-only", action="store_true", help="Sadece profil guncelle")
    parser.add_argument("--embeddings-only", action="store_true", help="Sadece embedding guncelle")
    parser.add_argument("--clear-cache", action="store_true", help="Sadece cache temizle")
    parser.add_argument("--list-users", action="store_true", help="Kullanicilari listele")

    args = parser.parse_args()

    if args.list_users:
        users = get_all_usernames()
        print(f"Kayitli kullanicilar ({len(users)}):")
        for u in users:
            print(f"  @{u}")

    elif args.clear_cache:
        clear_caches()

    elif args.profiles_only:
        update_profiles(args.users)

    elif args.embeddings_only:
        update_embeddings(args.users)

    else:
        run_full_update(
            usernames=args.users,
            skip_profiles=False,
            skip_embeddings=False
        )
