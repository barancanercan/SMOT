# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Meclis Istihbarat Sistemi** (Parliament Intelligence System) v3.0 - AI-powered political intelligence SaaS platform for analyzing Turkish metropolitan municipality council members' social media activities.

**Stack**: FastAPI backend + Next.js 14 frontend (App Router) + Ollama LLM + SQLite/PostgreSQL

## Quick Commands

```bash
# Backend (port 8001)
cd backend
uvicorn app.main:app --reload --port 8001    # API server
pytest tests/ -v                              # Tests
ruff check app/                               # Lint

# Frontend (port 3000)
cd frontend
npm run dev                                   # Dev server
npm run build                                 # Production build
npm run lint                                  # Lint

# Docker
docker-compose up --build                     # Full stack

# Database
python -c "from app.core.database import init_database; init_database()"
python -c "from app.core.database import clear_report_cache; clear_report_cache()"

# Ollama
ollama pull qwen3:14b                         # Download recommended model
ollama list                                   # Check installed models
```

## Architecture

```
meclis-istihbarat/
├── backend/                      # FastAPI Backend (Python 3.10+)
│   └── app/
│       ├── api/
│       │   ├── v1/              # REST endpoints
│       │   │   ├── dashboard.py # System stats, health check
│       │   │   ├── users.py     # Councilor CRUD
│       │   │   ├── tweets.py    # Tweet queries
│       │   │   ├── analytics.py # Followers, parties, engagement
│       │   │   ├── reports.py   # Report generation (LLM)
│       │   │   └── exports.py   # Excel/PDF export
│       │   └── deps.py          # Dependency injection (get_db)
│       │
│       ├── core/                # Core modules
│       │   ├── config.py        # Pydantic Settings v2
│       │   ├── database.py      # SQLAlchemy setup, cache functions
│       │   ├── models.py        # ORM: Councilor, Tweet, ProfileHistory, ReportCache
│       │   └── db_config.py     # session_scope() context manager
│       │
│       ├── services/            # Business logic
│       │   ├── analysis/        # LLM analysis
│       │   │   ├── analyzer.py  # OllamaAnalyzer class (qwen3:14b)
│       │   │   ├── prompts.py   # Prompt templates (few-shot, chain-of-thought)
│       │   │   ├── schemas.py   # Pydantic: IntelligenceAnalysis
│       │   │   └── vector_db.py # ChromaDB integration
│       │   ├── reporting/       # Report generation
│       │   │   └── report_generator.py
│       │   └── scraping/        # X/Twitter scrapers
│       │       ├── profile_scraper.py
│       │       └── x_scraper.py
│       │
│       ├── workers/             # Background tasks
│       └── utils/               # Logger, retry decorators
│
├── frontend/                     # Next.js 14 (TypeScript)
│   └── src/
│       ├── app/                 # App Router pages
│       │   ├── page.tsx         # Dashboard
│       │   ├── users/           # User management
│       │   ├── tweets/          # Tweet archive
│       │   ├── analytics/       # Analytics views
│       │   └── reports/         # Report generation UI
│       ├── components/          # React components
│       │   ├── layout/          # Sidebar, Header
│       │   └── ui/              # Reusable UI
│       └── lib/
│           └── api.ts           # API client (fetch wrapper)
│
└── data/                         # SQLite database (meclis.db)
```

## Key Patterns

### Backend Patterns
- **Dependency Injection**: `app/api/deps.py` → `get_db()` yields database sessions
- **Session Management**: `session_scope()` context manager in `core/db_config.py`
- **Retry Decorators**: `@retry_on_db_error`, `@retry_on_scraping_error` in `utils/retry_config.py`
- **Pydantic Validation**: All API requests/responses use Pydantic models
- **LLM Response Cleanup**: `_clean_json_response()` removes JSON-LD artifacts (@context, @type)

### Analysis Framework (Green/Red/Grey)
```
Green Team: Party loyalty, leadership support, party events
Red Team:   Opposition criticism, political rivals
Grey Team:  Non-political content, local services, personal
```

