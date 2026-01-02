#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.database import init_database

print("\n" + "="*70)
print("DATABASE SETUP")
print("="*70 + "\n")

try:
    print("Creating database...")
    db = init_database("meclis.db")
    print("✅ Database created: meclis.db")
    print("✅ Tables created")
    print("\n" + "="*70)
    print("✅ SETUP COMPLETE!")
    print("="*70 + "\n")
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
