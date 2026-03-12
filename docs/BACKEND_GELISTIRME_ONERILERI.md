# Backend Gelistirme Onerileri

> **Meclis Istihbarat Sistemi - FastAPI Backend Uzman Raporu**
>
> Tarih: Mart 2026 | Versiyon: 3.0

---

## Executive Summary

Backend, FastAPI + SQLAlchemy ORM uzerine kurulu basit ama islevsel bir yapidir. **Guvenlik eksiklikleri kritik seviyededir** - authentication yok, CORS tum originlere acik, rate limiting mevcut degil. Production'a cikmadan once P0 seviyesindeki guvenlik onlemleri ZORUNLUDUR.

**Mevcut Skor:** 3.7/10
**Hedef Skor:** 7.5/10 (6 ay sonra)

---

## Mevcut Durum Analizi

### Guclu Yanlar
| Alan | Detay | Dosya |
|------|-------|-------|
| ORM Kullanimi | SQLAlchemy ile clean data access | `database.py` |
| Pydantic Settings | Type-safe configuration | `config.py` |
| Session Yonetimi | `session_scope()` context manager | `db_config.py` |
| Retry Decorators | `@retry_on_db_error` pattern | `retry_config.py` |
| API Documentation | Swagger/ReDoc otomatik | `main.py:27-30` |

### Kritik Zayifliklar
| Alan | Sorun | Risk Seviyesi |
|------|-------|---------------|
| Authentication | HIC YOK | **KRITIK** |
| CORS | `allow_origins=["*"]` | **KRITIK** |
| Rate Limiting | HIC YOK | **YUKSEK** |
| Input Validation | Kismi (SQL Injection riski dusuk) | **ORTA** |
| Database | SQLite (production icin uygun degil) | **YUKSEK** |

---

## P0: Kritik Oncelik - GUVENLIK (Hemen Yapilmali)

### 1. Authentication Sistemi

**Problem:** Tum API endpointleri acik, herhangi bir kimlik dogrulama yok.

**Dosya:** `backend/app/main.py` - middleware eklenmeli

**Cozum - JWT Authentication:**
```python
# app/core/security.py (yeni dosya)
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise JWTError()
        return TokenData(username=username)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

**Dependency Injection:**
```python
# app/api/deps.py - Guncelle
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    return verify_token(token)
```

**Gerekli Paketler:**
```
python-jose[cryptography]
passlib[bcrypt]
```

**Effort:** Medium | **Impact:** Critical

---

### 2. CORS Duzeltmesi

**Problem:** `allow_origins=["*"]` tum domainlerden erisime izin verir - CSRF saldirilarina acik.

**Dosya:** `backend/app/main.py:35-41`

**Mevcut Kod (GUVENLI DEGIL):**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # <-- TEHLIKE
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Duzeltilmis Kod:**
```python
# main.py
from app.core.config import settings

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,  # config'den al
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

**Config Guncellemesi:**
```python
# config.py - Varsayilan degeri guncelle
cors_origins: str = Field(
    default="http://localhost:3000,http://127.0.0.1:3000",  # Sadece frontend
    description="Allowed CORS origins"
)
```

**Effort:** Low | **Impact:** Critical

---

### 3. Rate Limiting

**Problem:** API rate limiting yok - DDoS ve abuse'a acik.

**Cozum - slowapi Kullanimi:**
```python
# app/core/rate_limit.py (yeni dosya)
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

# main.py'de ekle
from app.core.rate_limit import limiter

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Endpoint'lerde kullan
@router.post("/reports/generate")
@limiter.limit("5/minute")  # Dakikada 5 istek
async def generate_report(request: Request, ...):
    pass
```

**Rate Limit Onerileri:**
| Endpoint | Limit | Aciklama |
|----------|-------|----------|
| `/reports/generate` | 5/minute | LLM yogun |
| `/users` | 30/minute | Liste sorgusu |
| `/tweets/{user}` | 20/minute | Veri okuma |
| `POST /users` | 10/hour | Kullanici ekleme |

**Gerekli Paket:**
```
slowapi
```

**Effort:** Low | **Impact:** High

---

## P1: Yuksek Oncelik (30 Gun Icinde)

### 4. PostgreSQL Migration

**Problem:** SQLite production icin uygun degil - concurrent yazma, olcekleme, backup sorunlari.

**Dosya:** `backend/app/core/config.py:40-46`

**Adim 1 - Alembic Kurulumu:**
```bash
pip install alembic psycopg2-binary
alembic init alembic
```

