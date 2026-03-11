# Meclis Istihbarat Sistemi

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Yapay Zeka Destekli Siyasi Istihbarat Analiz Platformu**

Turkiye Buyuksehir Belediye Meclisi uyelerinin sosyal medya aktivitelerini analiz eden, stratejik istihbarat raporlari ureten SaaS platformu. Tamamen yerel ve ucretsiz calisir - harici API gerektirmez.

---

## Temel Ozellikler

### Yapay Zeka Analizi
- **Yesil/Kirmizi/Gri Takim Framework'u**: Parti sadakati, muhalefet elestirisi ve bagimsiz gundemleri ayiran analiz metodolojisi
- **Yerel LLM Entegrasyonu**: Ollama ile qwen3:14b modeli (gizlilik odakli, internet baglantisi gerektirmez)
- **Chain-of-Thought & Few-Shot Learning**: Gelismis prompt muhendisligi ile yuksek kaliteli analizler

### Veri Toplama & Analiz
- **X/Twitter Scraping**: Selenium + Undetected Chrome ile engellenmeden veri toplama
- **Vector Arama**: ChromaDB ile anlamsal tweet arama ve benzerlik analizi
- **Profil Takibi**: Takipci sayisi, bio degisiklikleri gibi profil metriklerinin tarihsel takibi

### Raporlama
- **Bireysel Raporlar**: Her meclis uyesi icin detayli istihbarat raporu
- **Parti Raporlari**: Parti bazinda toplu istatistikler ve karsilastirmalar
- **Export**: Markdown, Excel ve PDF formatlari

### Modern Arayuz
- **Dashboard**: Canli istatistikler ve ozet gorunum
- **Analitik**: Takipci siralamalari, parti dagilimi, engagement metrikleri
- **Tweet Arsivi**: Filtreleme, arama ve top tweetler

---

## Hizli Baslangic

### Gereksinimler

| Yazilim | Versiyon | Aciklama |
|---------|----------|----------|
| Python | 3.10+ | Backend |
| Node.js | 20+ | Frontend |
| Ollama | Latest | LLM (qwen3:14b onerilir) |
| Chrome | Latest | Scraping icin |

### 1. Ollama Kurulumu

```bash
# Ollama'yi yukle (https://ollama.ai)
# Ardindan model indir:
ollama pull qwen3:14b
```

### 2. Backend Kurulumu

```bash
cd backend

# Virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Bagimliliklari yukle
pip install -r requirements.txt

# Veritabanini baslat
python -c "from app.core.database import init_database; init_database()"

# API'yi calistir
uvicorn app.main:app --reload --port 8001
```

### 3. Frontend Kurulumu

```bash
cd frontend
npm install
npm run dev
```

### 4. Erisim

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8001/docs
- **API Health**: http://localhost:8001/api/v1/health

### Docker ile Calistirma

```bash
docker-compose up --build
```

---

## Proje Mimarisi

```
meclis-istihbarat/
├── backend/                    # FastAPI Backend (Python)
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/            # REST API endpoints
│   │   │   │   ├── dashboard.py
│   │   │   │   ├── users.py
│   │   │   │   ├── tweets.py
│   │   │   │   ├── analytics.py
│   │   │   │   ├── reports.py
│   │   │   │   └── exports.py
│   │   │   └── deps.py        # Dependency injection
│   │   │
│   │   ├── core/              # Cekirdek moduller
│   │   │   ├── config.py      # Pydantic Settings
│   │   │   ├── database.py    # SQLAlchemy setup
│   │   │   ├── models.py      # ORM modelleri
│   │   │   └── db_config.py   # Session management
│   │   │
│   │   ├── services/          # Is mantigi
│   │   │   ├── analysis/      # LLM & vektorel analiz
│   │   │   │   ├── analyzer.py
│   │   │   │   ├── prompts.py
│   │   │   │   ├── schemas.py
│   │   │   │   └── vector_db.py
│   │   │   ├── reporting/     # Rapor uretimi
│   │   │   └── scraping/      # Veri toplama
│   │   │
│   │   ├── workers/           # Arka plan gorevleri
│   │   └── utils/             # Logger, retry, helpers
│   │
│   ├── tests/                 # Test suite
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                   # Next.js 14 Frontend
│   ├── src/
│   │   ├── app/               # App Router sayfalari
│   │   │   ├── page.tsx       # Dashboard
│   │   │   ├── users/         # Kullanici yonetimi
│   │   │   ├── tweets/        # Tweet arsivi
│   │   │   ├── analytics/     # Analitik
│   │   │   └── reports/       # Raporlar
│   │   ├── components/        # React componentleri
│   │   └── lib/               # API client, utils
│   │
│   ├── package.json
│   └── tailwind.config.ts
│
├── data/                       # SQLite database
├── docs/                       # Dokumantasyon
└── docker-compose.yml
```

---

## API Referansi

### Dashboard
| Method | Endpoint | Aciklama |
|--------|----------|----------|
| GET | `/api/v1/dashboard/overview` | Sistem istatistikleri |
| GET | `/api/v1/health` | API saglik kontrolu |

### Kullanicilar
| Method | Endpoint | Aciklama |
|--------|----------|----------|
| GET | `/api/v1/users` | Tum meclis uyeleri |
| GET | `/api/v1/users/{username}` | Kullanici detayi |
| POST | `/api/v1/users` | Yeni kullanici ekle |
| DELETE | `/api/v1/users/{username}` | Kullanici sil |

