# CLAUDE.md

Technical guidance for Claude Code when working with this repository.

## Project Overview

**Meclis Istihbarat Sistemi** (Parliament Intelligence System) v3.2

AI-powered political intelligence platform for analyzing Turkish council members' social media.

**Stack**: FastAPI + Next.js 14 + OpenAI/Ollama + SQLite/PostgreSQL

**Ports**: Backend: 8000 | Frontend: 3000

## Quick Commands

```bash
# Backend
cd backend
uvicorn app.main:app --reload --port 8000
pytest tests/ -v
ruff check app/

# Frontend
cd frontend
npm run dev
npm run build
npm run lint

# Database
python -c "from app.core.database import init_database; init_database()"
python -c "from app.core.database import clear_report_cache; clear_report_cache()"

# Docker
docker-compose up --build
```

## Architecture

```
backend/
├── app/
│   ├── api/v1/              # REST endpoints
│   │   ├── dashboard.py     # Stats, health
│   │   ├── users.py         # Councilor CRUD (add/bulk/delete)
│   │   ├── tweets.py        # Tweet queries
│   │   ├── analytics.py     # Followers, parties, comparison
│   │   ├── reports.py       # LLM reports (user/party/multi)
│   │   └── exports.py       # Excel export
│   ├── core/
│   │   ├── config.py        # Settings
│   │   ├── constants.py     # Party normalization (Turkish chars)
│   │   ├── database.py      # SQLAlchemy, cache
│   │   ├── models.py        # ORM models
│   │   └── security.py      # Auth
│   ├── services/
│   │   ├── analysis/        # LLM
│   │   │   ├── analyzer.py  # TweetAnalyzer
│   │   │   ├── prompts.py   # Templates (comparison prompt)
│   │   │   └── schemas.py   # Pydantic
│   │   ├── reporting/
│   │   │   └── report_generator.py
│   │   └── scraping/        # X scrapers
│   └── utils/               # Logger, retry
├── scripts/                 # Utility scripts
└── tests/

frontend/
├── src/
│   ├── app/                 # Pages
│   │   ├── page.tsx         # Dashboard
│   │   ├── analytics/       # Followers, parties
│   │   ├── reports/         # User/party/multi reports
│   │   ├── comparison/      # User comparison (NEW)
│   │   ├── users/           # User management (NEW)
│   │   ├── tweets/          # Tweet search
│   │   └── system/          # System status
│   ├── components/
│   │   ├── charts/          # Recharts
│   │   ├── layout/          # Sidebar
│   │   └── ui/              # Components
│   └── lib/
│       └── api.ts           # API client
└── public/                  # Assets
```

## Key Patterns

### Backend

- **Dependency Injection**: `get_db()` in `api/deps.py`
- **Session Management**: `session_scope()` context manager
- **Party Normalization**: `normalize_party_name()` with Turkish char support
- **LLM Cleanup**: `_clean_json_response()` removes JSON-LD artifacts

### Analysis Framework

```
Green Team: Party loyalty, leadership support
Red Team:   Opposition criticism, rivals
Grey Team:  Non-political, local services
```

### Frontend

- **API Client**: `lib/api.ts` - typed fetch wrapper
- **Server Components**: Default, "use client" when needed
- **Dark Theme**: All components use dark colors
- **Recharts**: Custom dark tooltips
- **Turkish UI**: All text in Turkish

## Configuration

