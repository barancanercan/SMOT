<div align="center">

# M.I.S - Meclis Istihbarat Sistemi

### Yapay Zeka Destekli Siyasi Istihbarat Analiz Platformu

[![Live Demo](https://img.shields.io/badge/Demo-Live-success?style=for-the-badge&logo=vercel)](https://meclis-istihbarat-sistemi.vercel.app)
[![API](https://img.shields.io/badge/API-Online-success?style=for-the-badge&logo=fastapi)](https://meclisistihbaratsistemi.onrender.com/docs)

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-000000?style=flat-square&logo=next.js&logoColor=white)](https://nextjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.3+-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--3.5-412991?style=flat-square&logo=openai&logoColor=white)](https://openai.com)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

<br/>

<img src="https://raw.githubusercontent.com/barancanercan/MeclisIstihbaratSistemi/main/docs/banner.png" alt="M.I.S Banner" width="800"/>

**Turkiye'nin Belediye Meclis uyelerinin sosyal medya aktivitelerini analiz eden,**
**profesyonel istihbarat raporlari ureten modern SaaS platformu.**

[Canli Demo](https://meclis-istihbarat-sistemi.vercel.app) · [API Dokumantasyonu](https://meclisistihbaratsistemi.onrender.com/docs) · [Hata Bildir](https://github.com/barancanercan/MeclisIstihbaratSistemi/issues)

</div>

---

## Icindekiler

- [Ozellikler](#-ozellikler)
- [Ekran Goruntuleri](#-ekran-goruntuleri)
- [Teknoloji Stack](#-teknoloji-stack)
- [Hizli Baslangic](#-hizli-baslangic)
- [Kurulum](#-kurulum)
- [API Referansi](#-api-referansi)
- [Analiz Framework'u](#-analiz-frameworku)
- [Deployment](#-deployment)
- [Katkida Bulunma](#-katkida-bulunma)
- [Lisans](#-lisans)

---

## Ozellikler

### Yapay Zeka Destekli Analiz

<table>
<tr>
<td width="50%">

**Yesil Takim Analizi**
- Parti liderligine destek tespiti
- Sadakat seviyesi olcumu
- Parti ici iletisim analizi

</td>
<td width="50%">

**Kirmizi Takim Analizi**
- Muhalefet elestiri tespiti
- Rakip parti analizi
- Politik polemik takibi

</td>
</tr>
<tr>
<td width="50%">

**Gri Takim Analizi**
- Apolitik icerik tespiti
- Yerel hizmet vurgusu
- Bagimsiz gundem analizi

</td>
<td width="50%">

**Coklu LLM Destegi**
- OpenAI GPT-3.5/4 (Onerilir)
- Ollama (Yerel & Ucretsiz)
- Otomatik fallback sistemi

</td>
</tr>
</table>

### Raporlama Modulleri

| Modul | Aciklama | Ozellikler |
|-------|----------|------------|
| **Bireysel Rapor** | Tek kullanici icin detayli analiz | Profil, engagement, LLM analizi |
| **Parti Raporu** | Tum parti uyeleri analizi | Uye bazli + birlesik AI rapor |
| **Coklu Rapor** | Secilen kullanicilar | Grup analizi + karsilastirma |
| **Karsilastirma** | 2-10 kullanici | Metrik + grafik + AI ozeti |

### Kullanici Yonetimi

- **Tekli Ekleme** - Form ile hizli kullanici kaydi
- **Toplu Ekleme** - CSV formatinda bulk import
- **Akilli Silme** - Cascade delete (tweetler, profiller, cache)
- **Parti Normalizasyonu** - Otomatik parti ismi eslestirme

### Modern Arayuz

- **Full Dark Theme** - Goz yormayan karanlik tasarim
- **Responsive Design** - Mobil ve tablet uyumlu
- **Turkce UI** - Tamamen Turkce arayuz
- **Canli Grafikler** - Recharts ile interaktif grafikler
- **Hizli Arama** - Klavye ile aninda erisim

---

## Ekran Goruntuleri

<div align="center">

### Ana Sayfa
<img src="https://raw.githubusercontent.com/barancanercan/MeclisIstihbaratSistemi/main/docs/screenshots/landing.png" alt="Landing Page" width="700"/>

### Dashboard
<img src="https://raw.githubusercontent.com/barancanercan/MeclisIstihbaratSistemi/main/docs/screenshots/dashboard.png" alt="Dashboard" width="700"/>

### Rapor Olusturma
<img src="https://raw.githubusercontent.com/barancanercan/MeclisIstihbaratSistemi/main/docs/screenshots/reports.png" alt="Reports" width="700"/>

### Karsilastirma
<img src="https://raw.githubusercontent.com/barancanercan/MeclisIstihbaratSistemi/main/docs/screenshots/comparison.png" alt="Comparison" width="700"/>

</div>

---

## Teknoloji Stack

<div align="center">

### Backend
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)](https://sqlalchemy.org)
[![Pydantic](https://img.shields.io/badge/Pydantic-E92063?style=for-the-badge&logo=pydantic&logoColor=white)](https://pydantic.dev)

### Frontend
[![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org)
[![React](https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![TailwindCSS](https://img.shields.io/badge/Tailwind-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white)](https://tailwindcss.com)

### AI & Data
[![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com)
[![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)
[![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org)

### Deployment
[![Vercel](https://img.shields.io/badge/Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://vercel.com)
[![Render](https://img.shields.io/badge/Render-46E3B7?style=for-the-badge&logo=render&logoColor=black)](https://render.com)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)

</div>

---

## Hizli Baslangic

### Gereksinimler

| Yazilim | Minimum Versiyon |
|---------|-----------------|
| Python | 3.10+ |
| Node.js | 20+ |
| Git | 2.0+ |

### 30 Saniyede Basla

```bash
# 1. Klonla
git clone https://github.com/barancanercan/MeclisIstihbaratSistemi.git
cd MeclisIstihbaratSistemi

# 2. Backend
cd backend
python -m venv .venv && .venv\Scripts\activate  # Windows
pip install -r requirements.txt
cp .env.example .env  # API key'leri duzenle
uvicorn app.main:app --reload

# 3. Frontend (yeni terminal)
cd frontend
npm install && npm run dev
```

**Erisim:**
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

---

## Kurulum

### Backend Detayli Kurulum

```bash
cd backend

# Virtual Environment
python -m venv .venv

# Aktivasyon
.venv\Scripts\activate      # Windows CMD
.venv\Scripts\Activate.ps1  # Windows PowerShell
source .venv/bin/activate   # Linux/macOS

# Bagimliliklari Yukle
pip install -r requirements.txt

# Environment Dosyasi
cp .env.example .env
```

#### `.env` Konfigurasyonu

```env
# ============================================
# LLM AYARLARI (Zorunlu)
# ============================================
LLM_PROVIDER=openai

# OpenAI (Onerilir - Hizli & Guvenilir)
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_TIMEOUT=60

# Ollama (Alternatif - Ucretsiz & Yerel)
OLLAMA_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:3b

# ============================================
# VERITABANI
# ============================================
DATABASE_URL=sqlite:///./data/meclis.db

# ============================================
# API AYARLARI
# ============================================
ENVIRONMENT=development
DEBUG=true
API_PREFIX=/api/v1
CORS_ORIGINS=http://localhost:3000

# ============================================
# GUVENLIK
# ============================================
SECRET_KEY=your-secret-key-change-in-production
```

#### Veritabanini Baslat

```bash
python -c "from app.core.database import init_database; init_database()"
```

#### Sunucuyu Calistir

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Detayli Kurulum

```bash
cd frontend

# Bagimliliklari Yukle
npm install

# Environment (opsiyonel - default localhost:8000)
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Gelistirme Sunucusu
npm run dev

# Production Build
npm run build && npm start
```

---

## API Referansi

### Base URL

| Ortam | URL |
|-------|-----|
| Production | `https://meclisistihbaratsistemi.onrender.com` |
| Development | `http://localhost:8000` |

### Endpoints

<details>
<summary><b>Sistem</b></summary>

| Method | Endpoint | Aciklama |
|--------|----------|----------|
| `GET` | `/health` | Saglik kontrolu |
| `GET` | `/api/v1/health` | API durumu |
| `GET` | `/api/v1/dashboard/overview` | Dashboard verileri |

</details>

<details>
<summary><b>Kullanicilar</b></summary>

| Method | Endpoint | Aciklama |
|--------|----------|----------|
| `GET` | `/api/v1/users` | Kullanici listesi |
| `GET` | `/api/v1/users/{username}` | Kullanici detayi |
| `POST` | `/api/v1/users` | Yeni kullanici ekle |
| `POST` | `/api/v1/users/bulk` | Toplu kullanici ekle |
| `DELETE` | `/api/v1/users/{username}` | Kullanici sil |

**Tekli Kullanici Ekleme:**
```json
POST /api/v1/users
{
  "username": "example_user",
  "name": "Ornek Kullanici",
  "party": "CHP",
  "district": "Kadikoy"
}
```

**Toplu Kullanici Ekleme:**
```json
POST /api/v1/users/bulk
{
  "users": [
    {"username": "user1", "name": "User 1", "party": "AK Parti"},
    {"username": "user2", "name": "User 2", "party": "CHP"}
  ]
}
```

</details>

<details>
<summary><b>Tweetler</b></summary>

| Method | Endpoint | Aciklama |
|--------|----------|----------|
| `GET` | `/api/v1/tweets/{username}` | Kullanici tweetleri |
| `GET` | `/api/v1/tweets/{username}/top` | En iyi tweetler |

</details>

<details>
<summary><b>Analitik</b></summary>

| Method | Endpoint | Aciklama |
|--------|----------|----------|
| `GET` | `/api/v1/analytics/followers` | Takipci siralamalari |
| `GET` | `/api/v1/analytics/parties` | Parti istatistikleri |
| `POST` | `/api/v1/analytics/compare` | Kullanici karsilastir |
| `POST` | `/api/v1/analytics/compare/llm` | AI ile karsilastir |

**Karsilastirma Istegi:**
```json
POST /api/v1/analytics/compare
{
  "usernames": ["user1", "user2", "user3"]
}
```

</details>

<details>
<summary><b>Raporlar</b></summary>

| Method | Endpoint | Aciklama |
|--------|----------|----------|
| `POST` | `/api/v1/reports/generate` | Kullanici raporu |
| `POST` | `/api/v1/reports/party` | Parti raporu |
| `POST` | `/api/v1/reports/multi` | Coklu kullanici raporu |

**Kullanici Raporu:**
```json
POST /api/v1/reports/generate
{
  "username": "example_user",
  "use_llm": true,
  "force_refresh": false
}
```

**Parti Raporu:**
```json
POST /api/v1/reports/party
{
  "party": "CHP",
  "use_llm": true
}
```

**Coklu Kullanici Raporu:**
```json
POST /api/v1/reports/multi
{
  "usernames": ["user1", "user2"],
  "use_llm": true
}
```

</details>

<details>
<summary><b>Export</b></summary>

| Method | Endpoint | Aciklama |
|--------|----------|----------|
| `GET` | `/api/v1/exports/followers/excel` | Excel indir |

</details>

---

## Analiz Framework'u

M.I.S, siyasi icerik analizinde **Yesil-Kirmizi-Gri Takim** framework'unu kullanir:

```
┌─────────────────────────────────────────────────────────────┐
│                    TWEET ANALIZI                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   YESIL     │  │   KIRMIZI   │  │    GRI      │         │
│  │   TAKIM     │  │    TAKIM    │  │   TAKIM     │         │
│  ├─────────────┤  ├─────────────┤  ├─────────────┤         │
│  │ Parti       │  │ Muhalefet   │  │ Apolitik    │         │
│  │ Sadakati    │  │ Elestirisi  │  │ Icerik      │         │
│  ├─────────────┤  ├─────────────┤  ├─────────────┤         │
│  │ • Lider     │  │ • Rakip     │  │ • Yerel     │         │
│  │   destegi   │  │   elestiri  │  │   hizmet    │         │
│  │ • Parti     │  │ • Hukumet   │  │ • Kisisel   │         │
│  │   savunusu  │  │   politika  │  │   paylasim  │         │
│  │ • Basari    │  │ • Politik   │  │ • Gunluk    │         │
│  │   vurgusu   │  │   polemik   │  │   yasam     │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                             │
│  Sadakat: Dusuk/Orta/Yuksek    Guven Skoru: 0.0 - 1.0      │
└─────────────────────────────────────────────────────────────┘
```

### Analiz Ciktilari

| Metrik | Aciklama | Degerler |
|--------|----------|----------|
| `executive_summary` | Genel ozet | Metin |
| `green_summary` | Yesil takim analizi | Metin |
| `loyalty_level` | Parti sadakat seviyesi | Dusuk/Orta/Yuksek |
| `red_summary` | Kirmizi takim analizi | Metin |
| `criticism_level` | Elestiri seviyesi | Dusuk/Orta/Yuksek |
| `grey_summary` | Gri takim analizi | Metin |
| `independent_topics` | Bagimsiz gundemler | Liste |
| `confidence_score` | Analiz guven skoru | 0.0 - 1.0 |

---

## Deployment

### Vercel (Frontend)

1. [Vercel](https://vercel.com)'e GitHub ile giris yap
2. **Import Project** → Repo sec
3. **Root Directory:** `frontend`
4. **Environment Variables:**
   ```
   NEXT_PUBLIC_API_URL=https://your-backend.onrender.com
   ```
5. **Deploy**

### Render (Backend)

1. [Render](https://render.com)'a GitHub ile giris yap
2. **New Web Service** → Repo sec
3. Ayarlar:
   - **Root Directory:** `backend`
   - **Build Command:** `pip install -r requirements-render.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. **Environment Variables:**
   ```
   OPENAI_API_KEY=sk-xxxxx
   ENVIRONMENT=production
   LLM_PROVIDER=openai
   ```
5. **Create Web Service**

### Docker

```bash
# Tum servisleri baslat
docker-compose up --build

# Sadece backend
cd backend && docker build -t mis-backend . && docker run -p 8000:8000 mis-backend
```

---

## Proje Yapisi

```
MeclisIstihbaratSistemi/
├── backend/
│   ├── app/
│   │   ├── api/v1/           # REST endpoints
│   │   │   ├── dashboard.py  # Dashboard stats
│   │   │   ├── users.py      # User CRUD
│   │   │   ├── tweets.py     # Tweet queries
│   │   │   ├── analytics.py  # Analytics & comparison
│   │   │   └── reports.py    # Report generation
│   │   ├── core/
│   │   │   ├── config.py     # Settings
│   │   │   ├── constants.py  # Party normalization
│   │   │   ├── database.py   # DB operations
│   │   │   └── models.py     # SQLAlchemy models
│   │   ├── services/
│   │   │   ├── analysis/     # LLM integration
│   │   │   │   ├── analyzer.py
│   │   │   │   └── prompts.py
│   │   │   └── reporting/    # Report generation
│   │   └── utils/            # Helpers
│   ├── data/                 # SQLite database
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/              # Next.js pages
│   │   │   ├── page.tsx      # Landing
│   │   │   ├── dashboard/    # Dashboard
│   │   │   ├── analytics/    # Charts
│   │   │   ├── reports/      # Reports
│   │   │   ├── comparison/   # Comparison
│   │   │   ├── users/        # User management
│   │   │   └── system/       # System status
│   │   ├── components/
│   │   │   ├── charts/       # Recharts
│   │   │   ├── layout/       # Sidebar, nav
│   │   │   └── ui/           # UI components
│   │   └── lib/
│   │       └── api.ts        # API client
│   ├── package.json
│   └── tailwind.config.ts
├── docs/                     # Documentation
├── render.yaml               # Render blueprint
├── docker-compose.yml
└── README.md
```

---

## Katkida Bulunma

Katkalarinizi bekliyoruz! Asagidaki adimlari takip edin:

1. **Fork** yapin
2. Feature branch olusturun (`git checkout -b feature/yeni-ozellik`)
3. Degisiklikleri commit edin (`git commit -m 'feat: Yeni ozellik eklendi'`)
4. Branch'i push edin (`git push origin feature/yeni-ozellik`)
5. **Pull Request** acin

### Commit Kurallari

```
feat: Yeni ozellik
fix: Hata duzeltme
docs: Dokumantasyon
style: Kod formati
refactor: Kod iyilestirme
test: Test ekleme
chore: Diger
```

---

## Sorun Giderme

<details>
<summary><b>OpenAI API Hatasi</b></summary>

```bash
# API key kontrol
echo $OPENAI_API_KEY

# .env dosyasini kontrol et
cat backend/.env | grep OPENAI
```
</details>

<details>
<summary><b>CORS Hatasi</b></summary>

```bash
# backend/.env
CORS_ORIGINS=http://localhost:3000,https://your-frontend.vercel.app
```
</details>

<details>
<summary><b>Database Hatasi</b></summary>

```bash
# Veritabanini yeniden olustur
cd backend
python -c "from app.core.database import init_database; init_database()"
```
</details>

<details>
<summary><b>Eski Rapor Gorunuyor</b></summary>

```bash
# Cache temizle
cd backend
python -c "from app.core.database import clear_report_cache; clear_report_cache()"
```
</details>

---

## Lisans

Bu proje [MIT Lisansi](LICENSE) altinda lisanslanmistir.

---

<div align="center">

### Gelistirici

**Baran Can Ercan**

[![GitHub](https://img.shields.io/badge/GitHub-barancanercan-181717?style=for-the-badge&logo=github)](https://github.com/barancanercan)

---

<sub>M.I.S v3.2 - Yapay Zeka ile Siyasi Analiz</sub>

<sub>Made with by Baran Can Ercan</sub>

</div>
