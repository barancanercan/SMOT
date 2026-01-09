# Meclis Istihbarat Sistemi

**v1.0** - Ankara Belediyesi meclis uyelerinin X/Twitter aktivitesini toplayan veri kazima sistemi.

---

## Sistem Akisi

```
CSV (Meclis Uyeleri)
    |
X/Twitter Scraping (Selenium + Undetected Chrome)
    |-- Tweet Text
    |-- Timestamp
    |-- Engagement (likes, replies, retweets, views)
    |-- RT Detection
    |-- Date Filtering (90 gun)
    |
SQLite Database
    |-- Deduplication
    |-- Councilor metadata
    |
CSV Export
```

---

## Proje Yapisi

```
MeclisIstihbaratSistemi/
|
|-- config.py           # Merkezi konfigurason
|-- database.py         # SQLite islemleri
|-- x_scraper.py        # XTwitterScraper sinifi
|-- scraper_worker.py   # Ana veri toplama scripti
|-- export_to_csv.py    # CSV export
|
|-- data/
|   |-- data.csv        # Meclis uyeleri listesi
|
|-- meclis.db           # SQLite veritabani
|-- requirements.txt
|-- .env                # X credentials
```

---

## Kurulum

### 1. Gereksinimler
```bash
sudo apt-get install -y python3.10 chromium-browser
```

### 2. Proje Setup
```bash
git clone https://github.com/barancanercan/MeclisIstihbaratSistemi.git
cd MeclisIstihbaratSistemi
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Veritabani Olustur
```bash
python database.py
```

---

## Kullanim

### Veri Toplama
```bash
python scraper_worker.py
```
- Browser acilir, manuel X login gerekir
- 120 saniye login suresi
- Tum kullanicilar icin tweet toplanir

### CSV Export
```bash
python export_to_csv.py
```
Cikti dosyalari:
- `tweets_export_v3_2.csv` - Tum tweetler
- `tweets_statistics_v3_2.csv` - Kullanici istatistikleri
- `rt_analysis_v3_2.csv` - RT analizi

---

## Konfigurason

`config.py`:
```python
DB_PATH = "meclis.db"
CSV_PATH = "data/data.csv"
MAX_TWEETS_PER_USER = 500
DAYS_BACK = 90
```

---

## Veritabani Semasi

**councilors**
- username, name, party, district

**tweets**
- username, tweet_text, tweet_date
- is_retweet, retweet_from
- likes, replies, retweets, views

---

## Teknik Stack

| Katman | Arac |
|--------|------|
| Dil | Python 3.10+ |
| Scraper | Selenium |
| Bot Bypass | undetected-chromedriver |
| Database | SQLite3 |

---

## Lisans

MIT License

---

## Iletisim

**Gelistirici:** Baran Can Ercan
**GitHub:** https://github.com/barancanercan/MeclisIstihbaratSistemi