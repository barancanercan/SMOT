# 🏛️ Meclis İstihbarat Sistemi

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Built with Qwen2.5](https://img.shields.io/badge/LLM-Qwen2.5--7B-red.svg)](https://huggingface.co/Qwen/Qwen2.5-7B)
[![Database v2.0](https://img.shields.io/badge/Database-SQLite%20v2.0-blue.svg)](https://www.sqlite.org/)

**Ankara Belediyesi meclis üyelerinin X/Twitter aktivitesini otomatik olarak toplarıp Qwen2.5-7B LLM ile analiz eden, tamamen açık kaynak ve lokal çalışan yapay zeka sistemi.**

---

## 📊 Sistem Akışı
```
CSV → Parse → Scrape → Database v2.0 → LLM Analysis → Report
```

---

## 🎯 Özellikler

✅ **Otomatik Tweet Scraping** - Selenium + Undetected Chrome ile gerçek X/Twitter'dan veri çekme  
✅ **Rich Metadata** - Beğeni, yorum, retweet, tarih, RT kaynağı takibi  
✅ **LLM Analysis** - Qwen2.5-7B ile Türkçe siyaset analizi  
✅ **Database v2.0** - Foreign keys, indexes, constraints, transaction support  
✅ **Lokal & Güvenli** - Cloud API yok, hiçbir veri dışarı çıkmıyor  
✅ **Clean Architecture** - Modüler yapı (config, models, src)  
✅ **Gradio Web UI** - Kullanışlı arayüz (66 satır kod)  
✅ **CSV Export** - Tüm tweetler tablo formatında  

---

## 🏗️ Proje Mimarisi
```
MeclisIstihbaratSistemi/
├── 📄 config.py              # Tüm constants
├── 🎨 meclis_app.py          # Gradio UI (66 satır)
├── 📦 models/
│   ├── __init__.py
│   └── database.py           # v2.0 Schema
├── 🔧 src/
│   ├── __init__.py
│   ├── analyzer.py           # LLM Analysis
│   ├── csv_parser.py         # CSV Processing
│   └── pipeline.py           # Main Orchestration
├── 🐦 x_scraper.py           # X/Twitter Scraper
├── 📊 view_tweets.py         # Data Export
├── 🛠️ tools/
│   ├── db_setup.py
│   └── test_scraper.py
├── .env                      # Credentials
├── requirements.txt
└── meclis.db                 # SQLite v2.0
```

---

## 🚀 Kurulum (5 Adım)

### 1. Ön Gereksinimler
```bash
sudo apt-get install -y python3.10 python3.10-venv chromium-browser
curl -fsSL https://ollama.com/install.sh | sh
```

### 2. Klonla & Setup
```bash
git clone https://github.com/barancan/MeclisIstihbaratSistemi.git
cd MeclisIstihbaratSistemi
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Ollama Model
```bash
# Terminal 1:
OLLAMA_NUM_THREADS=6 ollama serve

# Terminal 2:
ollama pull qwen2.5:7b-instruct-q4_K_M
```

### 4. Credentials (.env)
```bash
cat > .env << 'EOF'
X_USERNAME=your_x_username
X_PASSWORD=your_x_password
