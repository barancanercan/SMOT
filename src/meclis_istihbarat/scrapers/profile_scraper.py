#!/usr/bin/env python3
"""
Profile Scraper v1.0 - Twitter Profil Bilgileri
- Takipci sayisi
- Takip sayisi
- Tweet sayisi
- Listed count
"""

import time
import random
import re
from datetime import datetime
from typing import Dict, List, Optional
from meclis_istihbarat.utils.logger import get_logger
from meclis_istihbarat.utils.retry_config import retry_on_scraping_error

logger = get_logger("ProfileScraper")

# Add parent directory for imports

try:
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import (
        TimeoutException,
        NoSuchElementException
    )
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

try:
    import undetected_chromedriver as uc
    UNDETECTED_AVAILABLE = True
except ImportError:
    UNDETECTED_AVAILABLE = False


class ProfileScraper:
    """Twitter profil bilgilerini toplayan scraper"""

    def __init__(self, driver=None, headless=True):
        """
        Args:
            driver: Mevcut selenium driver (x_scraper'dan paylasilabilir)
            headless: Kendi driver olusturulacaksa headless mod
        """
        self.driver = driver
        self.own_driver = False

        if self.driver is None:
            self._init_driver(headless)
            self.own_driver = True

    def _init_driver(self, headless: bool):
        """Initialize Chrome driver"""
        if not SELENIUM_AVAILABLE or not UNDETECTED_AVAILABLE:
            raise Exception("Selenium veya undetected-chromedriver yuklu degil")

        import platform
        options = uc.ChromeOptions()

        if platform.system() == "Windows":
            options.binary_location = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"

        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--blink-settings=imagesEnabled=false")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

        self.driver = uc.Chrome(options=options, version_main=None, use_subprocess=False)

    def _parse_count(self, text: str) -> int:
        """Parse count strings like '1.2K', '5.5M', '123'"""
        if not text:
            return 0

        text = text.strip().upper()
        text = ''.join(c for c in text if c.isdigit() or c in ['.', 'K', 'M', 'B'])

        try:
            if 'K' in text:
                return int(float(text.replace('K', '')) * 1000)
            elif 'M' in text:
                return int(float(text.replace('M', '')) * 1_000_000)
            elif 'B' in text:
                return int(float(text.replace('B', '')) * 1_000_000_000)
            else:
                return int(text) if text else 0
        except Exception:
            return 0

    @retry_on_scraping_error
    def scrape_profile(self, username: str) -> Optional[Dict]:
        """
        Tek bir kullanicinin profil bilgilerini cek

        Returns:
            {
                'username': str,
                'followers': int,
                'following': int,
                'tweets': int,
                'listed': int,
                'scrape_date': str (YYYY-MM-DD)
            }
        """
        if not self.driver:
            logger.error("Driver yok")
            return None

        url = f"https://x.com/{username}"

        try:
            self.driver.get(url)
            time.sleep(random.uniform(2, 3))

            # Profil mevcut mu kontrol et
            try:
                self.driver.find_element(
                    By.XPATH,
                    "//span[contains(text(), 'does not exist') or contains(text(), 'mevcut de')]"
                )
                logger.warning(f"@{username}: Profil bulunamadi")
                return None
            except NoSuchElementException:
                pass  # Profile exists, continue

            # Profil yüklenmesini bekle
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@data-testid='UserName']"))
                )
            except TimeoutException:
                logger.warning(f"Timeout waiting for profile to load for @{username}")
                pass

            result = {
                'username': username,
                'followers': 0,
                'following': 0,
                'tweets': 0,
                'listed': 0,
                'scrape_date': datetime.now().strftime("%Y-%m-%d")
            }

            # ==========================================
            # FOLLOWERS COUNT
            # ==========================================
            try:
                # Method 1: aria-label from link
                followers_link = self.driver.find_element(
                    By.XPATH,
                    f"//a[@href='/{username}/verified_followers' or @href='/{username}/followers']"
                )
                followers_text = followers_link.text
                result['followers'] = self._parse_count(followers_text.split()[0])
            except NoSuchElementException:
                try:
                    # Method 2: Text content near "Followers"
                    followers_elem = self.driver.find_element(
                        By.XPATH,
                        "//span[contains(text(), 'Followers') or contains(text(), 'Takipci')]/.."
                    )
                    text = followers_elem.text
                    # Extract number before "Followers"
                    match = re.search(r'([\d.,KMB]+)\s*(Followers|Takipci)', text, re.IGNORECASE)
                    if match:
                        result['followers'] = self._parse_count(match.group(1))
                except Exception:
                    pass

            # ==========================================
            # FOLLOWING COUNT
            # ==========================================
            try:
                following_link = self.driver.find_element(
                    By.XPATH,
                    f"//a[@href='/{username}/following']"
                )
                following_text = following_link.text
                result['following'] = self._parse_count(following_text.split()[0])
            except NoSuchElementException:
                try:
                    following_elem = self.driver.find_element(
                        By.XPATH,
                        "//span[contains(text(), 'Following') or contains(text(), 'Takip')]/.."
                    )
                    text = following_elem.text
                    match = re.search(r'([\d.,KMB]+)\s*(Following|Takip)', text, re.IGNORECASE)
                    if match:
                        result['following'] = self._parse_count(match.group(1))
                except Exception:
                    pass

            # ==========================================
            # TWEET COUNT (posts)
            # ==========================================
            try:
                # Header'daki post sayisi
                posts_elem = self.driver.find_element(
                    By.XPATH,
                    "//div[@data-testid='UserName']/following::div[contains(text(), 'post') or contains(text(), 'gönderi')]"
                )
                posts_text = posts_elem.text
                result['tweets'] = self._parse_count(posts_text.split()[0])
            except NoSuchElementException:
                try:
                    # Alternative: Look for post count in header
                    header = self.driver.find_element(
                        By.XPATH,
                        "//div[@data-testid='primaryColumn']//h2[@role='heading']/.."
                    )
                    header_text = header.text
                    match = re.search(r'([\d.,KMB]+)\s*(posts?|gönderi)', header_text, re.IGNORECASE)
                    if match:
                        result['tweets'] = self._parse_count(match.group(1))
                except Exception:
                    pass

            # ==========================================
            # LISTED COUNT (optional)
            # ==========================================
            # Listed count genellikle profilde direkt gorunmuyor
            # Ileride eklenebilir

            return result

        except Exception as e:
            logger.error(f"@{username}: Hata - {str(e)[:50]}")
            return None

    def scrape_profiles(self, usernames: List[str]) -> List[Dict]:
        """
        Birden fazla kullanicinin profil bilgilerini cek

        Args:
            usernames: Kullanici adlari listesi

        Returns:
            Profil bilgileri listesi
        """
        logger.info(f"PROFIL SCRAPER v1.0 - Kullanici sayisi: {len(usernames)}")

        results = []

        for i, username in enumerate(usernames, 1):
            logger.info(f"[{i}/{len(usernames)}] @{username}")

            profile = self.scrape_profile(username)

            if profile:
                results.append(profile)
                logger.info(f"Takipci: {profile['followers']:,} | Takip: {profile['following']:,} | Tweet: {profile['tweets']:,}")
            else:
                logger.error(f"@{username} alinirken HATA")

            # Rate limiting
            if i < len(usernames):
                time.sleep(random.uniform(1, 2))

        logger.info(f"Tamamlandi: {len(results)}/{len(usernames)} profil")
        return results

    def scrape_and_save(self, usernames: List[str]) -> int:
        """
        Profilleri cek ve database'e kaydet

        Returns:
            Kaydedilen profil sayisi
        """
        from meclis_istihbarat.core.database import save_profile_snapshot

        profiles = self.scrape_profiles(usernames)
        saved = 0

        for p in profiles:
            success = save_profile_snapshot(
                username=p['username'],
                followers_count=p['followers'],
                following_count=p['following'],
                tweet_count=p['tweets'],
                listed_count=p['listed'],
                scrape_date=p['scrape_date']
            )
            if success:
                saved += 1

        logger.info(f"Database'e kaydedildi: {saved} profil")
        return saved

    def close(self):
        """Driver'i kapat (sadece kendi olusturduysa)"""
        if self.own_driver and self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


