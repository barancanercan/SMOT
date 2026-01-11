# Meclis Istihbarat Sistemi

**v2.1** - Ankara Buyuksehir Belediyesi meclis uyelerinin X/Twitter aktivitesini toplayan, analiz eden ve raporlayan sistem.

---

## Ozellikler

### Veri Toplama
- **86 Meclis Uyesi:** Ankara BB meclis uyelerinin Twitter hesaplari
- **Akilli Scraping:** Session crash durumunda otomatik devam (`--resume`)
- **Profil Takibi:** Takipci sayisi degisim gecmisi

### Analiz
- **LLM Analizi:** Ollama + qwen2.5:7b ile profesyonel icerik analizi
- **Tematik Analiz:** Ana konular ve iletisim stratejisi
- **Siyasi Pozisyon:** Parti/lider destegi tespiti
- **Elestiri Analizi:** Muhalefete yonelik tutum
- **Vector Database:** ChromaDB ile semantic search

### Dashboard
- **Takipci Siralamasi:** Parti bazli takipci karsilastirmasi
- **Parti Analizi:** CHP vs AKP vs Diger istatistikleri
- **Engagement Metrikleri:** Like, RT, Reply, View analizi
- **Ilce Bazli Analiz:** Coklu ilce temsili gorsellestirme
- **Interaktif Grafikler:** Plotly ile zengin gorseller

### Raporlama
- **Tek/Toplu Rapor:** Markdown formatinda detayli raporlar
- **Parti Filtreleme:** CHP, AKP, Diger hizli secim
- **Excel Export:** Engagement ve takipci verileri
- **PDF Export:** Rapor ciktisi

---

## Hizli Baslangic

### 1. Kurulum

```bash
git clone https://github.com/barancanercan/MeclisIstihbaratSistemi.git
cd MeclisIstihbaratSistemi
python3.10 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Ollama Kurulumu (LLM Analizi icin)

```bash
# Ollama indir: https://ollama.com/download
ollama pull qwen2.5:7b
ollama serve
```

### 3. Web Arayuzu

```bash
streamlit run ui/streamlit_app.py
```

Tarayicida http://localhost:8501 adresine gidin.

---

## Ekran Goruntuleri

### Dashboard
- Takipci siralamasi (parti renkli)
- Parti bazli toplam takipci pasta grafigi
- Engagement analizi bar chart
- Ilce temsil dagilimi

### Raporlar
- Profil bilgileri ve metrikler
- En cok etkilesim alan tweetler (tam metin)
- LLM destekli siyasi analiz

---

## Sistem Mimarisi

```
data/total_data.csv (147 Meclis Uyesi - 86 X hesabi)
        |
        v
[Tweet Scraping]
    x_scraper.py (Selenium + Undetected Chrome)
    run_full_scrape.py (Batch scraping)
        |
        v
[SQLite Database] meclis.db
    - councilors (kullanici bilgileri + parti)
    - tweets (12,480+ tweet)
    - profile_history (takipci gecmisi)
    - report_cache (rapor onbellegi)
        |
        v
[Analysis Layer]
    - Vector DB (ChromaDB + embeddings)
    - LLM (Ollama + qwen2.5:7b)
    - Profesyonel Turkce promptlar
        |
        v
[Reporting]
    - Metrik hesaplama
    - Engagement analizi
    - Parti bazli LLM analizi
        |
        v
[Web UI - Streamlit]
    - Dashboard (4 tab: Takipci, Parti, Engagement, Ilce)
    - Raporlar (Tek + Toplu)
    - En Iyi Tweetler
```

---

## Proje Yapisi

```
MeclisIstihbaratSistemi/
|
|-- config.py                # Konfigurasyon
|-- database.py              # SQLite islemleri
|-- x_scraper.py             # Tweet scraper
|-- run_full_scrape.py       # Toplu veri toplama
|
|-- analysis/
|   |-- analyzer.py          # LLM analizi (HTTP API)
|   |-- embeddings.py        # Vector embedding
|   |-- vector_db.py         # ChromaDB
|   |-- prompts.py           # Profesyonel prompt sablonlari
|
|-- reporting/
|   |-- report_generator.py  # Rapor olusturma + PDF/Excel export
|   |-- metrics.py           # Metrik hesaplama
|
|-- ui/
|   |-- streamlit_app.py     # Streamlit UI (ana arayuz)
|   |-- app.py               # Gradio UI (alternatif)
|
|-- scraping/
|   |-- profile_scraper.py   # Profil bilgileri
|
|-- data/
|   |-- total_data.csv       # Meclis uyeleri listesi (147)
|   |-- meclis.db            # Veritabani
|
|-- docs/
|   |-- ROADMAP.md           # Gelistirme plani
|
|-- requirements.txt
|-- .env                     # X credentials
```

---

## Mevcut Durum (v2.1)

| Metrik | Deger |
|--------|-------|
| Toplam Meclis Uyesi | 147 |
| X Hesabi Olan | 86 |
| Toplam Tweet | 12,480+ |
| Parti Dagilimi | CHP: 46, AKP: 32, Diger: 8 |

---

## Teknik Stack

| Katman | Arac | Aciklama |
|--------|------|----------|
| Scraping | Selenium + undetected-chromedriver | Bot detection bypass |
| Database | SQLite | Lightweight, local |
| Vector DB | ChromaDB | Semantic search |
| Embedding | sentence-transformers | all-MiniLM-L6-v2 |
| LLM | Ollama + qwen2.5:7b | Turkce destekli, HTTP API |
| UI | Streamlit + Plotly | Interaktif dashboard |
| Export | openpyxl + fpdf2 | Excel ve PDF cikti |

---

## Gereksinimler

- Python 3.10+
- Chrome/Chromium browser
- 8GB+ RAM (16GB onerilen)
- Ollama (LLM analizi icin)
- NVIDIA GPU (opsiyonel, hizli inference)

---

## Lisans

MIT License

---

## Iletisim

**Gelistirici:** Baran Can Ercan
**GitHub:** https://github.com/barancanercan/MeclisIstihbaratSistemi