**Adim 2 - alembic.ini Ayarlari:**
```ini
[alembic]
script_location = alembic
sqlalchemy.url = postgresql://user:pass@localhost/meclis_db
```

**Adim 3 - Migration Olusturma:**
```bash
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

**Config Guncellemesi:**
```python
# config.py
database_url: str = Field(
    default="postgresql://localhost/meclis_db",  # Production default
    description="Database connection URL"
)
```

**Veri Migrasyon Scripti:**
```python
# scripts/migrate_sqlite_to_pg.py
import sqlite3
import psycopg2

def migrate():
    sqlite_conn = sqlite3.connect("data/meclis.db")
    pg_conn = psycopg2.connect("postgresql://...")

    # Councilors
    for row in sqlite_conn.execute("SELECT * FROM councilors"):
        pg_conn.execute("INSERT INTO councilors VALUES (%s, ...)", row)

    # Tweets
    for row in sqlite_conn.execute("SELECT * FROM tweets"):
        pg_conn.execute("INSERT INTO tweets VALUES (%s, ...)", row)

    pg_conn.commit()
```

**Effort:** High | **Impact:** High

---

### 5. Celery Async Tasks

**Problem:** LLM analizi senkron - API'yi 5+ dakika bloke edebilir.

**Dosya:** `backend/app/api/v1/reports.py:28-68`

**Cozum:**
```python
# app/workers/celery_app.py (yeni dosya)
from celery import Celery

celery_app = Celery(
    "meclis_worker",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1"
)

@celery_app.task(bind=True, max_retries=3)
def generate_report_task(self, username: str, use_llm: bool = True):
    try:
        generator = ReportGenerator(use_llm=use_llm)
        report = generator.generate_report(username)
        save_report_cache(username, "full" if use_llm else "quick", report)
        return {"status": "success", "username": username}
    except Exception as e:
        self.retry(countdown=60)
```

**API Endpoint Guncellemesi:**
```python
# reports.py
from app.workers.celery_app import generate_report_task

@router.post("/generate")
async def generate_report(request: GenerateReportRequest):
    # Async task baslat
    task = generate_report_task.delay(request.username, request.use_llm)
    return {
        "task_id": task.id,
        "status": "processing",
        "status_url": f"/reports/status/{task.id}"
    }

@router.get("/status/{task_id}")
async def get_report_status(task_id: str):
    task = celery_app.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": task.state,
        "result": task.result if task.ready() else None
    }
```

**Gerekli Altyapi:**
- Redis server
- Celery worker process

**Effort:** High | **Impact:** Critical

---

## P2: Orta Oncelik (60 Gun Icinde)

### 6. Pagination Implementasyonu

**Problem:** Tum liste endpointleri pagination yok - buyuk veri setlerinde performans sorunu.

**Dosya:** `backend/app/api/v1/users.py:17-51`

**Cozum:**
```python
# app/api/schemas/common.py (yeni dosya)
from pydantic import BaseModel
from typing import Generic, TypeVar, List

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int

# users.py - Guncelle
@router.get("/", response_model=PaginatedResponse)
async def get_all_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    party: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Councilor)

    if party:
        query = query.filter(Councilor.party.ilike(f"%{party}%"))

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return PaginatedResponse(
        items=[...],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )
```

**Effort:** Low | **Impact:** Medium

---

### 7. API Versioning Strategy

**Problem:** `/api/v1` prefix var ama versioning stratejisi belirsiz.

**Cozum:**
```python
# app/api/__init__.py
from fastapi import APIRouter

# v1 router (mevcut)
from app.api.v1.router import api_router as v1_router

# v2 router (gelecek)
# from app.api.v2.router import api_router as v2_router

def setup_routes(app):
    app.include_router(v1_router, prefix="/api/v1")
    # app.include_router(v2_router, prefix="/api/v2")

    # Deprecation header middleware
    @app.middleware("http")
    async def add_deprecation_header(request, call_next):
        response = await call_next(request)
        if "/api/v1/" in str(request.url):
            response.headers["Deprecation"] = "false"
            response.headers["Sunset"] = "2027-01-01"  # Ornek
        return response
```

**Effort:** Low | **Impact:** Low

---

### 8. Test Coverage %80

**Problem:** Test dosyalari mevcut degil veya cok az.

**Hedef Struktur:**
```
backend/
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # Fixtures
│   ├── test_users.py         # User API tests
│   ├── test_reports.py       # Report API tests
│   ├── test_analyzer.py      # LLM analyzer tests
│   └── test_database.py      # Database function tests
```

**conftest.py Ornegi:**
```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.models import Base
from app.api.deps import get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture
def test_db():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(test_db):
    return TestClient(app)