# ============================================================================
# HAFTALIK KARSILASTIRMA FONKSIYONLARI
# ============================================================================

def get_weekly_comparison(username: str) -> Optional[Dict]:
    """
    Son 7 gunluk profil degisimini getir

    Returns:
        {
            'username': str,
            'followers_change': int,
            'following_change': int,
            'tweets_change': int,
            'followers_start': int,
            'followers_end': int,
            'period_start': str,
            'period_end': str
        }
    """
    from meclis_istihbarat.core.database import get_all_profile_history
    from datetime import datetime, timedelta

    history = get_all_profile_history(username)

    if len(history) < 2:
        return None

    # Son kayit
    latest = history[-1]

    # 7 gun oncesine en yakin kayit
    target_date = datetime.strptime(latest['date'], "%Y-%m-%d") - timedelta(days=7)

    # En yakin kaydi bul
    closest = None
    min_diff = float('inf')

    for h in history[:-1]:
        h_date = datetime.strptime(h['date'], "%Y-%m-%d")
        diff = abs((h_date - target_date).days)
        if diff < min_diff:
            min_diff = diff
            closest = h

    if not closest:
        closest = history[0]  # En eski kayit

    return {
        'username': username,
        'followers_change': latest['followers'] - closest['followers'],
        'following_change': latest['following'] - closest['following'],
        'tweets_change': latest['tweets'] - closest['tweets'],
        'followers_start': closest['followers'],
        'followers_end': latest['followers'],
        'period_start': closest['date'],
        'period_end': latest['date']
    }


