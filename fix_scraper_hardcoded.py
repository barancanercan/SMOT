#!/usr/bin/env python3
"""Fix hardcoded values in scrape_tweets method"""

with open('x_scraper.py', 'r') as f:
    content = f.read()

# Fix 1: max_scrolls = 25 → self.MAX_SCROLLS
if 'max_scrolls = 25' in content:
    print("⚠️  Found hardcoded: max_scrolls = 25")
    content = content.replace('max_scrolls = 25', 'max_scrolls = self.MAX_SCROLLS')
    print("✅ Fixed to: max_scrolls = self.MAX_SCROLLS")

# Fix 2: found_old_tweets > 10 → found_old_tweets > self.CONSECUTIVE_OLD_THRESHOLD
if 'found_old_tweets > 10' in content:
    print("⚠️  Found hardcoded: found_old_tweets > 10")
    content = content.replace('found_old_tweets > 10', 'found_old_tweets > self.CONSECUTIVE_OLD_THRESHOLD')
    print("✅ Fixed to: found_old_tweets > self.CONSECUTIVE_OLD_THRESHOLD")

# Fix 3: consecutive_old > 5 (if any remain)
if 'consecutive_old > 5' in content:
    print("⚠️  Found hardcoded: consecutive_old > 5")
    content = content.replace('consecutive_old > 5', 'consecutive_old > self.CONSECUTIVE_OLD_THRESHOLD')
    print("✅ Fixed to: consecutive_old > self.CONSECUTIVE_OLD_THRESHOLD")

with open('x_scraper.py', 'w') as f:
    f.write(content)

print("\n✅ x_scraper.py fixed!")
print("\nVerification:")
import subprocess
subprocess.run(['grep', '-n', 'max_scrolls\|found_old\|consecutive_old >', 'x_scraper.py'])