### Frontend Patterns
- **API Client**: `frontend/src/lib/api.ts` - typed fetch wrapper
- **Server Components**: Default, use "use client" only when needed
- **Tailwind CSS**: Utility-first styling
- **Lucide Icons**: Icon library

## Configuration

Backend settings via environment variables or `backend/.env`:

```env
# Database
DATABASE_URL=sqlite:///./data/meclis.db

# LLM (Ollama)
OLLAMA_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3:14b          # Recommended for quality
# OLLAMA_MODEL=qwen2.5:3b       # Faster, lower quality

# API
API_PREFIX=/api/v1
DEBUG=true

# CORS
CORS_ORIGINS=http://localhost:3000
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/dashboard/overview` | System stats |
| GET | `/api/v1/users` | List councilors |
| GET | `/api/v1/users/{username}` | User detail |
| POST | `/api/v1/users` | Add user |
| DELETE | `/api/v1/users/{username}` | Remove user |
| GET | `/api/v1/tweets/{username}` | User tweets |
| GET | `/api/v1/tweets/{username}/top` | Top tweets |
| GET | `/api/v1/analytics/followers` | Follower ranking |
| GET | `/api/v1/analytics/parties` | Party stats |
| POST | `/api/v1/reports/generate` | Generate user report (LLM) |
| POST | `/api/v1/reports/party` | Generate party report |

**Swagger UI**: http://localhost:8001/docs

## LLM Analysis

### Prompt Engineering (prompts.py)
- **System Prompt**: Role-based (political intelligence analyst)
- **Few-Shot Learning**: Example analysis in prompt for quality
- **Chain-of-Thought**: Step-by-step reasoning instructions

### Analysis Output (schemas.py)
```python
class IntelligenceAnalysis(BaseModel):
    executive_summary: str      # 2-3 sentence overview
    green_summary: str          # Party loyalty analysis
    loyalty_level: str          # Dusuk/Orta/Yuksek
    red_summary: str            # Opposition criticism
    criticism_level: str        # Dusuk/Orta/Yuksek
    grey_summary: str           # Non-political content
    independent_topics: List[str]  # Topic list
```

### LLM Options (analyzer.py)
```python
"options": {
    "temperature": 0.3,      # Low creativity for consistency
    "num_predict": 4096,     # Long responses
    "num_ctx": 8192,         # Large context window
    "top_p": 0.9,
    "repeat_penalty": 1.1    # Prevent repetition
}
```

## Database Models

```python
# core/models.py
Councilor: username, name, party, district, bio, followers, following, tweet_count
Tweet: username, tweet_id, text, date, likes, retweets, replies, views, is_retweet
ProfileHistory: username, date, followers, following, tweet_count
ReportCache: username, report_type, content, created_at, expires_at
```

## Hard Constraints

1. **Free & Local**: No paid APIs. Ollama for LLM, Selenium for scraping
2. **No silent errors**: All `try-except` must log or re-raise
3. **Type hints**: Required on all Python functions
4. **PostgreSQL target**: SQLite for dev; PostgreSQL for production
5. **Turkish UI**: All user-facing text in Turkish
6. **English code**: Variables, functions, comments in English

## Common Tasks

### Add New API Endpoint
1. Create route in `backend/app/api/v1/`
2. Add to router in `backend/app/api/v1/__init__.py`
3. Add types to `frontend/src/lib/api.ts` if needed

### Modify Analysis Prompts
1. Edit `backend/app/services/analysis/prompts.py`
2. Clear cache: `clear_report_cache()`
3. Test with fresh analysis

### Add New Database Field
1. Update model in `backend/app/core/models.py`
2. Run `init_database()` (SQLite will add column)
3. Update API responses as needed

## Troubleshooting

| Issue | Solution |
|-------|----------|
| LLM returns JSON-LD | `_clean_json_response()` handles this |
| Ollama connection failed | Check `ollama serve` is running |
| CORS errors | Verify `CORS_ORIGINS` includes frontend URL |
| Database locked | Use `session_scope()` context manager |
| Scraping blocked | Update undetected-chromedriver |