```

**Test Ornegi:**
```python
# tests/test_users.py
def test_get_all_users(client):
    response = client.get("/api/v1/users")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_user_not_found(client):
    response = client.get("/api/v1/users/nonexistent")
    assert response.status_code == 404
```

**Effort:** High | **Impact:** High

---

## P3: Gelecek Planlamasi (90+ Gun)

### 9. Scraper Abstraction Layer

**Problem:** Scraper dogrudan Selenium'a bagimli, alternatif kaynaklara gecis zor.

**Dosya:** `backend/app/services/scraping/`

**Cozum - Strategy Pattern:**
```python
# services/scraping/base.py
from abc import ABC, abstractmethod
from typing import List, Dict

class BaseScraper(ABC):
    @abstractmethod
    async def get_user_tweets(self, username: str, limit: int) -> List[Dict]:
        pass

    @abstractmethod
    async def get_user_profile(self, username: str) -> Dict:
        pass

# services/scraping/selenium_scraper.py
class SeleniumScraper(BaseScraper):
    async def get_user_tweets(self, username: str, limit: int) -> List[Dict]:
        # Mevcut implementasyon
        pass

# services/scraping/api_scraper.py (gelecek)
class OfficialAPIScraper(BaseScraper):
    async def get_user_tweets(self, username: str, limit: int) -> List[Dict]:
        # Twitter/X API kullanimi
        pass

# services/scraping/factory.py
def get_scraper(scraper_type: str = "selenium") -> BaseScraper:
    scrapers = {
        "selenium": SeleniumScraper,
        "api": OfficialAPIScraper,
    }
    return scrapers[scraper_type]()
```

**Effort:** Medium | **Impact:** Medium

---

## Implementasyon Yol Haritasi

```
Hafta 1-2 (ACIL):
├── P0.1: JWT Authentication
├── P0.2: CORS duzeltmesi
└── P0.3: Rate limiting

Hafta 3-4:
├── P1.4: PostgreSQL migration (Alembic)
└── P1.5: Celery async tasks

Hafta 5-8:
├── P2.6: Pagination
├── P2.7: API versioning
└── P2.8: Test coverage %50

Hafta 9-12:
├── P2.8: Test coverage %80
└── P3.9: Scraper abstraction
```

---

## Basari Metrikleri

| KPI | Mevcut | 30 Gun | 60 Gun | 90 Gun |
|-----|--------|--------|--------|--------|
| Security Score | 2/10 | 6/10 | 8/10 | 9/10 |
| API Response Time (p95) | 500ms | 300ms | 200ms | 150ms |
| Test Coverage | 0% | 30% | 60% | 80% |
| Error Rate | N/A | <5% | <2% | <1% |
| Uptime | N/A | 99% | 99.5% | 99.9% |

---

## Guvenlik Checklist

| Item | Durum | Oncelik |
|------|-------|---------|
| JWT Authentication | [ ] Yapilmadi | P0 |
| CORS Restriction | [ ] Yapilmadi | P0 |
| Rate Limiting | [ ] Yapilmadi | P0 |
| Input Validation | [~] Kismi | P1 |
| SQL Injection Protection | [x] ORM ile | - |
| HTTPS Enforcement | [ ] Yapilmadi | P1 |
| Security Headers | [ ] Yapilmadi | P1 |
| Secrets Management | [ ] Yapilmadi | P1 |
| Audit Logging | [ ] Yapilmadi | P2 |
| Dependency Scanning | [ ] Yapilmadi | P2 |

---

## Referans Dosyalar

| Dosya | Satir | Aciklama |
|-------|-------|----------|
| `backend/app/main.py` | 35-41 | CORS middleware (GUVENLI DEGIL) |
| `backend/app/main.py` | 44 | Router dahil etme |
| `backend/app/api/deps.py` | - | Dependency injection |
| `backend/app/core/config.py` | 37 | CORS origins config |
| `backend/app/core/config.py` | 40-46 | Database URL |
| `backend/app/core/database.py` | - | Database operations |
| `backend/app/api/v1/reports.py` | 28-68 | Senkron report generation |
| `backend/app/api/v1/users.py` | 17-51 | Pagination olmayan liste |

---

*Bu rapor Meclis Istihbarat Sistemi v3.0 kod tabanina dayanmaktadir.*
