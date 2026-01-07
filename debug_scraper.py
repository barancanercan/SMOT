#!/usr/bin/env python3
"""
🔬 ULTRA DEBUG - Ham veri + Element inspection
Scroll, selector, HTML - herşeyi göster
"""

from x_scraper import XTwitterScraper
import time


def ultra_debug():
    """Ultra detailed debug"""
    print("\n" + "=" * 80)
    print("🔬 ULTRA DEBUG - RAW DATA INSPECTION")
    print("=" * 80 + "\n")

    scraper = XTwitterScraper(headless=False, require_login=True)

    if not scraper.logged_in:
        print("❌ Login failed")
        return

    username = "atila_celik06"
    print(f"✅ Login OK, navigating to @{username}...\n")

    try:
        url = f"https://x.com/{username}"
        scraper.driver.get(url)
        time.sleep(3)
        scraper._wait_for_page_load()

        # ===== PHASE 1: Initial State =====
        print("\n" + "=" * 80)
        print("PHASE 1: INITIAL STATE INSPECTION")
        print("=" * 80 + "\n")

        # Get initial metrics
        initial_height = scraper.driver.execute_script("return document.body.scrollHeight")
        initial_scroll_y = scraper.driver.execute_script("return window.scrollY")
        initial_inner_height = scraper.driver.execute_script("return window.innerHeight")

        print(f"📏 PAGE DIMENSIONS:")
        print(f"   Page Height (scrollHeight): {initial_height}")
        print(f"   Window Inner Height: {initial_inner_height}")
        print(f"   Current Scroll Y: {initial_scroll_y}")
        print(f"   Viewport Height: {initial_inner_height}\n")

        # Find all tweet elements
        elements = scraper.driver.find_elements("xpath", "//article[@data-testid='tweet']")
        print(f"📌 TWEET ELEMENTS FOUND: {len(elements)}\n")

        # ===== PHASE 2: Individual Element Inspection =====
        print("=" * 80)
        print("PHASE 2: INDIVIDUAL ELEMENT INSPECTION")
        print("=" * 80 + "\n")

        for idx, element in enumerate(elements[:5], 1):
            print(f"━━━ ELEMENT #{idx} ━━━\n")

            # Get element position
            try:
                location = element.location
                size = element.size
                print(f"📍 POSITION:")
                print(f"   X: {location['x']}, Y: {location['y']}")
                print(f"   Width: {size['width']}, Height: {size['height']}\n")
            except:
                print(f"❌ Position error\n")

            # Get raw HTML snippet
            try:
                html = element.get_attribute("innerHTML")[:300]
                print(f"📄 RAW HTML (first 300 chars):")
                print(f"   {html}...\n")
            except:
                pass

            # Try different text extraction methods
            print(f"📝 TEXT EXTRACTION ATTEMPTS:")

            # Method 1: _get_tweet_text
            try:
                text1 = scraper._get_tweet_text(element)
                print(f"   ✅ _get_tweet_text: {text1[:60] if text1 else 'NULL'}...")
            except Exception as e:
                print(f"   ❌ _get_tweet_text: {e}")

            # Method 2: Direct selector
            try:
                text2 = element.find_element("xpath", ".//div[@data-testid='tweetText']//span").text
                print(f"   ✅ tweetText span: {text2[:60]}...")
            except:
                print(f"   ❌ tweetText span: NOT FOUND")

            # Method 3: Direct text
            try:
                text3 = element.text
                print(f"   ✅ element.text: {text3[:60] if text3 else 'NULL'}...")
            except:
                print(f"   ❌ element.text: ERROR")

            # Date check
            try:
                time_elem = element.find_element("xpath", ".//time")
                timestamp = time_elem.get_attribute("datetime")
                print(f"   ✅ DateTime: {timestamp}")
            except:
                print(f"   ❌ DateTime: NOT FOUND")

            print()

        # ===== PHASE 3: Scroll Test =====
        print("=" * 80)
        print("PHASE 3: SCROLL MECHANICS TEST")
        print("=" * 80 + "\n")

        print("⏳ Testing scroll behavior...\n")

        for scroll_num in range(5):
            print(f"SCROLL #{scroll_num}:")

            # Before scroll
            before_height = scraper.driver.execute_script("return document.body.scrollHeight")
            before_y = scraper.driver.execute_script("return window.scrollY")

            print(f"   Before: height={before_height}, scrollY={before_y}")

            # DO THE SCROLL
            scroll_distance = 1500
            scraper.driver.execute_script(f"window.scrollBy(0, {scroll_distance});")

            print(f"   → Scrolling by {scroll_distance}px...")
            time.sleep(1)

            # After scroll
            after_height = scraper.driver.execute_script("return document.body.scrollHeight")
            after_y = scraper.driver.execute_script("return window.scrollY")

            print(f"   After: height={after_height}, scrollY={after_y}")

            # Analyze
            height_change = after_height - before_height
            scroll_change = after_y - before_y

            print(f"   Changes: height_delta={height_change}, scroll_delta={scroll_change}")

            if height_change > 0:
                print(f"   ✅ New content loaded!")
            elif scroll_change == 0:
                print(f"   ❌ SCROLL DIDN'T WORK! (scrollY unchanged)")
            elif height_change == 0:
                print(f"   ⚠️  Height unchanged but scrollY moved")

            # Count tweets
            current_elements = scraper.driver.find_elements("xpath", "//article[@data-testid='tweet']")
            print(f"   🔢 Total tweets on page: {len(current_elements)}\n")

            if height_change == 0 and scroll_change == 0:
                print("   🛑 STOPPING: No scroll movement and no new content\n")
                break

        # ===== PHASE 4: Network Activity =====
        print("=" * 80)
        print("PHASE 4: PAGE LOAD CHECK")
        print("=" * 80 + "\n")

        # Check if page is still loading
        ready_state = scraper.driver.execute_script("return document.readyState")
        print(f"📄 Document Ready State: {ready_state}")

        # Check for loading indicators
        try:
            loading = scraper.driver.find_elements("xpath", "//div[contains(@class, 'loading')]")
            print(f"⏳ Loading indicators found: {len(loading)}")
        except:
            pass

        # Final tweet count
        final_elements = scraper.driver.find_elements("xpath", "//article[@data-testid='tweet']")
        print(f"\n📊 FINAL TWEET COUNT: {len(final_elements)}")

        scraper.close()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        scraper.close()


if __name__ == "__main__":
    ultra_debug()