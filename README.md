# Meclis Istihbarat Sistemi v3.1

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.3+-blue.svg)](https://typescriptlang.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Yapay Zeka Destekli Siyasi Istihbarat Analiz Platformu**

Turkiye Buyuksehir Belediye Meclisi uyelerinin sosyal medya aktivitelerini analiz eden, profesyonel istihbarat raporlari ureten modern SaaS platformu.

---

## Ozellikler

### Yapay Zeka Analizi
- **Yesil/Kirmizi/Gri Takim Framework'u** - Parti sadakati, muhalefet elestirisi ve bagimsiz gundemleri ayiran analiz
- **Coklu LLM Destegi** - OpenAI GPT-3.5 (hizli, onerilir) veya Ollama (yerel, ucretsiz)
- **Chain-of-Thought Prompting** - Gelismis prompt muhendisligi ile kaliteli analizler
- **Turkce NLP** - Tam Turkce dil destegi

### Veri Toplama
- **X/Twitter Scraping** - Selenium + Undetected Chrome
- **Vector Arama** - ChromaDB ile anlamsal arama
- **Profil Takibi** - Tarihsel metrik analizi

### Raporlama
- **PDF Raporlar** - Profesyonel karanlik tema tasarimi
- **Excel Export** - Takipci ve etkilesim verileri
- **Markdown** - Ham rapor ciktisi

### Modern Arayuz
- **Dark Theme** - Tamamen karanlik tema
- **Responsive** - Mobil uyumlu
- **Grafikler** - Recharts ile interaktif grafikler

---

## Teknoloji Stack

| Katman | Teknoloji |
|--------|-----------|
| **Backend** | FastAPI, SQLAlchemy, Pydantic v2 |
| **Frontend** | Next.js 14, React 18, TailwindCSS |
| **Database** | SQLite (dev) / PostgreSQL (prod) |
| **LLM** | OpenAI API / Ollama |
| **Vector DB** | ChromaDB |
| **PDF** | FPDF2 |
| **Charts** | Recharts |

---

## Hizli Baslangic

### Gereksinimler

- Python 3.10+
- Node.js 20+
- Git

### 1. Projeyi Klonla

```bash
git clone https://github.com/username/meclis-istihbarat.git
cd meclis-istihbarat
```

### 2. Backend Kurulumu

```bash
cd backend

# Virtual environment
python -m venv .venv
.venv\Scripts\activate     # Windows
# source .venv/bin/activate  # Linux/Mac

# Bagimliliklar
pip install -r requirements.txt

# Environment
cp .env.example .env
# .env dosyasini duzenle

# Veritabani
python -c "from app.core.database import init_database; init_database()"

# Calistir
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Kurulumu

```bash
cd frontend
npm install
npm run dev
```

### 4. Erisim

| Servis | URL |
|--------|-----|
| Frontend | http://localhost:3000 |
| API Docs | http://localhost:8000/docs |
| Health | http://localhost:8000/api/v1/health |

---

## Konfigrasyon

### Environment Degiskenleri

`backend/.env` dosyasi:

```env
# LLM Provider
LLM_PROVIDER=openai              # openai veya ollama

# OpenAI (Onerilir)
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_TIMEOUT=60

# Ollama (Alternatif)
OLLAMA_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:3b

# Database
DATABASE_URL=sqlite:///./data/meclis.db

# API
API_PREFIX=/api/v1
DEBUG=true
CORS_ORIGINS=http://localhost:3000
```

---

## LLM Secenekleri

### OpenAI (Onerilir)

| Ozellik | Deger |
|---------|-------|
| Model | gpt-3.5-turbo |
| Hiz | 3-5 saniye |
| Maliyet | ~$0.002/analiz |
| Kalite | Mukemmel |

### Ollama (Yerel)

| Ozellik | Deger |
|---------|-------|
| Model | qwen2.5:3b |
| Hiz | 15-60 saniye |
| Maliyet | Ucretsiz |
| Kalite | Iyi |

```bash
# Ollama kurulumu
ollama pull qwen2.5:3b
ollama serve
```

---

## API Endpoints

| Method | Endpoint | Aciklama |
|--------|----------|----------|
| GET | `/api/v1/health` | Sistem durumu |
| GET | `/api/v1/dashboard/overview` | Dashboard verileri |
| GET | `/api/v1/users` | Kullanici listesi |
| GET | `/api/v1/users/{username}` | Kullanici detayi |
| POST | `/api/v1/users` | Kullanici ekle |
| DELETE | `/api/v1/users/{username}` | Kullanici sil |
| GET | `/api/v1/tweets/{username}` | Tweetler |
| GET | `/api/v1/analytics/followers` | Takipci siralamalari |
| GET | `/api/v1/analytics/parties` | Parti istatistikleri |
| POST | `/api/v1/reports/generate` | Rapor olustur |
| GET | `/api/v1/exports/report/{username}/pdf` | PDF indir |
| GET | `/api/v1/exports/followers/excel` | Excel indir |

---

## Proje Yapisi

```
meclis-istihbarat/
├── backend/
│   ├── app/
│   │   ├── api/v1/           # REST endpoints
│   │   ├── core/             # Config, DB, Models
│   │   ├── services/
│   │   │   ├── analysis/     # LLM analiz
│   │   │   ├── reporting/    # PDF generator
│   │   │   └── scraping/     # X scraper
│   │   └── utils/            # Logger, retry
│   ├── scripts/              # Utility scripts
│   ├── tests/                # Test suite
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/              # Next.js pages
│   │   ├── components/       # React components
│   │   └── lib/              # API client
│   └── package.json
├── data/                     # SQLite database
├── .github/workflows/        # CI/CD
├── docker-compose.yml
├── CLAUDE.md                 # AI assistant guide
└── README.md
```

---

## Analiz Framework'u

### Yesil Takim (Parti Sadakati)
- Parti liderligine destek
- Parti etkinlikleri
- Basarilari one cikarma

### Kirmizi Takim (Muhalefet)
- Rakip parti elestirisi
- Hukumet politikalari
- Siyasi polemik

### Gri Takim (Bagimsiz)
- Yerel hizmetler
- Kisisel paylasilmlar
- Apolitik icerik

---

## Docker

```bash
docker-compose up --build
```

---

## Gelistirme

### Test

```bash
# Backend
cd backend && pytest tests/ -v

# Frontend
cd frontend && npm run lint
```

### Cache Temizleme

```bash
cd backend
python -c "from app.core.database import clear_report_cache; clear_report_cache()"
```

---

## Sorun Giderme

| Sorun | Cozum |
|-------|-------|
| OpenAI hatasi | API key kontrol |
| Ollama baglanti | `ollama serve` calistir |
| CORS hatasi | CORS_ORIGINS kontrol |
| Eski rapor | Cache temizle |

---

## Lisans

MIT License

---

## Katki

1. Fork
2. Feature branch (`git checkout -b feature/amazing`)
3. Commit (`git commit -m 'feat: Add feature'`)
4. Push (`git push origin feature/amazing`)
5. Pull Request

---

**Meclis Istihbarat Sistemi** - Yapay Zeka ile Siyasi Analiz
