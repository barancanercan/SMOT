#!/usr/bin/env python3
"""
Profile Scraper v2.0 - Twitter Profil Bilgileri (Detaylı)
- Takipçi/takip sayısı
- Tweet sayısı
- Bio (biyografi)
- Location (konum)
- Website
- Verified (mavi tik)
- Join date (katılma tarihi)
"""

import time
import random
import re
from datetime import datetime
from typing import Dict, List, Optional
from app.utils.logger import get_logger
from app.utils.retry_config import retry_on_scraping_error

logger = get_logger("ProfileScraper")

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
    """Twitter profil bilgilerini toplayan scraper v2.0"""

    def __init__(self, driver=None, headless=False, require_manual_login=True):
        """
        Args:
            driver: Mevcut selenium driver (x_scraper'dan paylaşılabilir)
            headless: Kendi driver oluşturulacaksa headless mod
            require_manual_login: Manuel login bekle
        """
        self.driver = driver
        self.own_driver = False
        self.logged_in = False
        self.require_manual_login = require_manual_login

        if self.driver is None:
            self._init_driver(headless)
            self.own_driver = True
            if require_manual_login:
                self._manual_login_wait()

    def _init_driver(self, headless: bool):
        """Initialize Chrome driver"""
        if not SELENIUM_AVAILABLE or not UNDETECTED_AVAILABLE:
            raise Exception("Selenium veya undetected-chromedriver yüklü değil")

        import platform
        options = uc.ChromeOptions()

        if platform.system() == "Windows":
            options.binary_location = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"

        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

        self.driver = uc.Chrome(options=options, headless=False, version_main=146)
        logger.info("Browser hazır")

    def _manual_login_wait(self):
        """Wait for user to manually login to X.com"""
        try:
            logger.info("=" * 70)
            logger.info("MANUEL LOGIN GEREKLİ")
            logger.info("=" * 70)

            self.driver.get("https://x.com/login")
            time.sleep(2)

            logger.info("Lütfen açılan browser'da X/Twitter'a giriş yapın...")
            logger.info("Sistem 120 saniye bekleyecek...")

            for i in range(120):
                current_url = self.driver.current_url
                if "x.com/login" not in current_url and "x.com/i/flow" not in current_url:
                    self.logged_in = True
                    logger.info("LOGIN BAŞARILI!")
                    return True

                try:
                    self.driver.find_element(By.XPATH, "//nav[@aria-label='Primary navigation']")
                    self.logged_in = True
                    logger.info("LOGIN BAŞARILI!")
                    return True
                except Exception:
                    pass

                if i % 10 == 0 and i > 0:
                    logger.info(f"Bekleniyor... {i}s geçti")

                time.sleep(1)

            logger.warning("120 saniye doldu, login algılanamadı")
            self.logged_in = False
            return False

        except Exception as e:
            logger.error(f"Login hatası: {e}")
            self.logged_in = False
            return False

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
        Tek bir kullanıcının TÜM profil bilgilerini çek

        Returns:
            {
                'username': str,
                'display_name': str,
                'bio': str,
                'location': str,
                'website': str,
                'join_date': str,
                'verified': bool,
                'followers': int,
                'following': int,
                'tweets': int,
                'profile_image_url': str,
                'scrape_date': str (YYYY-MM-DD)
            }
        """
        if not self.driver:
            logger.error("Driver yok")
            return None

        url = f"https://x.com/{username}"

        try:
            self.driver.get(url)
            time.sleep(random.uniform(2, 4))

            # Profil mevcut mu kontrol et
            try:
                self.driver.find_element(
                    By.XPATH,
                    "//span[contains(text(), 'does not exist') or contains(text(), 'mevcut de') or contains(text(), 'Account suspended')]"
                )
                logger.warning(f"@{username}: Profil bulunamadı veya askıya alınmış")
                return None
            except NoSuchElementException:
                pass  # Profile exists

            # Profil yüklenmesini bekle
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@data-testid='UserName']"))
                )
            except TimeoutException:
                logger.warning(f"Timeout: @{username}")
                pass

            result = {
                'username': username,
                'display_name': '',
                'bio': '',
                'location': '',
                'website': '',
                'join_date': '',
                'verified': False,
                'followers': 0,
                'following': 0,
                'tweets': 0,
                'profile_image_url': '',
                'scrape_date': datetime.now().strftime("%Y-%m-%d")
            }

            # ==========================================
            # DISPLAY NAME
            # ==========================================
            try:
                name_elem = self.driver.find_element(
                    By.XPATH,
                    "//div[@data-testid='UserName']//span[not(contains(text(), '@'))]"
                )
                result['display_name'] = name_elem.text.strip()
            except NoSuchElementException:
                pass

            # ==========================================
            # VERIFIED (Mavi Tik)
            # ==========================================
            try:
                self.driver.find_element(
                    By.XPATH,
                    "//div[@data-testid='UserName']//*[contains(@aria-label, 'Verified') or contains(@aria-label, 'verified') or @data-testid='icon-verified']"
                )
                result['verified'] = True
            except NoSuchElementException:
                result['verified'] = False

            # ==========================================
            # BIO (Biyografi)
            # ==========================================
            try:
                bio_elem = self.driver.find_element(
                    By.XPATH,
                    "//div[@data-testid='UserDescription']"
                )
                result['bio'] = bio_elem.text.strip()
            except NoSuchElementException:
                pass

            # ==========================================
            # LOCATION
            # ==========================================
            try:
                location_elem = self.driver.find_element(
                    By.XPATH,
                    "//span[@data-testid='UserLocation']"
                )
                result['location'] = location_elem.text.strip()
            except NoSuchElementException:
                pass

            # ==========================================
            # WEBSITE / URL
            # ==========================================
            try:
                url_elem = self.driver.find_element(
                    By.XPATH,
                    "//a[@data-testid='UserUrl']"
                )
                result['website'] = url_elem.get_attribute("href") or url_elem.text.strip()
            except NoSuchElementException:
                pass

            # ==========================================
            # JOIN DATE (Katılma Tarihi)
            # ==========================================
            try:
                join_elem = self.driver.find_element(
                    By.XPATH,
                    "//span[@data-testid='UserJoinDate']"
                )
                result['join_date'] = join_elem.text.strip()
            except NoSuchElementException:
                pass

            # ==========================================
            # PROFILE IMAGE URL
            # ==========================================
            try:
                img_elem = self.driver.find_element(
                    By.XPATH,
                    "//div[@data-testid='UserAvatar-Container-unknown']//img | //a[contains(@href, '/photo')]//img"
                )
                result['profile_image_url'] = img_elem.get_attribute("src") or ""
            except NoSuchElementException:
                pass

            # ==========================================
            # FOLLOWERS COUNT
            # ==========================================
            try:
                followers_link = self.driver.find_element(
                    By.XPATH,
                    f"//a[@href='/{username}/verified_followers' or @href='/{username}/followers']"
                )
                followers_text = followers_link.text
                result['followers'] = self._parse_count(followers_text.split()[0])
            except NoSuchElementException:
                try:
                    followers_elem = self.driver.find_element(
                        By.XPATH,
                        "//span[contains(text(), 'Followers') or contains(text(), 'Takipçi')]/.."
                    )
                    text = followers_elem.text
                    match = re.search(r'([\d.,KMB]+)\s*(Followers|Takipçi)', text, re.IGNORECASE)
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
                posts_elem = self.driver.find_element(
                    By.XPATH,
                    "//div[@data-testid='UserName']/following::div[contains(text(), 'post') or contains(text(), 'gönderi')]"
                )
                posts_text = posts_elem.text
                result['tweets'] = self._parse_count(posts_text.split()[0])
            except NoSuchElementException:
                try:
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

            logger.info(f"@{username}: {result['followers']:,} takipçi | Bio: {len(result['bio'])} karakter")
            return result

        except Exception as e:
            logger.error(f"@{username}: Hata - {str(e)[:50]}")
            return None

    def scrape_profiles(self, usernames: List[str]) -> List[Dict]:
        """
        Birden fazla kullanıcının profil bilgilerini çek
        """
        logger.info(f"PROFIL SCRAPER v2.0 - Kullanıcı sayısı: {len(usernames)}")

        results = []

        for i, username in enumerate(usernames, 1):
            logger.info(f"[{i}/{len(usernames)}] @{username}")

            profile = self.scrape_profile(username)

            if profile:
                results.append(profile)
            else:
                logger.warning(f"@{username} alınamadı")

            # Rate limiting
            if i < len(usernames):
                time.sleep(random.uniform(2, 4))

        logger.info(f"Tamamlandı: {len(results)}/{len(usernames)} profil")
        return results

    def scrape_and_save(self, usernames: List[str]) -> int:
        """
        Profilleri çek ve database'e kaydet
        """
        from app.core.database import save_profile_snapshot, update_councilor_profile

        profiles = self.scrape_profiles(usernames)
        saved = 0

        for p in profiles:
            # ProfileHistory'ye sayısal metrikleri kaydet
            save_profile_snapshot(
                username=p['username'],
                followers_count=p['followers'],
                following_count=p['following'],
                tweet_count=p['tweets'],
                listed_count=0,
                scrape_date=p['scrape_date']
            )

            # Councilor tablosuna detaylı bilgileri kaydet
            success = update_councilor_profile(
                username=p['username'],
                bio=p['bio'],
                location=p['location'],
                website=p['website'],
                verified=p['verified'],
                profile_image_url=p['profile_image_url'],
                join_date=p['join_date']
            )

            if success:
                saved += 1

        logger.info(f"Database'e kaydedildi: {saved} profil")
        return saved

    def close(self):
        """Driver'ı kapat (sadece kendi oluşturduysa)"""
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
# HAFTALIK KARŞILAŞTIRMA FONKSİYONLARI
# ============================================================================