### Tweetler
| Method | Endpoint | Aciklama |
|--------|----------|----------|
| GET | `/api/v1/tweets/{username}` | Kullanici tweetleri |
| GET | `/api/v1/tweets/{username}/top` | En iyi tweetler |
| GET | `/api/v1/tweets/{username}/stats` | Tweet istatistikleri |

### Analitik
| Method | Endpoint | Aciklama |
|--------|----------|----------|
| GET | `/api/v1/analytics/followers` | Takipci siralamasi |
| GET | `/api/v1/analytics/parties` | Parti istatistikleri |
| GET | `/api/v1/analytics/engagement` | Engagement metrikleri |

### Raporlar
| Method | Endpoint | Aciklama |
|--------|----------|----------|
| POST | `/api/v1/reports/generate` | Kullanici raporu olustur |
| POST | `/api/v1/reports/party` | Parti raporu olustur |
| GET | `/api/v1/reports/{username}` | Cached rapor getir |

### Export
| Method | Endpoint | Aciklama |
|--------|----------|----------|
| GET | `/api/v1/exports/followers/excel` | Takipci verileri (Excel) |
| GET | `/api/v1/exports/tweets/{username}/excel` | Tweetler (Excel) |

**Interaktif API Dokumantasyonu**: http://localhost:8001/docs

---

## Konfigurasyonu

### Ortam Degiskenleri

`backend/.env` dosyasi olusturun:

```env
# Database
DATABASE_URL=sqlite:///./data/meclis.db

# LLM
OLLAMA_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3:14b

# API
API_PREFIX=/api/v1
DEBUG=true

# CORS
CORS_ORIGINS=http://localhost:3000

# Scraping
SCRAPER_HEADLESS=true
SCRAPER_RATE_LIMIT=5
```

### LLM Model Secimi

| Model | Boyut | Hiz | Kalite | Kullanim |
|-------|-------|-----|--------|----------|
| qwen3:14b | 14B | Orta | Yuksek | Production (onerilir) |
| qwen2.5:3b | 3B | Hizli | Orta | Gelistirme/Test |
| llama3.2:3b | 3B | Hizli | Orta | Alternatif |

---

## Analiz Metodolojisi

### Yesil/Kirmizi/Gri Takim Framework'u

Platform, her politikacinin sosyal medya aktivitesini uc temel kategoride analiz eder:

| Kategori | Aciklama | Ornek |
|----------|----------|-------|
| **Yesil Takim** | Parti sadakati, liderlik destegi, parti etkinlikleri | "Genel Baskan'imizin yanindayiz" |
| **Kirmizi Takim** | Muhalefet elestirisi, siyasi rakiplere yonelik paylasillar | "AKP'nin ekonomi politikalari..." |
| **Gri Takim** | Siyaset disi konular, yerel hizmetler, kisisel paylasillar | "Yeni parkimiz hizmete acildi" |

### Rapor Ciktisi

Her analiz sonucunda:
- **Executive Summary**: 2-3 cumlelik genel degerlendirme
- **Sadakat Seviyesi**: Dusuk / Orta / Yuksek
- **Elestiri Seviyesi**: Dusuk / Orta / Yuksek
- **Bagimsiz Konular**: Siyaset disi ilgi alanlari listesi

---

## Gelistirme

### Kod Kalitesi

```bash
# Backend linting
cd backend && ruff check app/

# Backend tests
cd backend && pytest tests/ -v

# Frontend linting
cd frontend && npm run lint

# Frontend type check
cd frontend && npm run type-check
```

### Veritabani Migrasyonu

```bash
# Yeni tablo eklemek icin
python -c "from app.core.database import init_database; init_database()"

# Cache temizleme
python -c "from app.core.database import clear_report_cache; clear_report_cache()"
```

---

## Teknoloji Yigini

| Katman | Teknoloji | Versiyon |
|--------|-----------|----------|
| **Backend Framework** | FastAPI | 0.100+ |
| **ORM** | SQLAlchemy | 2.0 |
| **Validation** | Pydantic | 2.0 |
| **Frontend Framework** | Next.js | 14 |
| **UI Library** | React | 18 |
| **Styling** | Tailwind CSS | 3.0 |
| **Database (Dev)** | SQLite | 3 |
| **Database (Prod)** | PostgreSQL | 15+ |
| **LLM Runtime** | Ollama | Latest |
| **Vector Database** | ChromaDB | 0.4+ |
| **Scraping** | Selenium | 4.0+ |
| **Browser Automation** | undetected-chromedriver | 3.5+ |

---

## Yol Haritasi

- [ ] PostgreSQL production desteği
- [ ] Celery ile asenkron gorev kuyrugu
- [ ] WebSocket ile canli bildirimler
- [ ] Multi-tenant mimari
- [ ] Gelismis dashbord grafikleri
- [ ] Karsilastirmali parti analizi
- [ ] API rate limiting
- [ ] Kullanici yetkilendirme sistemi

---

## Katkida Bulunma

1. Fork yapın
2. Feature branch olusturun (`git checkout -b feature/amazing-feature`)
3. Degisikliklerinizi commit edin (`git commit -m 'Add amazing feature'`)
4. Branch'i push edin (`git push origin feature/amazing-feature`)
5. Pull Request açın

---

## Lisans

MIT License - Detaylar icin [LICENSE](LICENSE) dosyasina bakin.

---

## Iletisim

**Gelistirici**: Baran Can Ercan

**Proje**: [GitHub Repository](https://github.com/barancanercan/meclis-istihbarat)

---

<p align="center">
  <sub>Yapay Zeka ile Turkiye Siyasetini Anlamak</sub>
</p>
