"""
Database Migration Script - Add Instagram columns to existing tables
Run this on production to add missing columns without losing data.
"""
import sqlite3
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings


def get_db_path():
    """Extract SQLite database path from URL"""
    db_url = settings.database_url
    if db_url.startswith("sqlite:///"):
        return db_url.replace("sqlite:///", "")
    return None


def column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns


def table_exists(cursor, table_name):
    """Check if a table exists"""
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    return cursor.fetchone() is not None


def migrate():
    """Run migration to add Instagram columns"""
    db_path = get_db_path()
    if not db_path:
        print("Error: Only SQLite databases are supported")
        return False

    print(f"Database: {db_path}")

    if not os.path.exists(db_path):
        print(f"Error: Database file not found: {db_path}")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # =====================================================
        # 1. Add columns to councilors table
        # =====================================================
        print("\n[1/3] Checking councilors table...")

        if not table_exists(cursor, "councilors"):
            print("  - councilors table not found, skipping")
        else:
            # Add instagram_username
            if not column_exists(cursor, "councilors", "instagram_username"):
                print("  - Adding instagram_username column...")
                cursor.execute("ALTER TABLE councilors ADD COLUMN instagram_username VARCHAR(100)")
                print("  - Done")
            else:
                print("  - instagram_username already exists")

            # Add instagram_updated_at
            if not column_exists(cursor, "councilors", "instagram_updated_at"):
                print("  - Adding instagram_updated_at column...")
                cursor.execute("ALTER TABLE councilors ADD COLUMN instagram_updated_at DATETIME")
                print("  - Done")
            else:
                print("  - instagram_updated_at already exists")

        # =====================================================
        # 2. Create instagram_posts table if not exists
        # =====================================================
        print("\n[2/3] Checking instagram_posts table...")

        if not table_exists(cursor, "instagram_posts"):
            print("  - Creating instagram_posts table...")
            cursor.execute("""
                CREATE TABLE instagram_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(100) NOT NULL,
                    post_id VARCHAR(100),
                    caption TEXT,
                    post_type VARCHAR(20) DEFAULT 'photo',
                    likes INTEGER DEFAULT 0,
                    comments INTEGER DEFAULT 0,
                    views INTEGER DEFAULT 0,
                    post_url VARCHAR(500),
                    thumbnail_url VARCHAR(500),
                    timestamp DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("CREATE INDEX ix_instagram_posts_username ON instagram_posts (username)")
            cursor.execute("CREATE INDEX ix_instagram_posts_timestamp ON instagram_posts (timestamp)")
            print("  - Done")
        else:
            print("  - instagram_posts table already exists")

        # =====================================================
        # 3. Create instagram_profiles table if not exists
        # =====================================================
        print("\n[3/3] Checking instagram_profiles table...")

        if not table_exists(cursor, "instagram_profiles"):
            print("  - Creating instagram_profiles table...")
            cursor.execute("""
                CREATE TABLE instagram_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(100) NOT NULL,
                    full_name VARCHAR(200),
                    bio TEXT,
                    followers_count INTEGER DEFAULT 0,
                    following_count INTEGER DEFAULT 0,
                    posts_count INTEGER DEFAULT 0,
                    is_verified BOOLEAN DEFAULT 0,
                    profile_pic_url VARCHAR(500),
                    scrape_date DATE NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("CREATE INDEX ix_instagram_profiles_username ON instagram_profiles (username)")
            cursor.execute("CREATE INDEX ix_instagram_profiles_scrape_date ON instagram_profiles (scrape_date)")
            print("  - Done")
        else:
            print("  - instagram_profiles table already exists")

        # =====================================================
        # 4. Add listed_count to profile_history if missing
        # =====================================================
        print("\n[Bonus] Checking profile_history table...")

        if table_exists(cursor, "profile_history"):
            if not column_exists(cursor, "profile_history", "listed_count"):
                print("  - Adding listed_count column...")
                cursor.execute("ALTER TABLE profile_history ADD COLUMN listed_count INTEGER DEFAULT 0")
                print("  - Done")
            else:
                print("  - listed_count already exists")

        # Commit all changes
        conn.commit()
        print("\n✅ Migration completed successfully!")
        return True

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 50)
    print("Instagram Migration Script")
    print("=" * 50)
    migrate()