def get_weekly_comparison(username: str) -> Optional[Dict]:
    """Son 7 günlük profil değişimini getir"""
    from app.core.database import get_all_profile_history
    from datetime import datetime, timedelta

    history = get_all_profile_history(username)

    if len(history) < 2:
        return None

    latest = history[-1]
    target_date = datetime.strptime(latest['date'], "%Y-%m-%d") - timedelta(days=7)

    closest = None
    min_diff = float('inf')

    for h in history[:-1]:
        h_date = datetime.strptime(h['date'], "%Y-%m-%d")
        diff = abs((h_date - target_date).days)
        if diff < min_diff:
            min_diff = diff
            closest = h

    if not closest:
        closest = history[0]

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
    """Tüm kullanıcılar için haftalık karşılaştırma"""
    results = []
    for username in usernames:
        comparison = get_weekly_comparison(username)
        if comparison:
            results.append(comparison)
    return results


def print_weekly_report(usernames: List[str]):
    """Haftalık değişim raporu yazdır"""
    comparisons = get_all_weekly_comparisons(usernames)

    if not comparisons:
        logger.warning("Karşılaştırma için yeterli veri yok")
        return

    print(f"\n{'='*80}")
    print("HAFTALIK PROFIL DEGISIM RAPORU")
    print(f"{'='*80}")
    print(f"{'Kullanıcı':<20} {'Takipçi':<15} {'Değişim':<12} {'Takip':<10} {'Tweet':<10}")
    print(f"{'-'*80}")

    for c in comparisons:
        followers_change = c['followers_change']
        change_str = f"+{followers_change}" if followers_change >= 0 else str(followers_change)

        print(f"@{c['username']:<19} {c['followers_end']:>10,} {change_str:>12} "
              f"{c['following_change']:>+10} {c['tweets_change']:>+10}")

    print(f"{'='*80}")
    print(f"Dönem: {comparisons[0]['period_start']} - {comparisons[0]['period_end']}")
    print(f"{'='*80}\n")


# ============================================================================
# CLI / TEST
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Twitter Profil Scraper v2.0")
    parser.add_argument("--users", nargs="+", help="Kullanıcı adları")
    parser.add_argument("--save", action="store_true", help="Database'e kaydet")
    parser.add_argument("--compare", action="store_true", help="Haftalık karşılaştırma göster")

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
                    print(f"\n@{r['username']}:")
                    print(f"  Ad: {r['display_name']}")
                    print(f"  Bio: {r['bio'][:100]}..." if len(r['bio']) > 100 else f"  Bio: {r['bio']}")
                    print(f"  Konum: {r['location']}")
                    print(f"  Website: {r['website']}")
                    print(f"  Katılım: {r['join_date']}")
                    print(f"  Verified: {r['verified']}")
                    print(f"  Takipçi: {r['followers']:,}")
                    print(f"  Takip: {r['following']:,}")
                    print(f"  Tweet: {r['tweets']:,}")
    else:
        print("Kullanım:")
        print("  python profile_scraper.py --users user1 user2 --save")
        print("  python profile_scraper.py --users user1 user2 --compare")
