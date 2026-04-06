# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Meclis Istihbarat Sistemi** (Parliament Intelligence System) v6.0

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
pytest tests/test_chat.py::test_query -v  # Single test
ruff check app/

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

# Chat Cache (clear after code changes)
curl -X POST "http://localhost:8000/api/v1/chat/cache/clear"

# Scraping
cd scrapers
python batch_parallel.py             # Parallel batch scraping (Twitter + Instagram)
python batch_twitter.py              # Twitter-only batch scraping
python batch_instagram.py            # Instagram-only batch scraping
python scheduler.py                  # Scheduled scraping (APScheduler)
cd ../scripts
python daily_sync.py                 # Daily sync script

# Instagram Scraping (API-based)
cd backend
python scripts/update_instagram_engagement.py  # Fix 0-like posts
python -m app.services.scraping.instagram_api_scraper --users USERNAME --max-posts 50

# Docker
docker-compose up --build
```

## Architecture

### Backend Structure

```
backend/app/
├── api/v1/              # REST endpoints (dashboard, users, tweets, analytics, reports, chat, exports, auth, metrics)
├── core/                # Config, database, models, constants (party normalization), security
├── services/
│   ├── agents/          # A-RAG Agent System (meta_agent orchestrates retriever, classifier, summarizer, reranker)
│   ├── analysis/        # LLM analysis (TweetAnalyzer, prompts, schemas, chat_prompts)
│   ├── chat/            # Chat with Tweets v6 - Modern RAG System
│   │   ├── chat_handler.py      # Main orchestrator with ensemble intent detection
│   │   ├── semantic_retriever.py # Embedding-based search with sentence-transformers
│   │   ├── query_reasoner.py    # Political context understanding (GPT-4o)
│   │   ├── turkish_nlp.py       # Turkish NLP (stemming, synonyms, stopwords)
│   │   ├── intent_parser.py     # Rule-based intent parsing
│   │   ├── response_generator.py # LLM response generation
│   │   ├── session_manager.py   # Chat session persistence
│   │   └── query_cache.py       # TTL-based caching (30min responses, 1hr intents)
│   ├── reporting/       # Report generation
│   └── scraping/        # Instagram scrapers (selenium legacy, instaloader API recommended)
└── utils/               # Logger, retry helpers

scrapers/
├── batch_parallel.py    # Parallel batch scraping (Twitter + Instagram concurrent)
├── batch_twitter.py     # Twitter batch scraper (CDP-based)
├── batch_instagram.py   # Instagram batch scraper
├── twitter_scraper.py   # Core Twitter scraper (CDP/Selenium)
├── cdp_browser.py       # Chrome DevTools Protocol browser manager
├── migrate_schema.py    # Idempotent DB schema migration (adds missing columns)
└── scheduler.py         # APScheduler-based scraping scheduler

scripts/
└── daily_sync.py        # Daily sync: scrape all platforms + update stats
```

### Frontend Structure

```
frontend/src/
├── app/                 # Next.js pages (dashboard, analytics, reports, chat, comparison, users, tweets, instagram, system)
├── components/          # UI components (charts/, layout/, ui/)
└── lib/api.ts           # Typed API client
```

### Key Patterns

- **Dependency Injection**: `get_db()` in `api/deps.py`
- **Session Management**: `session_scope()` context manager
- **Party Normalization**: `normalize_party_name()` handles Turkish chars (AK Parti variants, etc.)
- **LLM Cleanup**: `_clean_json_response()` removes JSON-LD artifacts
- **API Client**: `lib/api.ts` - typed fetch wrapper with error handling

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

**Important Design Decisions:**
- Economy topic ≠ criticism (explicit keywords required)
- Sentiment filter only for explicit criticism queries
- Tweets sorted by engagement (likes + retweets)

## Configuration

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-3.5-turbo
OLLAMA_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:3b
DATABASE_URL=sqlite:///./data/meclis.db
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
| Instagram 0 likes | Run `python scripts/update_instagram_engagement.py` |
| Instagram 403 | Rate limited - wait 5 min, script auto-retries |
| Chat old response | Clear chat cache: `POST /api/v1/chat/cache/clear` |
| Chat wrong results | Restart server to reload code changes |
| DB malformed schema | DB corrupted — restore from git: `git show <commit>:data/meclis.db > data/meclis.db` then re-run migration |
| Migration emoji error | Windows cp1254 encoding — use `PYTHONIOENCODING=utf-8 python scrapers/migrate_schema.py` |

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
