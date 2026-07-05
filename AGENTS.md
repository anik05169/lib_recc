# AGENTS.md — AI / Cursor entry point

Read this file first before editing `lib_recc`.

## 30-second summary

**Library AI** is a full-stack book library app: React 19 + Vite frontend, FastAPI + MongoDB backend, dual TF-IDF recommenders (global catalog + per-user library), 1–5 star ratings, and HuggingFace Llama-3 AI book suggestions.

Repo: `anik05169/lib_recc` on GitHub. Frontend targets Vercel; backend targets Render/Railway.

## Documentation index

| Doc | When to read |
|-----|--------------|
| [handoff.md](handoff.md) | **Give this to another LLM** — current state, constraints, next phases |
| [docs/INDEX.md](docs/INDEX.md) | Hub linking all docs |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design, auth flow, data split |
| [docs/API.md](docs/API.md) | Every endpoint + frontend caller |
| [docs/DATABASE.md](docs/DATABASE.md) | MongoDB collections and schema |
| [docs/ML.md](docs/ML.md) | Recommender + HF integration |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Env vars, Procfile, Vercel, CORS |
| [docs/FRONTEND.md](docs/FRONTEND.md) | Components, `App.jsx` state |
| [docs/BACKEND.md](docs/BACKEND.md) | Modules, routes, startup |
| [docs/KNOWN_ISSUES.md](docs/KNOWN_ISSUES.md) | Open bugs and tech debt |
| [docs/CHANGELOG.md](docs/CHANGELOG.md) | What changed and when |

## Critical files

| Area | Files |
|------|-------|
| Frontend hub | `frontend/src/App.jsx` |
| API config | `frontend/src/api.js` |
| Auth UI | `frontend/src/components/Login.jsx`, `Register.jsx` |
| Backend entry | `backend/app/main.py` |
| Recommender | `backend/app/services/recommender.py` |
| AI suggest | `backend/app/services/hf_recommender.py` |
| Auth | `backend/app/core/auth.py` |
| MongoDB | `backend/app/db/mongo.py` |

## Environment (required)

**Backend** (`backend/.env`): `MONGODB_URI`, `JWT_SECRET`  
**Frontend** (`frontend/.env`): `VITE_API_BASE_URL`  
**Optional:** `HF_API_KEY`, `ALLOWED_ORIGINS`, `VITE_GOOGLE_BOOKS_API_KEY`

See `backend/.env.example` and `frontend/.env.example`.

## Do NOT break these constraints

1. **Single Gunicorn worker** — recommender state lives in process memory (`backend/Procfile` uses `-w 1`). Multiple workers = stale/empty models.
2. **In-memory models** — global `_books_df` and per-user `_user_models` reset on restart. Training runs in a daemon thread at startup (`backend/app/startup.py`).
3. **Login required for UI** — catalog is only shown after JWT login (API catalog endpoints are public).
4. **Custom books stay private** — `POST /user/add-custom-book` does not add to global `books` collection.
5. **Ratings require library membership** — enforced in `backend/app/routes/ratings.py`.

## Common tasks

| Task | Start here |
|------|------------|
| Fix deploy / CORS | `docs/DEPLOYMENT.md` |
| Add API endpoint | `docs/API.md`, `backend/app/routes/` |
| Change recommender | `docs/ML.md`, `backend/app/services/recommender.py` |
| Frontend bug | `docs/FRONTEND.md`, `frontend/src/App.jsx` |
| New env var | Both `.env.example` files + `docs/DEPLOYMENT.md` |

## Phases still open (see handoff.md)

- Phase 2: ML improvements (title+description TF-IDF, hybrid ratings)
- Phase 3: Tests, CI, MongoDB indexes
- Phase 4: UX polish (delete confirm, header name, search flicker)
