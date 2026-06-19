# Field Intel — Project Context

Internal field intelligence repository for orthopedic sales/BD team. Reps log rumors and observations; the app tags them automatically and makes them searchable.

## Stack
- Backend: Python 3.11 + FastAPI + asyncpg + Alembic
- DB: PostgreSQL 16 (FTS via tsvector/GIN)
- Frontend: React + Vite + TypeScript (PWA, mobile-first + desktop)
- AI: Anthropic Claude API (optional enrichment layer)

## Dev setup
```bash
cp .env.example .env
docker-compose up
# In a separate terminal, run migrations + seed:
docker-compose exec backend python -m alembic upgrade head
docker-compose exec backend python -m seed.seed_all
```

## Key principles
- Deterministic extraction first (jellyfish fuzzy matching) — no Claude dependency for core features
- Gazetteers are DB tables, not hardcoded constants
- Model IDs only in `backend/app/config.py`
- Claude calls always server-side, guarded by `if not settings.anthropic_api_key`
- `extract()` is a pure function — no DB calls inside it
- Timestamps shown prominently everywhere for sorting/referencing

## Run tests
```bash
cd backend && pip install -r requirements.txt
python -m pytest tests/ -v
```

## Build phases (completed order)
1. Schema + seed
2. Deterministic extractor + unit tests
3. Capture + storage API
4. Search API
5. Frontend PWA (mobile + desktop)
6. Claude enrichment fallback
7. Claude search synthesis
8. Admin gazetteer UI
