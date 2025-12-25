# 🏛️ Meclis İstihbarat Sistemi

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Built with Qwen2.5](https://img.shields.io/badge/LLM-Qwen2.5-7B-red.svg)](https://huggingface.co/Qwen/Qwen2.5-7B)

**Ankara Belediyesi meclis üyelerinin X/Twitter aktivitesini otomatik olarak toplarıp Qwen2.5-7B LLM ile analiz eden, tamamen açık kaynak ve lokal çalışan yapay zeka sistemi.**

---

## 📊 Sistem Akışı

```
CSV Yükleme
    ↓
CSV Parse (username/link)
    ↓
Selenium ile X Scraping (Gerçek Tweets)
    ↓
SQLite Database (Lokal Storage)
    ↓
Qwen2.5-7B LLM Analysis (3 Soru)
    ↓
Markdown Report (HTML Preview)
```

---

## 🎯 Özellikler

✅ **Otomatik Tweet Scraping** - Selenium ile gerçek X/Twitter'dan veri çekme  
✅ **Akıllı CSV Parsing** - `username` veya `link` sütunlarını otomatik algılama  
✅ **LLM-Powered Analysis** - Qwen2.5-7B ile Türkçe analiz  
✅ **Advanced Prompting** - Chain-of-thought, evidence-based cevaplar  
✅ **Lokal & Gizli** - Cloud API yok, hiçbir veri dışarı çıkmıyor  
✅ **Terminal Progress** - Her adımı real-time izleme  
✅ **Web UI** - Gradio ile güzel arayüz  
✅ **SQLite Persistence** - Hızlı lokal depolama  

---

## 🚀 Kurulum

### 1️⃣ Ön Gereksinimler

```bash
# Ubuntu/Debian
sudo apt-get install -y python3.10 python3.10-venv git chromium-browser

# Ollama (https://ollama.com)
curl -fsSL https://ollama.com/install.sh | sh
```

### 2️⃣ Repository Klonla

```bash
git clone https://github.com/YOUR_USERNAME/MeclisIstihbaratSistemi.git
cd MeclisIstihbaratSistemi
```

### 3️⃣ Virtual Environment Kur

```bash
python3.10 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install selenium webdriver-manager --break-system-packages
```

### 4️⃣ Ollama Setup (Ayrı Terminal)

```bash
# Terminal 1: Ollama daemon başlat
OLLAMA_NUM_THREADS=6 ollama serve

# Terminal 2: Model çek
ollama pull qwen2.5:7b-instruct-q4_K_M
```

### 5️⃣ Uygulamayı Çalıştır

```bash
# Orijinal terminalinizde
cd /path/to/MeclisIstihbaratSistemi
source .venv/bin/activate
python meclis_app.py
```

**Browser otomatik açılacak:** http://127.0.0.1:7860

---

## 📝 Kullanım

### CSV Format

**Seçenek 1: Username Sütunu**
```csv
username,name,party,district
abbas_atamer,Abbas ATAMER,CHP,Keçiören
atila_celik06,Atila ÇELİK,CHP,Keçiören
avmertdemirel,Abdulkadim Mert DEMİREL,AKP,Keçiören
```

**Seçenek 2: Link Sütunu (Otomatik Parse)**
```csv
Meclis Üyesi,İlçe,link,Parti
Abbas ATAMER,Keçiören,https://x.com/abbas_atamer,CHP
Atila ÇELİK,Keçiören,https://x.com/atila_celik06,CHP
```

### Analiz Süreci

1. **CSV Yükle** → Sistem üyeleri tespit eder
2. **Scrape & Analyze Başlat** → X'ten tweets çeker
3. **Otomatik Sorular** (Her üye için 3 soru):
   - Bu üyenin ana gündemleri neler?
   - Hangi konularda en çok tweet atıyor?
   - Son ayda ne hakkında konuşmaya başladı?
4. **Rapor Oluştur** → Markdown formatında HTML preview

---

## 💻 Sistem Gereksinimleri

| Özellik | Gereksinim | Baran'ın Sistemi |
|---------|-----------|------------------|
| **OS** | Ubuntu 20.04+ | ✅ Ubuntu 24.04 |
| **Python** | 3.10+ | ✅ 3.10 |
| **RAM** | 8GB+ | ✅ 16GB |
| **Disk** | 15GB+ | ✅ 200GB+ |
| **CPU** | Dual-core+ | ✅ i7-1165G7 |
| **İnternet** | Gerekli | ✅ Var |

### Performans Metrikleri

| Metrik | Değer |
|--------|-------|
| **Model** | Qwen2.5-7B-Instruct (Q4_K_M) |
| **Model Boyutu** | 4.7 GB |
| **RAM Kullanımı** | 7-7.5 GB |
| **Token Speed** | 8-12 tok/s |
| **Inference Süresi** | ~5-15 sn/soru |
| **13 Üye Analizi** | ~5-10 dakika |

---

## 📁 Dosya Yapısı

```
MeclisIstihbaratSistemi/
├── meclis_app.py           # 🎯 Ana uygulama
├── x_scraper.py            # 🐦 X/Twitter scraper
├── requirements.txt        # 📦 Dependencies
├── README.md              # 📖 Bu dosya
├── .gitignore             # 🚫 Git ignore
├── councilors_example.csv # 📊 Örnek veri
└── .venv/                 # 🐍 Virtual env
```

---

## 🏗️ Sistem Mimarisi

### Backend Stack
- **LLM:** Qwen2.5-7B-Instruct (Ollama)
- **Scraper:** Selenium + webdriver-manager
- **Database:** SQLite3
- **Prompt Engine:** Advanced chain-of-thought

### Frontend Stack
- **UI:** Gradio 6.2+
- **Output:** Markdown rendered as HTML

### Key Components

```python
# CSV → Usernames
parse_csv(csv_file) → List[str]

# Usernames → Tweets
XTwitterScraper.scrape_multiple(usernames) → Dict[str, List[str]]

# Tweets → Database
save_tweets(username, tweets) → None

# Database → Analysis
get_tweets(username) → List[str]
Analyzer.analyze(tweets, username, question) → str

# Analysis → Report
scrape_and_analyze(csv_file) → str (markdown)
```

---

## 🔒 Gizlilik & Güvenlik

✅ **Tamamen Lokal**
- Hiçbir veri cloud'a gönderilmez
- Ollama lokal inference
- SQLite lokal storage
- Selenium headless browsing

✅ **Açık Kaynak**
- Tüm kod MIT lisansıyla
- Audit edilebilir kod
- Bağımlılıklar şeffaf

✅ **Veri Koruma**
- X'ten sadece public tweetler çekiliyor
- Database şifreli olabilir (opsiyonel)
- Hiçbir kişisel veri işlenmiyor

---

## 🐛 Troubleshooting

| Sorun | Çözüm |
|-------|-------|
| `❌ Ollama connection failed` | `OLLAMA_NUM_THREADS=6 ollama serve` çalıştırıldığını kontrol et |
| `ModuleNotFoundError: selenium` | `pip install selenium webdriver-manager --break-system-packages` |
| `Chrome not found` | `sudo apt-get install chromium-browser` |
| `High memory usage` | `OLLAMA_NUM_THREADS=4` (daha düşük thread sayısı) |
| `Slow inference` | CPU tercih et, ekstra aplikasyonları kapat |

---

## 📚 Gelişmiş Kullanım

### Custom Questions
`scrape_and_analyze()` fonksiyonunda `QUESTIONS` listesini değiştir:

```python
QUESTIONS = [
    "Seçmen sözleşmelerini tuttu mu?",
    "En kritik konular neler?",
    "Sosyal medya üslubu nasıl?",
]
```

### Model Değiştirme
`meclis_app.py`'da `OLLAMA_MODEL` değiştir:

```python
# Hızlı (3B)
OLLAMA_MODEL = "qwen2.5:3b-instruct-q5_K_M"

# Ultra-hafif (1.5B)
OLLAMA_MODEL = "qwen2.5:1.5b-instruct-q8_0"

# Daha Güçlü (14B, daha yavaş)
OLLAMA_MODEL = "qwen2.5:14b-instruct-q4_K_M"
```

### Batch Processing
Birden fazla CSV'yi arka arkaya işle:

```bash
for csv in *.csv; do
  echo "Processing $csv..."
  # Programatik olarak process et
done
```

---

## 🚀 Yol Haritası

### ✅ Tamamlanan
- [x] CSV parsing
- [x] X scraping (Selenium)
- [x] LLM integration (Ollama)
- [x] Prompt engineering
- [x] Reporting system
- [x] Gradio UI
- [x] Terminal tracking

### 🔄 Planlanan
- [ ] Scheduler (haftalık otomatik raporlar)
- [ ] RAG (Vector store ile enhanced context)
- [ ] Trend analysis (zaman serisi)
- [ ] Dashboard (comparative analytics)
- [ ] Docker deployment
- [ ] API endpoints (FastAPI)
- [ ] Batch export (CSV/JSON/PDF)

---

## 📧 İletişim & Katkıda Bulunma

**Geliştirici:** Baran Can  
**Email:** baran@example.com  
**İşletme:** Ankara Metropolitan Municipality  

**Katkıda Bulun:**
1. Fork et
2. Branch oluştur (`git checkout -b feature/xyz`)
3. Commit et (`git commit -m "Add xyz"`)
4. Push et (`git push origin feature/xyz`)
5. Pull Request aç

---

## 📄 Lisans

MIT License - Detaylar için `LICENSE` dosyasına bak

---

## 🙏 Teşekkürler

- 🦙 **Ollama** - Lokal LLM inference
- 🤖 **Qwen** - Açık kaynak LLM modeli
- 🌐 **Selenium** - Web scraping
- 💜 **Gradio** - Web UI framework
- 🐍 **Python** - Harika dil

---

**Made with ❤️ for Ankara**  
*"Teknoloji halkın hizmetinde olmalı"*