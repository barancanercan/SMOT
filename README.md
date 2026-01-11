# Meclis Istihbarat Sistemi

**v2.0** - Ankara Buyuksehir Belediyesi meclis uyelerinin X/Twitter aktivitesini toplayan, analiz eden ve raporlayan sistem.

---

## Ozellikler

- **Tweet Toplama:** 86 meclis uyesi, son 3 aylik tweetler
- **Akilli Scraping:** Session crash durumunda otomatik devam (`--resume`)
- **LLM Analizi:** Ollama + qwen2.5 ile icerik analizi
- **Vector Database:** ChromaDB ile semantic search
- **Raporlama:** Tek/toplu kullanici raporlari, Markdown export
- **Web UI:** Streamlit tabanli kullanici dostu arayuz

---

## Hizli Baslangic

### 1. Kurulum

```bash
git clone https://github.com/barancanercan/MeclisIstihbaratSistemi.git
cd MeclisIstihbaratSistemi
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Veritabani Olustur

```bash
python database.py
```

### 3. Tweet Toplama

```bash
# Tum kullanicilar (ilk calistirma)
python run_full_scrape.py

# Eksik/basarisiz kullanicilari tamamla
python run_full_scrape.py --resume

# Belirli indexten devam et
python run_full_scrape.py --start 31
```

### 4. Web Arayuzu

```bash
# Streamlit (onerilen)
streamlit run ui/streamlit_app.py

# Gradio (alternatif)
python ui/app.py
```

---

## Sistem Mimarisi

```
data/data.csv (86 Meclis Uyesi)
        |
        v
[Tweet Scraping]
    x_scraper.py (Selenium + Undetected Chrome)
    run_full_scrape.py (Batch scraping)
        |
        v
[SQLite Database] meclis.db
    - councilors (kullanici bilgileri)
    - tweets (12,480+ tweet)
    - profile_history (takipci gecmisi)
    - report_cache (rapor onbellegi)
        |
        v
[Analysis Layer]
    - Vector DB (ChromaDB + embeddings)
    - LLM (Ollama + qwen2.5:7b)
        |
        v
[Reporting]
    - Metrik hesaplama
    - Engagement analizi
    - LLM destekli icerik analizi
        |
        v
[Web UI]
    - Streamlit (sade, hizli)
    - Dashboard, Raporlar, En Iyi Tweetler
```

---

## Proje Yapisi

```
MeclisIstihbaratSistemi/
|
|-- config.py                # Konfigurason
|-- database.py              # SQLite islemleri
|-- x_scraper.py             # Tweet scraper
|-- run_full_scrape.py       # Toplu veri toplama
|
|-- analysis/
|   |-- analyzer.py          # LLM analizi
|   |-- embeddings.py        # Vector embedding
|   |-- vector_db.py         # ChromaDB
|   |-- prompts.py           # LLM prompt sablonlari
|
|-- reporting/
|   |-- report_generator.py  # Rapor olusturma
|   |-- metrics.py           # Metrik hesaplama
|
|-- ui/
|   |-- streamlit_app.py     # Streamlit UI (onerilen)
|   |-- app.py               # Gradio UI (alternatif)
|
|-- scraping/
|   |-- profile_scraper.py   # Profil bilgileri
|
|-- workers/
|   |-- update_worker.py     # Haftalik guncelleme
|
|-- data/
|   |-- data.csv             # Meclis uyeleri listesi
|
|-- docs/
|   |-- ROADMAP.md           # Gelistirme plani
|
|-- meclis.db                # Veritabani
|-- requirements.txt
|-- .env                     # X credentials
```

---

## Mevcut Durum (v2.0)

| Metrik | Deger |
|--------|-------|
| Toplam Tweet | 12,480 |
| Orijinal Tweet | 3,764 |
| Retweet | 8,716 |
| Aktif Kullanici | 85/86 |

---

## Komut Referansi

### Veri Toplama

```bash
# Tum kullanicilar
python run_full_scrape.py

# Sadece basarisiz/eksik olanlar
python run_full_scrape.py --resume

# Belirli indexten basla
python run_full_scrape.py --start 31
```

### Raporlama

```bash
# Tek kullanici raporu (hizli)
python reporting/report_generator.py --user username --no-llm

# Tek kullanici raporu (LLM ile)
python reporting/report_generator.py --user username

# Toplu rapor
python reporting/report_generator.py --users user1 user2 user3

# Cache temizle
python reporting/report_generator.py --clear-cache
```

### Metrikler

```bash
# Etkilesim siralamasi
python reporting/metrics.py --users user1 user2 --ranking

# En iyi tweetler
python reporting/metrics.py --users user1 --top 10
```

### Web UI

```bash
# Streamlit (port 8501)
streamlit run ui/streamlit_app.py

# Gradio (port 7860)
python ui/app.py
```

---

## Teknik Stack

| Katman | Arac | Aciklama |
|--------|------|----------|
| Scraping | Selenium + undetected-chromedriver | Bot detection bypass |
| Database | SQLite | Lightweight, local |
| Vector DB | ChromaDB | Semantic search |
| Embedding | sentence-transformers | all-MiniLM-L6-v2 |
| LLM | Ollama + qwen2.5:7b | Turkce destekli |
| UI | Streamlit | Hizli, kullanici dostu |

---

## Gereksinimler

- Python 3.10+
- Chrome/Chromium browser
- 16GB+ RAM (LLM icin onerilen)
- Ollama (LLM analizi icin)

---

## Lisans

MIT License

---

## Iletisim

**Gelistirici:** Baran Can Ercan
**GitHub:** https://github.com/barancanercan/MeclisIstihbaratSistemi
