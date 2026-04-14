# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**S.A.M - Stratejik Analiz Merkezi** (Strategic Analysis Center) v6.0

AI-powered political intelligence platform analyzing Turkish council members' social media (Twitter + Instagram).

**Stack**: FastAPI + Next.js 14 + OpenAI/Ollama + SQLite/PostgreSQL + Sentence Transformers

**Ports**: Backend: 8000 | Frontend: 3000

## Quick Commands

```bash
# Backend
cd backend
uvicorn app.main:app --reload --port 8000
pytest tests/ -v                    # All tests
pytest tests/test_chat.py -v        # Single test file
ruff check app/                     # Lint check

# Frontend
cd frontend
npm run dev
npm run build
npm run lint
npm run type-check

# Database
python -c "from app.core.database import init_database; init_database()"
python -c "from app.core.database import clear_report_cache; clear_report_cache()"

# Schema Migration (idempotent - adds missing columns)
PYTHONIOENCODING=utf-8 python scrapers/migrate_schema.py

# Chat Cache (clear after code changes) — PowerShell:
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/chat/cache/clear" -Method POST

# Scraping
cd scrapers
python batch_parallel.py             # Parallel batch scraping (Twitter + Instagram)
python batch_twitter.py              # Twitter-only batch scraping
python batch_instagram.py            # Instagram-only batch scraping
python scheduler.py                  # Scheduled scraping (APScheduler)
cd ../scripts
python daily_sync.py                 # Daily sync script

# Instagram Engagement Fix
cd backend
python scripts/update_instagram_engagement.py              # Fix 0-like posts
python scripts/update_instagram_engagement.py --suspicious # Fix suspicious ratios (high comments, low likes)
python scripts/update_instagram_engagement.py --all        # Both modes

# Start Brave for CDP scraping
python scripts/start_brave.py        # Launches Brave on ports 9222 (Twitter) + 9226 (Instagram)

# Docker
docker-compose up --build
```

## Architecture

### Directory Structure

```
SAM/
├── backend/             # FastAPI Python backend
├── frontend/            # Next.js 14 TypeScript frontend
├── scrapers/            # CDP-based standalone scrapers
├── scripts/             # Utility scripts (start_brave.py, daily_sync.py)
├── tests/               # Test suite
│   ├── scrapers/        # CDP scraper tests (test_instagram_3.py, test_twitter_3.py)
│   └── test_scrapers.py # Mock-mode scraper tests
├── docs/                # Documentation & screenshots
├── data/                # Root-level data files
└── .github/workflows/   # CI/CD (backend-ci.yml, frontend-ci.yml)
```

### Backend Structure

```
backend/app/
├── api/v1/              # REST endpoints (dashboard, users, tweets, analytics, reports, chat, exports, auth, metrics)
├── core/                # Config, database, models, constants (party normalization), security
├── services/
│   ├── agents/          # A-RAG Agent System (meta_agent orchestrates retriever, classifier, summarizer, reranker)
│   ├── analysis/        # LLM analysis (TweetAnalyzer, prompts, schemas, chat_prompts)
│   ├── chat/            # Chat with Tweets v6 - Modern RAG System
│   │   ├── chat_handler.py       # Main orchestrator with ensemble intent detection
│   │   ├── semantic_retriever.py # Embedding-based search with sentence-transformers
│   │   ├── query_reasoner.py     # Political context understanding (GPT-4o)
│   │   ├── turkish_nlp.py        # Turkish NLP (stemming, synonyms, stopwords)
│   │   ├── intent_parser.py      # Rule-based intent parsing
│   │   ├── response_generator.py # LLM response generation + citation link injection
│   │   ├── session_manager.py    # Chat session persistence
│   │   └── query_cache.py        # TTL-based caching (30min responses, 1hr intents)
│   ├── reporting/       # Report generation
│   └── scraping/        # Instagram scrapers (selenium legacy, instaloader API recommended)
└── utils/               # Logger, retry helpers

scrapers/
├── batch_parallel.py    # Parallel batch scraping (Twitter + Instagram concurrent)
├── batch_twitter.py     # Twitter batch scraper (CDP-based)
├── batch_instagram.py   # Instagram batch scraper (CDP port 9226)
├── twitter_scraper.py   # Core Twitter scraper (CDP/Selenium)
├── cdp_browser.py       # Chrome DevTools Protocol browser manager
├── migrate_schema.py    # Idempotent DB schema migration (adds missing columns)
└── scheduler.py         # APScheduler-based scraping scheduler

scripts/
├── start_brave.py       # Launch Brave on CDP ports 9222 (Twitter) + 9226 (Instagram)
└── daily_sync.py        # Daily sync: scrape all platforms + update stats
```

### Frontend Structure

```
frontend/src/
├── app/                 # Next.js pages (dashboard, analytics, reports, chat, comparison, users, tweets, instagram)
├── components/          # UI components (charts/, layout/, ui/)
└── lib/api.ts           # Typed API client
```

### Key Patterns

- **Dependency Injection**: `get_db()` in `api/deps.py`
- **Session Management**: `session_scope()` context manager
- **Party Normalization**: `normalize_party_name()` handles Turkish chars (AK Parti variants, etc.)
- **LLM Cleanup**: `_clean_json_response()` removes JSON-LD artifacts
- **API Client**: `lib/api.ts` - typed fetch wrapper with error handling
- **Citation Links**: `_add_citation_links()` in `response_generator.py` converts `[N]` to markdown links

### Analysis Framework (Green-Red-Grey Teams)

```
Green Team: Party loyalty, leadership support → loyalty_level (Dusuk/Orta/Yuksek)
Red Team:   Opposition criticism, rivals → criticism_level (Dusuk/Orta/Yuksek)
Grey Team:  Non-political, local services → independent_topics list
```

