# 🏛️ Meclis İstihbarat Sistemi

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Built with Qwen2.5](https://img.shields.io/badge/LLM-Qwen2.5-7B-red.svg)](https://huggingface.co/Qwen/Qwen2.5-7B)

**Ankara Belediyesi meclis üyelerinin X/Twitter aktivitesini otomatik olarak toplarıp Qwen2.5-7B LLM ile analiz eden, tamamen açık kaynak ve lokal çalışan yapay zeka sistemi.**

---

## 📊 Sistem Akışı
```
CSV (13 Meclis Üyesi)
    ↓
X/Twitter Scraping (Selenium + Undetected Chrome)
    ├─ Tweet Text
    ├─ Timestamp (from Twitter)
    ├─ Engagement Metrics (likes, replies, retweets)
    ├─ RT Detection & Source Tracking
    └─ Date Filtering (90 days)
    ↓
SQLite Database v3.0
    ├─ Deduplication (tweet_id based)
    ├─ Incremental Sync (only new tweets)
    ├─ Sync Logging
    └─ Archive Management
    ↓
LLM Analysis (Qwen2.5-7B)
    └─ Turkish Political Analysis
    ↓
Gradio Web UI (Module 3 - Coming Soon)
    └─ Interactive Reports & Q&A
```

---

## 🎯 PROJECT STATUS

| Module | Status | Details |
|--------|--------|---------|
| **Module 1: Data Collection** | ✅ COMPLETE | 600+ tweets from 12/13 users |
| **Module 2: LLM Analysis** | 🔄 IN PROGRESS | Qwen2.5-7B integration ready |
| **Module 3: Web UI** | ⏳ QUEUED | Gradio interface planned |

---

## ✨ ÖZELLIKLER

### ✅ Module 1: Smart Data Collection

- **Selenium + Undetected Chrome** - Real X/Twitter data collection
- **Bot Detection Bypass** - Anti-bot mechanisms neutralized
- **Rich Metadata Extraction**
  - Tweet text (UTF-8 Turkish support)
  - Tweet date (from Twitter)
  - Engagement metrics (likes, replies, retweets)
  - Retweet detection & source tracking
  - User engagement score calculation

- **Database v3.0 - Production Ready**
  - Automatic deduplication (`tweet_id` based)
  - Incremental sync (only fetch new tweets on repeated runs)
  - Duplicate prevention (verified: 0 duplicates on 2nd run)
  - Sync logging for audit trail
  - Tweet archive for deleted content tracking
  
- **Advanced Scraping Optimization**
  - `MAX_SCROLLS = 100` (deeper content loading)
  - `CONSECUTIVE_OLD_THRESHOLD = 20` (tolerant date filtering)
  - Random delays (2-30s) for human-like behavior
  - Automatic scroll position reset for consistency

### ⏳ Module 2: LLM Analysis (In Progress)

- **Qwen2.5-7B-Instruct** (4.7GB, Q4_K_M quantized)
- **Turkish Language Support** (native 18T token training)
- **Evidence-Based Answers** (cites tweet numbers)
- **Political Analysis Framework**
  - Main agendas
  - Dominant themes
  - Political stance (CHP/AKP)
  - Temporal trends

### 🎨 Module 3: Web UI (Planned)

- **Gradio Interface**
  - CSV upload
  - Real-time scraping progress
  - LLM-powered Q&A
  - HTML report generation
  - Interactive dashboard

---

## 📁 Project Structure
```
MeclisIstihbaratSistemi/
│
├── 🐦 x_scraper.py (352 lines)
│   ├─ XTwitterScraper class
│   ├─ Selenium automation
│   ├─ Metadata extraction (6 fields)
│   ├─ RT detection algorithms
│   └─ Rate limiting & error handling
│
├── 📦 models/
│   ├─ __init__.py
│   └─ database.py (v3.0)
│       ├─ councilors table
│       ├─ tweets table (with tweet_id for deduplication)
│       ├─ sync_log table (audit trail)
│       ├─ tweet_archive table
│       └─ 7 performance indexes
│
├── 🔄 scraper_worker.py (v3.1)
│   ├─ CSV loading
│   ├─ RT detection (enhanced)
│   ├─ DB integration
│   ├─ Deduplication verification
│   ├─ Incremental sync
│   └─ Rate limiting (15-30s delays)
│
├── 📊 meclis_app.py (Gradio UI - Ready)
│   ├─ CSV parsing
│   ├─ Scraper coordination
│   ├─ LLM analysis
│   └─ Report generation
│
├── 📄 README.md (This file)
├── 📋 data/data.csv (13 Ankara Council Members)
├── 📦 requirements.txt
├── 🚫 .gitignore
└── 💾 meclis.db (SQLite v3.0 - auto-generated)
```

---

## 🚀 KURULUM (5 ADIM)

### 1. Ön Gereksinimler
```bash
sudo apt-get install -y python3.10 chromium-browser
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

### 4. Initialize Database
```bash
python3 models/database.py
# ✅ Database v3.0 initialized
```

### 5. Module 1: Data Collection
```bash
# First run (full scrape)
python3 scraper_worker.py
# Expected: 600+ tweets from 12 users

# Second run (incremental sync - duplicates filtered)
python3 scraper_worker.py
# Expected: Scraped=600+, Duplicates=600+, Saved=0 ✅
```

---

## 📊 DATA COLLECTION RESULTS (As of Jan 7, 2025)

### Collection Statistics
```
Total Users Processed:    12/13
Total Tweets Scraped:     600+ (target: 100+/user)
Average per User:         50+ tweets
Collection Method:        Selenium + Undetected Chrome
Time Window:              Last 90 days
Metadata Quality:         ✅ Complete
Deduplication:            ✅ Verified (0 dupes on 2nd run)
```

### Top Collectors
```
1. @cihanayhan85        100 tweets
2. @mustafasenkb        98 tweets
3. @atila_celik06       92 tweets
4. @avfatihunal         58 tweets
5. @MehmetAAygun        57 tweets
... (7 more users)
```

### Database Quality Metrics
```
✅ Zero Duplicates        (tweet_id deduplication verified)
✅ All Timestamps Valid   (90-day filtering working)
✅ Metadata Complete      (6/6 fields extracted)
✅ RT Detection Active    (is_retweet flag set)
✅ Engagement Scores      (calculated from metrics)
✅ Sync Logging Ready     (audit trail in place)
```

---

## ⚠️ KNOWN ISSUES & LIMITATIONS

### 1. X.com Rate Limiting
**Issue:** After multiple logins in short period, X.com temporarily blocks scraping
**Status:** Expected behavior (anti-bot protection)
**Solution:** Wait 2-4 hours, then resume (implemented: 15-30s delays between users)
**Workaround:** Use credential caching, minimize re-logins

### 2. @brahimuyar12 Returns No Tweets
**Possible Reasons:**
- Private account mode
- Low activity in last 90 days
- Account protection settings
**Status:** Skipped in current run (marked as no_tweets)

### 3. RT Detection v1.0
**Limitation:** Classic "RT @username:" format detected, but new X.com quote-retweet format incomplete
**Status:** Working (0 false positives in v1.0)
**Improvement:** Will be enhanced in Module 2 (LLM can provide context)

---

## 🛠️ NEXT STEPS (Roadmap)

### Immediate (This Week)
- [ ] Module 2: LLM Analysis Integration
  - Question-based analysis system
  - Evidence-backed responses
  - Turkish political analysis prompts
  
- [ ] Module 3: Gradio Web UI
  - CSV upload interface
  - Real-time scraping progress
  - Report generation

### Short-term (Next Week)
- [ ] Incremental Sync Scheduler
  - APScheduler integration
  - Daily/weekly runs
  - Auto-update capability

- [ ] RT Detection v2.0
  - Quote-tweet format support
  - Source tracking improvement
  - Context awareness

### Medium-term (2-3 Weeks)
- [ ] Production Deployment
  - Docker containerization
  - Server deployment guide
  - Production database setup

- [ ] Advanced Features
  - Sentiment analysis
  - Trend detection
  - Time-series analysis
  - Comparative dashboards

---

## 💾 DATABASE SCHEMA v3.0

### tables

**councilors** (13 rows)
```
id, username (UNIQUE), name, party, district, 
last_synced, sync_status, created_at, updated_at
```

**tweets** (600+ rows)
```
id, username (FK), tweet_id (UNIQUE), tweet_text, tweet_date,
is_retweet, retweet_from, likes, replies, retweets, views,
engagement_score, is_deleted, created_at, updated_at
```

**sync_log** (audit trail)
```
id, username (FK), sync_type, tweets_collected, 
duplicates_skipped, start_time, end_time, status, error_message
```

**tweet_archive** (deleted content)
```
id, username (FK), tweet_id, tweet_text, deleted_at, reason
```

### Indexes
- `idx_tweets_username` (fast user lookups)
- `idx_tweets_date` (date range queries)
- `idx_tweets_tweet_id` (deduplication checks)
- `idx_tweets_deleted` (archive queries)
- `idx_councilors_last_synced` (sync tracking)

---

## 🔒 Gizlilik & Güvenlik

✅ **Tamamen Lokal** - Hiçbir bulut API yok  
✅ **Açık Kaynak** - MIT License, audit edilebilir  
✅ **Veri Güvenliği** - SQLite, şifrelenmiş depolama mümkün  
✅ **GDPR Uyumlu** - Veri silme / archival destekli  

---

## 📧 İletişim & Support

**Geliştirici:** Baran Can  
**Kurum:** Ankara Metropolitan Municipality  
**GitHub:** https://github.com/barancan/MeclisIstihbaratSistemi  

---

## 📄 Lisans

MIT License - Detaylar için LICENSE dosyasına bakın

---

## 🎓 Technical Stack

| Layer | Tool | Version |
|-------|------|---------|
| Language | Python | 3.10+ |
| Web Scraper | Selenium | 4.15+ |
| Bot Detection Bypass | undetected-chromedriver | 3.5+ |
| Database | SQLite3 | Native |
| LLM | Qwen2.5-7B | 4.7GB |
| LLM Runner | Ollama | Latest |
| Web UI | Gradio | 4.0+ |
| Data Processing | Pandas | 2.0+ |

---

**Made with ❤️ for Ankara Democracy**  
*"Teknoloji halkın hizmetinde olmalı"*

---

## 📝 Changelog

### v3.1 (Jan 7, 2025)
- ✅ Module 1: Data Collection COMPLETE
- ✅ Database v3.0 with deduplication
- ✅ 600+ tweets collected from 12/13 users
- ✅ Incremental sync verified
- ⏳ Rate limiting improvements (15-30s delays)
- ⏳ Module 2-3 in progress

### v3.0 (Jan 6, 2025)
- ✅ Database schema redesign
- ✅ Deduplication system
- ✅ Sync logging
- ✅ Archive management

### v2.0 (Jan 5, 2025)
- ✅ Scraper optimization (MAX_SCROLLS=100)
- ✅ RT detection v1.0
- ✅ Engagement metrics extraction

### v1.0 (Dec 2024)
- ✅ Initial project setup
- ✅ Selenium scraper
- ✅ Basic database

