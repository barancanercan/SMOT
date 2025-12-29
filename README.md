# 🏛️ Meclis İstihbarat Sistemi

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Built with Qwen2.5](https://img.shields.io/badge/LLM-Qwen2.5-7B-red.svg)](https://huggingface.co/Qwen/Qwen2.5-7B)

**Ankara Belediyesi meclis üyelerinin X/Twitter aktivitesini otomatik olarak toplarıp Qwen2.5-7B LLM ile analiz eden, tamamen açık kaynak ve lokal çalışan yapay zeka sistemi.**

---

## 📊 Sistem Akışı

```
CSV → Parse → Scrape → Database → LLM → Report
```

---

## 🎯 Özellikler

✅ **Otomatik Tweet Scraping** - Selenium ile gerçek X/Twitter'dan veri çekme  
✅ **Engagement Metrics** - Beğeni, yorum, retweet sayısı  
✅ **Retweet Tracking** - RT kaynak ve içerik ayrımı  
✅ **LLM Analysis** - Qwen2.5-7B ile Türkçe siyaset analizi  
✅ **Lokal & Güvenli** - Cloud API yok, hiçbir veri dışarı çıkmıyor  
✅ **Gradio Web UI** - Kullanışlı arayüz  
✅ **CSV Export** - Tüm tweetler tablo formatında  

---

## 🚀 Kurulum (5 adım)

### 1. Ön Gereksinimler
```bash
sudo apt-get install -y python3.10 python3.10-venv chromium-browser
curl -fsSL https://ollama.com/install.sh | sh
```

### 2. Klonla
```bash
git clone https://github.com/barancan/MeclisIstihbaratSistemi.git
cd MeclisIstihbaratSistemi
```

### 3. Virtual Env
```bash
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Ollama Model
```bash
# Terminal 1:
OLLAMA_NUM_THREADS=6 ollama serve

# Terminal 2:
ollama pull qwen2.5:7b-instruct-q4_K_M
```

### 5. Çalıştır
```bash
python meclis_app.py
# http://127.0.0.1:7860 otomatik açılacak
```

---

## 📝 Kullanım

1. CSV dosyası hazırla (username veya link sütunu)
2. Gradio UI'de dosyayı yükle
3. "BAŞLAT: Scrape & Analyze" tıkla
4. Raporunuzu HTML olarak alın

---

## 📁 Dosya Yapısı

```
├── meclis_app.py          # Ana uygulama
├── x_scraper.py           # X scraper
├── view_tweets.py         # CSV export
├── requirements.txt       # Dependencies
├── README.md             # Bu dosya
├── councilors_example.csv # Örnek data
└── tools/                # Dev tools
    ├── db_setup.py
    ├── test_scraper.py
    └── ...
```

---

## 💻 Gereksinimler

| Özellik | Gereksinim |
|---------|-----------|
| OS | Ubuntu 20.04+ |
| Python | 3.10+ |
| RAM | 8GB+ |
| Disk | 15GB+ |

---

## 🔒 Gizlilik

✅ Tamamen lokal  
✅ Cloud API yok  
✅ Açık kaynak (MIT)  
✅ Audit edilebilir  

---

## 🐛 Sorun Giderme

```bash
# Ollama bağlantı hatası
OLLAMA_NUM_THREADS=6 ollama serve

# Module hatası
pip install -r requirements.txt

# Chrome yok
sudo apt-get install chromium-browser
```

---

## 📧 İletişim

**Geliştirici:** Baran Can  
**Kurum:** Ankara Metropolitan Municipality

---

## 📄 Lisans

MIT License - Detaylar için LICENSE dosyasına bakın

---

**Made with ❤️ for Ankara**  
*"Teknoloji halkın hizmetinde olmalı"*