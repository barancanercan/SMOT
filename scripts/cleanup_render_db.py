"""
Render PostgreSQL veritabanındaki yanlış Instagram postlarını ve
duplicate kayıtları temizler.

Kullanım:
    python scripts/cleanup_render_db.py "postgresql://user:pass@host/dbname"
"""

import re
import sys
from collections import defaultdict

try:
    import psycopg2
except ImportError:
    print("psycopg2 gerekli: pip install psycopg2-binary")
    sys.exit(1)


def cleanup(database_url: str) -> None:
    conn = psycopg2.connect(database_url)
    conn.autocommit = False
    cur = conn.cursor()

    # 1. Yanlış 06AhmetOksuz postlarını sil
    cur.execute("DELETE FROM instagram_posts WHERE username = '06AhmetOksuz'")
    deleted = cur.rowcount
    print(f"Deleted wrong 06AhmetOksuz posts: {deleted}")

    cur.execute("""
        UPDATE councilors
        SET instagram_followers = NULL,
            instagram_following = NULL,
            instagram_posts_count = NULL,
            instagram_updated_at = NULL
        WHERE username = '06AhmetOksuz'
    """)
    print("Reset 06AhmetOksuz instagram stats")

    # 2. Duplicate postları shortcode bazında temizle
    cur.execute("SELECT id, post_url FROM instagram_posts WHERE post_url IS NOT NULL")
    posts = cur.fetchall()

    by_shortcode: dict = defaultdict(list)
    for id_, url in posts:
        m = re.search(r"/p/([A-Za-z0-9_-]+)", url or "")
        if m:
            by_shortcode[m.group(1)].append((id_, url))

    to_delete = []
    for sc, entries in by_shortcode.items():
        if len(entries) > 1:
            # Prefer URL with username in path (more explicit)
            entries_sorted = sorted(
                entries,
                key=lambda e: len([p for p in e[1].split("/") if p and "instagram.com" not in p]),
                reverse=True,
            )
            for d in entries_sorted[1:]:
                to_delete.append(d[0])

    if to_delete:
        cur.execute(
            "DELETE FROM instagram_posts WHERE id = ANY(%s)",
            (to_delete,),
        )
        print(f"Deleted {len(to_delete)} duplicate posts")
    else:
        print("No duplicates found")

    conn.commit()

    cur.execute("SELECT COUNT(*) FROM instagram_posts")
    total = cur.fetchone()[0]

    cur.execute("""
        SELECT ip.username, c.name, ip.likes, LEFT(ip.caption, 50)
        FROM instagram_posts ip
        LEFT JOIN councilors c ON ip.username = c.instagram_username
        ORDER BY ip.likes DESC
        LIMIT 5
    """)
    top5 = cur.fetchall()
    print(f"\nTotal posts: {total}")
    print("Top 5 posts after cleanup:")
    for r in top5:
        print(f"  {r}")

    cur.close()
    conn.close()
    print("\nDone!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanim: python scripts/cleanup_render_db.py \"<External Database URL>\"")
        sys.exit(1)
    cleanup(sys.argv[1])
