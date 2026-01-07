#!/usr/bin/env python3
"""Extract cookies - shorter timeout"""

import json
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pickle

def manual_login_and_export_cookies():
    """Manual login -> extract cookies"""
    print("\n" + "=" * 70)
    print("🍪 MANUAL LOGIN & COOKIE EXPORT")
    print("=" * 70)
    print("\n⚠️  INSTRUCTIONS:")
    print("1. Browser açılacak")
    print("2. X.com/login'de MANUAL giriş yap")
    print("3. Giriş yaptıktan 10 saniye sonra otomatik kapatılacak\n")
    
    input("Enter'e bas başlamak için...")
    
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = uc.Chrome(options=options)
    
    try:
        print("📱 X.com/login açılıyor...")
        driver.get("https://x.com/login")
        time.sleep(2)
        
        # SHORTER WAIT - 60 saniye max
        print("⏳ Home feed'i bekliyor (sen giriş yap)... (60 saniye)\n")
        
        try:
            WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.XPATH, "//nav[@aria-label='Primary navigation']"))
            )
            print("✅ Home feed detected!\n")
        except:
            print("⏳ Home feed bulunamadı ama cookies'i kaydetmeye devam ediyorum...\n")
        
        # Wait 5 more seconds for any remaining assets
        time.sleep(5)
        
        # Extract cookies
        print("🍪 Cookies kaydediliyor...")
        cookies = driver.get_cookies()
        
        # Save pickle
        with open('x_cookies.pkl', 'wb') as f:
            pickle.dump(cookies, f)
        
        print(f"✅ {len(cookies)} cookies saved to x_cookies.pkl\n")
        
        # Save JSON
        cookies_json = {c['name']: c['value'] for c in cookies}
        with open('x_cookies.json', 'w') as f:
            json.dump(cookies_json, f, indent=2)
        
        print("✅ Also saved as x_cookies.json")
        print("\n🚀 Now run: python3 scraper_worker_v5.py\n")
        
        return True
        
    finally:
        driver.quit()

if __name__ == "__main__":
    manual_login_and_export_cookies()

