# Changelog

## 2026-07-08 — Deploy prep + evaluation toolkit

### Deployment
- Added root `DEPLOY.md` with end-to-end deploy checklist and env var reference
- Added `railway.toml` for Railway deployment defaults (start command + health check)
- Expanded `backend/.env.example` and `frontend/.env.example` with production guidance
- Added `backend/scripts/seed_catalog.py` to seed initial books catalog
- Added production runtime validation/warnings in `backend/app/core/config.py`

### ML evaluation
- Added `backend/scripts/calc_recommender_stats.py` for offline recommender metrics:
  - `Precision@k`, `Recall@k`, `HitRate@k`, `MRR@k`
  - latency `mean`, `p50`, `p95`
- Added `backend/eval/relevance_labels.example.json` for labeled relevance inputs
- Added embeddings retriever mode in `backend/app/services/recommender.py`:
  - `RECOMMENDER_MODE=tfidf|embeddings`
  - `EMBEDDING_MODEL` (default: `sentence-transformers/all-MiniLM-L6-v2`)
- Added `backend/requirements-embeddings.txt` (`transformers`, `torch`) for embeddings setup
- Added `--mode` and `--books-file` options to stats script for embeddings and offline runs
- Updated ML and backend docs with usage instructions

---

## 2026-07-04 — Phases 2–4

### ML (Phase 2)
- Hybrid recommender: 0.7 content + 0.3 normalized rating
- TF-IDF uses title + description
- Global model retrains after admin `POST /books`
- HF API timeout; 503 when key missing

### Engineering (Phase 3)
- MongoDB indexes on startup
- Admin-only `POST /books` and `POST /train` (`is_admin` on user doc)
- Invalid JWT user id returns 401
- `backend/tests/` pytest suite
- `frontend` Vitest + GitHub Actions CI

### UX (Phase 4)
- Welcome message in header
- Delete confirmation
- Catalog search keeps list visible while updating
- Toast `aria-live`, delete error toasts
- AbortController on catalog fetch

---

## 2026-07-04 — Phase 0 + Phase 1

### Documentation
- Added `AGENTS.md`, `handoff.md`, `docs/` (9 files)
- Rewrote root, backend, and frontend READMEs

### Deploy readiness
- `GET /health` with `recommender_ready`
- `backend/Procfile` (Gunicorn, 1 worker)
- Pinned `requirements.txt`
- `backend/.env.example`, `frontend/.env.example`

### Bug fixes
- Catalog search debounce loop and duplicate API loads
- `res.ok` checks on catalog, ratings, recommendations
- `BookCard` respects `showDescription`
- `AiSuggestionRequest` Pydantic validation
- Regex-escaped catalog search
- Placeholder image URL (`placehold.co` instead of missing `/placeholder.jpg`)
- `api.js` graceful handling when `VITE_API_BASE_URL` unset
- HF recommender returns empty list when `HF_API_KEY` missing
- AI endpoint wraps errors as 502

### UI
- Page title set to "Library AI"
- Configuration screen when env missing

---

## Prior commits (summary)

- JWT secret handling and runtime config validation
- MongoDB connection error reporting on startup
- Frontend lint and hook warning fixes
- Full-stack security, architecture, UX improvements

See git log for details.
