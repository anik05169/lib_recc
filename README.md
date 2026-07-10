# Library AI

Full-stack personal library with **dual TF-IDF recommenders** and **HuggingFace AI** book suggestions.

**React 19 · FastAPI · MongoDB · Custom ML (no scikit-learn)**

---

## Live demo

> Update these after deploying — follow [DEPLOY.md](DEPLOY.md) (step-by-step checklist)

| | URL |
|---|-----|
| Frontend | `https://your-app.vercel.app` |
| API | `https://your-api.onrender.com` |
| Health | `https://your-api.onrender.com/health` |

---

## Features

- JWT auth (register / login)
- Paginated book catalog with search
- Personal library (collect from catalog or add custom books)
- 1–5 star ratings with aggregate scores
- **Global** similar-book recommendations (catalog TF-IDF or embeddings)
- **Per-user** similar-book recommendations (library TF-IDF or embeddings)
- AI assistant — natural language → 3 book suggestions (Llama-3 via HuggingFace)
- Offline recommender evaluation toolkit (`Precision@k`, `Recall@k`, `HitRate@k`, `MRR@k`, `p50/p95` latency)

---

## Quick start

```bash
# Backend
cd backend && pip install -r requirements.txt
cp .env.example .env          # set MONGODB_URI, JWT_SECRET
uvicorn app.main:app --reload

# Frontend
cd frontend && npm install
cp .env.example .env          # VITE_API_BASE_URL=http://localhost:8000
npm run dev
```

Open http://localhost:5173

---

## Documentation

| Doc | Purpose |
|-----|---------|
| [handoff.md](handoff.md) | **Give to another LLM** — full context handoff |
| [AGENTS.md](AGENTS.md) | Cursor / AI entry point |
| [DEPLOY.md](DEPLOY.md) | **Deploy checklist + all env vars** |
| [docs/INDEX.md](docs/INDEX.md) | Documentation hub |

### Recommender stats (resume metrics)

```bash
cd backend
python scripts/calc_recommender_stats.py --labels eval/relevance_labels.example.json --k 5 --runs 20
```

---

## Tech stack

| Layer | Tech |
|-------|------|
| Frontend | React 19, Vite, fetch |
| Backend | FastAPI, pymongo, pandas |
| Database | MongoDB Atlas |
| ML | Custom TF-IDF + cosine similarity |
| AI | HuggingFace Inference (Meta-Llama-3-8B-Instruct) |
| Auth | JWT, pbkdf2_sha256 |

---

## Project structure

```
lib_recc/
├── frontend/          # React app (Vercel)
├── backend/           # FastAPI app (Render/Railway)
├── docs/              # Architecture, API, ML, deploy guides
├── handoff.md         # LLM handoff document
└── library_db.books.json  # Seed catalog data
```

---

## Roadmap

- [x] Phase 0 — Documentation
- [x] Phase 1 — Deploy readiness
- [x] Phase 2 — ML (hybrid ratings, title+description TF-IDF)
- [x] Phase 3 — Tests, CI, MongoDB indexes
- [x] Phase 4 — UX polish

![CI](https://github.com/anik05169/lib_recc/actions/workflows/ci.yml/badge.svg)

See [docs/KNOWN_ISSUES.md](docs/KNOWN_ISSUES.md) for remaining low-priority items.
