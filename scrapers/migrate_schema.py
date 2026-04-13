#!/usr/bin/env python3
"""
S.A.M - Schema Migration
Tüm eksik kolonları ekler. Tekrar çalıştırılabilir (idempotent).
"""
import sqlite3
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, "data", "sam.db")


def add_column_if_missing(conn, table, col, col_type):
    try:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
        conn.commit()
        print(f"  ✅ {table}.{col} eklendi")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print(f"  ⏭️  {table}.{col} zaten var")
        else:
            print(f"  ❌ {table}.{col} hata: {e}")


def main():
    print(f"DB: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")

    # ── tweets ──────────────────────────────────────────────
    print("\n📋 tweets tablosu:")
    for col, typ in [
        ("tweet_url",       "TEXT"),
        ("views",           "INTEGER DEFAULT 0"),
        ("bookmarks",       "INTEGER DEFAULT 0"),
        ("hashtags",        "TEXT"),
        ("mentions",        "TEXT"),
        ("media_urls",      "TEXT"),
        ("media_count",     "INTEGER DEFAULT 0"),
        ("quote_tweet_id",  "TEXT"),
        ("conversation_id", "TEXT"),
        ("source",          "TEXT"),
    ]:
        add_column_if_missing(conn, "tweets", col, typ)

    # ── instagram_posts ──────────────────────────────────────
    print("\n📷 instagram_posts tablosu:")
    for col, typ in [
        ("post_url",    "TEXT"),
        ("shortcode",   "TEXT"),
        ("post_type",   "TEXT DEFAULT 'photo'"),
        ("video_views", "INTEGER DEFAULT 0"),
        ("hashtags",    "TEXT"),
        ("mentions",    "TEXT"),
        ("saves",       "INTEGER DEFAULT 0"),
        ("shares",      "INTEGER DEFAULT 0"),
        ("media_count", "INTEGER DEFAULT 1"),
        ("location",    "TEXT"),
    ]:
        add_column_if_missing(conn, "instagram_posts", col, typ)

    # ── councilors ───────────────────────────────────────────
    print("\n👤 councilors tablosu:")
    for col, typ in [
        ("followers_count",      "INTEGER DEFAULT 0"),
        ("following_count",      "INTEGER DEFAULT 0"),
        ("tweet_count_total",    "INTEGER DEFAULT 0"),
        ("listed_count",         "INTEGER DEFAULT 0"),
        ("twitter_updated_at",   "DATETIME"),
        ("instagram_followers",  "INTEGER DEFAULT 0"),
        ("instagram_following",  "INTEGER DEFAULT 0"),
        ("instagram_posts_count","INTEGER DEFAULT 0"),
        ("instagram_updated_at", "DATETIME"),
    ]:
        add_column_if_missing(conn, "councilors", col, typ)

    conn.close()

    # Doğrula
    print("\n✅ Final şema:")
    conn = sqlite3.connect(DB_PATH)
    for table in ["tweets", "instagram_posts", "councilors"]:
        c = conn.cursor()
        c.execute(f"PRAGMA table_info({table})")
        cols = [r[1] for r in c.fetchall()]
        c.execute(f"SELECT COUNT(*) FROM {table}")
        cnt = c.fetchone()[0]
        print(f"  {table} ({cnt} kayıt): {cols}")
    conn.close()
    print("\nMigration tamamlandı!")


if __name__ == "__main__":
    main()
