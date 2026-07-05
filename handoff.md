# handoff.md — LLM / developer handoff

**Last updated:** 2026-07-04  
**Project:** Library AI (`lib_recc`) — personal library + book recommendations  
**GitHub:** https://github.com/anik05169/lib_recc

---

## What this project is

A portfolio-grade full-stack app for browsing a book catalog, building a personal library, rating books, getting TF-IDF similar-book recommendations (global + per-user), and AI book suggestions via HuggingFace Llama-3.

**Stack:** React 19, Vite, FastAPI, MongoDB Atlas, custom TF-IDF (no scikit-learn), HuggingFace Inference API.

---

## What was completed (Phases 0–4)

### Phase 0 — Documentation
- `AGENTS.md`, `handoff.md`, `docs/*`, READMEs

### Phase 1 — Deploy readiness
- `GET /health`, `Procfile`, `render.yaml`, pinned deps, `.env.example` files
- Placeholder images, graceful `api.js` config

### Phase 2 — ML
- TF-IDF on title + description
- Hybrid scoring: 0.7 cosine + 0.3 normalized rating
- Retrain global model after `POST /books`
- HF timeout (30s), 503 when `HF_API_KEY` missing
- Fresh ratings map on recommend + after rate

### Phase 3 — Engineering
- MongoDB indexes on startup (`ensure_indexes`)
- `require_admin` for `POST /books` and `POST /train`
- `InvalidId` → 401 via `get_user_by_id`
- `pytest` tests + Vitest + GitHub Actions CI

### Phase 4 — UX
- Welcome message from `/auth/me`
- Delete confirmation dialog
- Catalog keeps books visible during search refresh
- `aria-live` toasts, delete error toasts
- AbortController on catalog fetch

### Not done yet (you deploy manually)
- Backend host on Render/Railway with env vars
- Vercel `VITE_API_BASE_URL` pointing to deployed API
- Backend `ALLOWED_ORIGINS` = your Vercel URL
- Live demo URLs in README (placeholders remain until you deploy)

---

## How to run locally

```bash
# Backend
cd backend
python -m venv venv && venv\Scripts\activate   # Windows
pip install -r requirements.txt
copy .env.example .env   # fill MONGODB_URI, JWT_SECRET
uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend
npm install
copy .env.example .env   # VITE_API_BASE_URL=http://localhost:8000
npm run dev
```

Open http://localhost:5173 — register, login, explore catalog.

---

## Architecture (one paragraph)

JWT auth (`localStorage` token). `App.jsx` holds all state. Two tabs: **Catalog** (paginated `GET /books`, global `GET /recommend/{id}`) and **My Collection** (user library, ratings, per-user `GET /user/recommend/{id}`, AI suggest via `POST /books/ai-suggest-new`). MongoDB database `library_db` with collections `users`, `books`, `user_books`, `ratings`. Recommender trains TF-IDF + cosine similarity in memory at startup and on library changes.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for diagrams.

---

## Hard constraints (do not violate)

| Constraint | Reason |
|------------|--------|
| Gunicorn `-w 1` | In-memory recommender not shared across workers |
| Don't scale workers without Redis/shared model | Each worker has its own `_books_df` |
| `JWT_SECRET` required at startup | `validate_runtime_config()` fails fast |
| `VITE_API_BASE_URL` baked at Vite build | Must set in Vercel before build |
| CORS must include frontend origin | Default is localhost only |

---

## API quick reference

| Endpoint | Auth | Purpose |
|----------|------|---------|
| `GET /health` | No | Deploy health + `recommender_ready` |
| `POST /auth/register`, `/auth/login` | No | Account + JWT |
| `GET /auth/me` | JWT | Validate token |
| `GET /books` | No | Paginated catalog |
| `GET /recommend/{book_id}` | No | Global similar books |
| `POST /books/ai-suggest-new` | JWT | HF AI suggestions |
| `GET /user/library` | JWT | User's books |
| `POST /user/add-from-catalog` | JWT | Copy catalog book to library |
| `POST /user/add-custom-book` | JWT | Private custom book |
| `GET /user/recommend/{book_id}` | JWT | Similar within user's library |
| `POST /ratings` | JWT | Rate library book 1–5 |
| `GET /ratings/average` | No | Aggregate ratings |

Full detail: [docs/API.md](docs/API.md)

---

## Frontend structure

```
App.jsx          — all state, fetch, auth, toasts
views/
  CatalogView    — search (debounced), pagination, collect book
  LibraryView    — AI suggest, add custom, UserLibrary
components/
  Login, Register, BookCard, AiBookSuggest, UserLibrary, AddCustomBook
api.js           — VITE_API_BASE_URL, PLACEHOLDER_IMAGE_URL
```

Unused backend endpoints (no UI): `POST /books`, `POST /train`, `GET /user/library/ids`

Detail: [docs/FRONTEND.md](docs/FRONTEND.md)

---

## Backend structure

```
backend/app/
  main.py           — FastAPI app, /health, CORS, lifespan
  startup.py        — train global recommender in background thread
  core/auth.py      — JWT, pbkdf2_sha256 passwords
  core/config.py    — CORS, JWT secret validation
  db/mongo.py       — pymongo → library_db
  routes/           — auth, books, users, ratings
  services/
    recommender.py  — TF-IDF + cosine (global + per-user)
    hf_recommender.py — HuggingFace chat completions
```

Detail: [docs/BACKEND.md](docs/BACKEND.md)

---

## Known open issues (priority order)

See [docs/KNOWN_ISSUES.md](docs/KNOWN_ISSUES.md). Top items:

1. **No tests / CI** — Phase 3
2. **No MongoDB indexes** — duplicate `book_id` / email risk — Phase 3
3. **Ratings not used in recommender** — Phase 2 hybrid scoring
4. **Global model stale after `POST /books`** — Phase 2
5. **Any authenticated user can `POST /books` and `POST /train`** — Phase 3 security
6. **Delete library book — no error toast on failure** — Phase 4
7. **Monolithic `App.jsx`** — defer unless refactoring

---

## Recommended next work

- Deploy backend (Render) + frontend (Vercel) — see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- Set `is_admin: true` on your MongoDB user for catalog admin endpoints
- Add live demo URLs to README
- Optional: screenshots/GIF for portfolio

~~Phase 2–4 implementation~~ — completed in codebase; deploy when ready.

---

## Deploy checklist (manual)

1. **Render/Railway:** Root dir `backend`, start via `Procfile`, set `MONGODB_URI`, `JWT_SECRET`, `ALLOWED_ORIGINS`
2. **Vercel:** Root dir `frontend`, set `VITE_API_BASE_URL` to Render URL, redeploy
3. Hit `GET https://your-api/health` — `recommender_ready: true` after ~10s
4. Update README live demo links

Full guide: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

---

## Files to read first for common tasks

| Goal | Read |
|------|------|
| Orient quickly | This file + `AGENTS.md` |
| Add endpoint | `docs/API.md`, relevant `backend/app/routes/*.py` |
| Fix frontend fetch | `frontend/src/App.jsx`, `frontend/src/api.js` |
| Change ML | `backend/app/services/recommender.py`, `docs/ML.md` |
| Deploy issue | `docs/DEPLOYMENT.md`, `backend/app/core/config.py` |

---

## Maintenance rule

When you change behavior, update the matching doc in the same commit:
- API change → `docs/API.md`
- Schema/index → `docs/DATABASE.md`
- ML logic → `docs/ML.md`
- Fixed bug → strikethrough in `docs/KNOWN_ISSUES.md` + `docs/CHANGELOG.md`