### Multi-Platform LLM Analysis

Three analyzer methods based on platform selection:
- `analyze_intelligence()` - Twitter only
- `analyze_instagram()` - Instagram only
- `analyze_multi_platform()` - Both platforms combined

### Chat with Tweets v6 Architecture

Modern RAG pipeline based on 2026 best practices:

```
User Query → QueryReasoner (GPT-4o) → IntentParser (Rules) → SemanticRetriever (Embeddings) → ResponseGenerator
```

**Key Components:**
- **Ensemble Intent Detection**: Keywords (50%) + Rules (30%) + LLM (20%) - LLM least trusted
- **Semantic Retrieval**: sentence-transformers for Turkish (paraphrase-multilingual-MiniLM-L12-v2)
- **Topic-First Search**: Detect topic → Get keywords → Determine intent (not reverse)
- **Criticism Concepts**: hükümet_eleştirisi, chp_eleştirisi (separate from topics)
- **Query Cache**: 30min TTL for responses, 1hr for intents
- **Citation Links**: `[N]` references in responses automatically link to tweet/post URLs

**Important Design Decisions:**
- Economy topic ≠ criticism (explicit keywords required)
- Sentiment filter only for explicit criticism queries
- Tweets sorted by engagement (likes + retweets)

### Instagram Scraping — Known Behavior

The CDP scraper (`batch_instagram.py`) sometimes captures low like counts (1-3) when the SPA hasn't fully rendered. Two safeguards are in place:

1. **`save_post_to_db`**: Uses `MAX(new, existing)` for likes — never overwrites a higher count
2. **Retry logic**: Waits for `likes > 5` or `timestamp present` before accepting page data
3. **Engagement updater**: Run `--suspicious` flag to fix posts where `comments > likes * 10`

## Configuration

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-3.5-turbo
OLLAMA_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:3b
DATABASE_URL=sqlite:///./data/sam.db
CORS_ORIGINS=http://localhost:3000
```

## Database Models

```python
Councilor: username, name, party, district, bio, followers_count, following_count,
           tweet_count_total, listed_count, twitter_updated_at,
           instagram_followers, instagram_following, instagram_posts_count, instagram_updated_at
Tweet: username, tweet_id, text, date, likes, retweets, is_retweet,
       hashtags, mentions, media_urls, media_count, quote_tweet_id, conversation_id, source, bookmarks
InstagramPost: username, post_id, caption, post_type, likes, comments, post_url, timestamp,
               video_views, saves, shares, hashtags, mentions, shortcode, media_count, location
ProfileHistory: username, date, followers, following
ReportCache: username, report_type, content, expires_at
ChatSession: id (UUID), title, platform, party_filter, created_at, updated_at
ChatMessage: id, session_id (FK), role, content, metadata (JSON), created_at
```

## Hard Constraints

1. **LLM**: OpenAI preferred, Ollama fallback
2. **No silent errors**: Log or re-raise
3. **Type hints**: Required on all functions
4. **Turkish UI**: All user-facing text in Turkish
5. **English code**: Variables in English
6. **Dark theme**: All UI components
7. **Minimum 1 tweet**: Required for individual LLM analysis

## Common Tasks

### Add API Endpoint
1. Create route in `backend/app/api/v1/`
2. Import in `__init__.py` and add to router in `router.py`
3. Update `frontend/src/lib/api.ts`

### Modify Prompts
1. Edit `backend/app/services/analysis/prompts.py` (or `chat_prompts.py` for chat)
2. Clear cache: `clear_report_cache()`
3. Test fresh analysis

### Add Database Field
1. Update `backend/app/core/models.py`
2. Add column to `scrapers/migrate_schema.py` (idempotent migration)
3. Run `PYTHONIOENCODING=utf-8 python scrapers/migrate_schema.py`
4. Update API responses

## Troubleshooting

| Issue | Solution |
|-------|----------|
| OpenAI error | Check API key in .env |
| Ollama failed | Run `ollama serve` |
| CORS error | Check CORS_ORIGINS in .env |
| Old report | Clear report cache |
| User not analyzed | Needs >= 1 tweet |
| Instagram wrong likes | Run `python scripts/update_instagram_engagement.py --suspicious` |
| Instagram 403 | Rate limited - wait 5 min, script auto-retries |
| Chat old response | Restart backend server (in-memory cache clears on restart) |
| Chat wrong results | Restart server to reload code changes |
| DB malformed schema | DB corrupted — restore from git: `git show <commit>:data/sam.db > data/sam.db` then re-run migration |
| Migration emoji error | Windows cp1254 encoding — use `PYTHONIOENCODING=utf-8 python scrapers/migrate_schema.py` |
| curl not working (Windows) | Use `Invoke-WebRequest -Uri "..." -Method POST` instead of `curl -X POST` |

## API Reference

Swagger UI: http://localhost:8000/docs

Key endpoints:
- `GET /api/v1/health` - Health check
- `GET/POST /api/v1/users` - User CRUD
- `POST /api/v1/reports/generate` - User report (platform-aware)
- `POST /api/v1/reports/party` - Party report
- `POST /api/v1/chat/query` - Chat with tweets (semantic search)
- `POST /api/v1/chat/cache/clear` - Clear chat query cache
- `GET /api/v1/chat/sessions` - List chat sessions
- `POST /api/v1/chat/sessions` - Create new session
- `POST /api/v1/analytics/compare/llm` - AI comparison
- `GET /api/v1/analytics/tweets/top` - Top tweets (returns tweet_url)
- `GET /api/v1/analytics/posts/top` - Top Instagram posts (returns post_url)
