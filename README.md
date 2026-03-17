# Meclis Istihbarat Sistemi v3.2

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.3+-blue.svg)](https://typescriptlang.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Yapay Zeka Destekli Siyasi Istihbarat Analiz Platformu**

Turkiye Buyuksehir Belediye Meclisi uyelerinin sosyal medya aktivitelerini analiz eden, profesyonel istihbarat raporlari ureten modern SaaS platformu.

---

## v3.2 Yenilikler

- **Kullanici Yonetimi** - Tekli ve toplu kullanici ekleme/silme
- **Coklu Kullanici Raporu** - Birden fazla kullanici icin birlesik rapor + bireysel AI analizi
- **Karsilastirma Modulu** - 2-10 kullaniciyi karsilastirma, grafikler, AI analizi
- **Gelismis Parti Raporu** - Her uye icin bireysel LLM analizi
- **Arama ve Navigasyon** - Harf tuslayarak kullanici arama
- **Tam Turkce Arayuz** - Tum UI ogeleri Turkceleştirildi

---

## Ozellikler

### Yapay Zeka Analizi
- **Yesil/Kirmizi/Gri Takim Framework'u** - Parti sadakati, muhalefet elestirisi ve bagimsiz gundemleri ayiran analiz
- **Coklu LLM Destegi** - OpenAI GPT-3.5 (hizli, onerilir) veya Ollama (yerel, ucretsiz)
- **Bireysel + Birlesik Analiz** - Her kullanici icin ayri ve toplu AI analizi
- **Turkce NLP** - Tam Turkce dil destegi

### Raporlama
- **Kullanici Raporu** - Detayli bireysel analiz
- **Parti Raporu** - Tum parti uyeleri + LLM analizi
- **Coklu Rapor** - Secilen kullanicilar icin birlesik rapor
- **Karsilastirma** - Yan yana metrik karsilastirma + AI

### Kullanici Yonetimi
- **Tekli Ekleme** - Form ile kullanici ekle
- **Toplu Ekleme** - CSV formatinda coklu kullanici
- **Silme** - Cascade delete (tweet, profil, cache)

### Modern Arayuz
- **Karanlik Tema** - Tamamen dark mode
- **Responsive** - Mobil uyumlu
- **Grafikler** - Bar chart, radar chart
- **Arama** - Harf tuslayarak hizli erisim

---

## Teknoloji Stack

| Katman | Teknoloji |
|--------|-----------|
| **Backend** | FastAPI, SQLAlchemy, Pydantic v2 |
| **Frontend** | Next.js 14, React 18, TailwindCSS |
| **Database** | SQLite (dev) / PostgreSQL (prod) |
| **LLM** | OpenAI API / Ollama |
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

## API Endpoints

| Method | Endpoint | Aciklama |
|--------|----------|----------|
| GET | `/api/v1/health` | Sistem durumu |
| GET | `/api/v1/dashboard/overview` | Dashboard verileri |
| GET | `/api/v1/users` | Kullanici listesi |
| GET | `/api/v1/users/{username}` | Kullanici detayi |
| POST | `/api/v1/users` | Kullanici ekle |
| POST | `/api/v1/users/bulk` | Toplu kullanici ekle |
| DELETE | `/api/v1/users/{username}` | Kullanici sil |
| GET | `/api/v1/tweets/{username}` | Tweetler |
| GET | `/api/v1/analytics/followers` | Takipci siralamalari |
| GET | `/api/v1/analytics/parties` | Parti istatistikleri |
| POST | `/api/v1/analytics/compare` | Kullanici karsilastir |
| POST | `/api/v1/analytics/compare/llm` | AI ile karsilastir |
| POST | `/api/v1/reports/generate` | Kullanici raporu |
| POST | `/api/v1/reports/party` | Parti raporu |
| POST | `/api/v1/reports/multi` | Coklu kullanici raporu |
| GET | `/api/v1/exports/followers/excel` | Excel indir |

---

## Sayfalar

| Sayfa | Yol | Aciklama |
|-------|-----|----------|
| Dashboard | `/` | Genel bakis |
| Analitik | `/analytics` | Takipci, parti grafikleri |
| Raporlar | `/reports` | Kullanici/parti/coklu rapor |
| Karsilastirma | `/comparison` | Kullanici karsilastirma |
| Kullanicilar | `/users` | Kullanici yonetimi |
| Tweetler | `/tweets` | Tweet arama |
| Sistem | `/system` | Sistem durumu |

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

**Meclis Istihbarat Sistemi** - Yapay Zeka ile Siyasi Analiz
