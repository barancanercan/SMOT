#!/usr/bin/env python3
"""
📊 Database Migration: Add views column to tweets table
Run once to upgrade schema v3.1 → v3.2
"""

import sqlite3
import sys

DB_PATH = "meclis.db"


def check_column_exists(cursor, table: str, column: str) -> bool:
    """Check if column exists in table"""
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    return column in columns


def migrate_add_views():
    """Add views column to tweets table"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        print("\n" + "=" * 60)
        print("📊 DATABASE MIGRATION: Add views column")
        print("=" * 60 + "\n")

        # Check if views column already exists
        if check_column_exists(cursor, "tweets", "views"):
            print("✅ Column 'views' already exists in tweets table")
            print("   No migration needed!\n")
            conn.close()
            return True

        # Add views column
        print("🔧 Adding 'views' column to tweets table...")
        cursor.execute("""
            ALTER TABLE tweets 
            ADD COLUMN views INTEGER DEFAULT 0
        """)
        conn.commit()

        print("✅ Migration successful!")
        print("   Column 'views' added with default value 0\n")

        # Verify
        if check_column_exists(cursor, "tweets", "views"):
            print("✅ Verification: Column 'views' confirmed in schema\n")

            # Show updated schema
            cursor.execute("PRAGMA table_info(tweets)")
            columns = cursor.fetchall()

            print("📋 Updated tweets table schema:")
            print("=" * 60)
            for col in columns:
                print(f"   {col[1]:20s} {col[2]:15s} {'NOT NULL' if col[3] else ''}")
            print("=" * 60 + "\n")

            print("✅ Database v3.2 ready!")
            print("   You can now run scraper_worker.py\n")
        else:
            print("❌ Verification failed!")
            conn.close()
            return False

        conn.close()
        return True

    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("✅ Column already exists (safe to ignore)")
            return True
        else:
            print(f"❌ Migration failed: {e}")
            return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    print("\n🏛️ Meclis İstihbarat Sistemi - Database Migration\n")

    success = migrate_add_views()

    if success:
        print("=" * 60)
        print("✅ MIGRATION COMPLETE")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Run scraper_worker.py to collect tweets with views")
        print("2. Views will be saved automatically\n")
        sys.exit(0)
    else:
        print("\n❌ Migration failed. Check errors above.\n")
        sys.exit(1)