```env
# LLM Provider
LLM_PROVIDER=openai

# OpenAI (Recommended)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_TIMEOUT=60

# Ollama (Fallback)
OLLAMA_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:3b

# Database
DATABASE_URL=sqlite:///./data/meclis.db

# API
API_PREFIX=/api/v1
DEBUG=true
CORS_ORIGINS=http://localhost:3000
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/dashboard/overview` | System stats |
| GET | `/api/v1/users` | List users |
| GET | `/api/v1/users/{username}` | User detail |
| POST | `/api/v1/users` | Add user |
| POST | `/api/v1/users/bulk` | Bulk add users |
| DELETE | `/api/v1/users/{username}` | Remove user (cascade) |
| GET | `/api/v1/tweets/{username}` | User tweets |
| GET | `/api/v1/analytics/followers` | Follower ranking |
| GET | `/api/v1/analytics/parties` | Party stats |
| POST | `/api/v1/analytics/compare` | Compare 2-10 users |
| POST | `/api/v1/analytics/compare/llm` | Compare with AI |
| POST | `/api/v1/reports/generate` | User report |
| POST | `/api/v1/reports/party` | Party report (with LLM) |
| POST | `/api/v1/reports/multi` | Multi-user report |
| GET | `/api/v1/exports/followers/excel` | Excel export |

**Swagger**: http://localhost:8000/docs

## LLM Analysis

### OpenAI (Recommended)
- Model: gpt-3.5-turbo
- Speed: 3-5 seconds
- Cost: ~$0.002/analysis

### Ollama (Fallback)
- Model: qwen2.5:3b
- Speed: 15-60 seconds
- Cost: Free

### Analysis Schema

```python
class IntelligenceAnalysis(BaseModel):
    executive_summary: str
    green_summary: str
    loyalty_level: str       # Dusuk/Orta/Yuksek
    red_summary: str
    criticism_level: str     # Dusuk/Orta/Yuksek
    grey_summary: str
    independent_topics: List[str]
    confidence_score: float  # 0.0-1.0
```

## Database Models

```python
Councilor: username, name, party, district, bio
Tweet: username, tweet_id, text, date, likes, retweets, is_retweet
ProfileHistory: username, date, followers, following
ReportCache: username, report_type, content, expires_at
```

## Hard Constraints

1. **LLM**: OpenAI preferred, Ollama fallback
2. **No silent errors**: Log or re-raise
3. **Type hints**: Required on all functions
4. **Turkish UI**: All user-facing text in Turkish
5. **English code**: Variables in English
6. **Dark theme**: All UI components
7. **Minimum 1 tweet**: For individual LLM analysis

## Common Tasks

### Add API Endpoint
1. Create route in `backend/app/api/v1/`
2. Add to router in `__init__.py`
3. Update `frontend/src/lib/api.ts`

### Modify Prompts
1. Edit `backend/app/services/analysis/prompts.py`
2. Clear cache: `clear_report_cache()`
3. Test fresh analysis

### Add Database Field
1. Update `backend/app/core/models.py`
2. Run `init_database()`
3. Update API responses

## Troubleshooting

| Issue | Solution |
|-------|----------|
| OpenAI error | Check API key in .env |
| Ollama failed | Run `ollama serve` |
| CORS error | Check CORS_ORIGINS |
| Old report | Clear report cache |
| User not analyzed | Check if has >= 1 tweet |

### Cache Management

```bash
# Clear report cache
python -c "from app.core.database import clear_report_cache; clear_report_cache()"

# Clear Python cache (PowerShell)
Get-ChildItem -Path backend -Recurse -Directory -Filter '__pycache__' | Remove-Item -Recurse -Force

# Clear Python cache (Bash)
find backend -type d -name '__pycache__' -exec rm -rf {} +
```

## File Locations

| Feature | File |
|---------|------|
| LLM Analyzer | `backend/app/services/analysis/analyzer.py` |
| Prompts | `backend/app/services/analysis/prompts.py` |
| Party Normalization | `backend/app/core/constants.py` |
| Report Generator | `backend/app/services/reporting/report_generator.py` |
| API Client | `frontend/src/lib/api.ts` |
| Dashboard | `frontend/src/app/page.tsx` |
| Reports Page | `frontend/src/app/reports/page.tsx` |
| Comparison Page | `frontend/src/app/comparison/page.tsx` |
| Users Page | `frontend/src/app/users/page.tsx` |
| System Page | `frontend/src/app/system/page.tsx` |
| Charts | `frontend/src/components/charts/` |