def get_all_weekly_comparisons(usernames: List[str]) -> List[Dict]:
    """Tum kullanicilar icin haftalik karsilastirma"""
    results = []

    for username in usernames:
        comparison = get_weekly_comparison(username)
        if comparison:
            results.append(comparison)

    return results


def print_weekly_report(usernames: List[str]):
    """Haftalik degisim raporu yazdir"""
    comparisons = get_all_weekly_comparisons(usernames)

    if not comparisons:
        logger.warning("Karsilastirma icin yeterli veri yok")
        return

    print(f"\n{'='*80}")
    print("HAFTALIK PROFIL DEGISIM RAPORU")
    print(f"{'='*80}")
    print(f"{'Kullanici':<20} {'Takipci':<15} {'Degisim':<12} {'Takip':<10} {'Tweet':<10}")
    print(f"{'-'*80}")

    for c in comparisons:
        followers_change = c['followers_change']
        change_str = f"+{followers_change}" if followers_change >= 0 else str(followers_change)

        print(f"@{c['username']:<19} {c['followers_end']:>10,} {change_str:>12} "
              f"{c['following_change']:>+10} {c['tweets_change']:>+10}")

    print(f"{'='*80}")
    print(f"Donem: {comparisons[0]['period_start']} - {comparisons[0]['period_end']}")
    print(f"{'='*80}\n")


# ============================================================================
# TEST / CLI
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Twitter Profil Scraper")
    parser.add_argument("--users", nargs="+", help="Kullanici adlari")
    parser.add_argument("--save", action="store_true", help="Database'e kaydet")
    parser.add_argument("--compare", action="store_true", help="Haftalik karsilastirma goster")

    args = parser.parse_args()

    if args.compare and args.users:
        print_weekly_report(args.users)
    elif args.users:
        with ProfileScraper() as scraper:
            if args.save:
                scraper.scrape_and_save(args.users)
            else:
                results = scraper.scrape_profiles(args.users)
                for r in results:
                    print(r)
    else:
        print("Kullanim:")
        print("  python profile_scraper.py --users user1 user2 --save")
        print("  python profile_scraper.py --users user1 user2 --compare")
