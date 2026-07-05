# Backend

**Stack:** FastAPI, pymongo, pandas, python-jose, passlib

Entry: `backend/app/main.py`

---

## Directory layout

```
backend/app/
├── main.py              # FastAPI app, routers, /health
├── startup.py           # Background recommender training
├── core/
│   ├── auth.py          # JWT, password hash, get_current_user
│   └── config.py        # CORS, JWT secret validation
├── db/
│   └── mongo.py         # get_mongo_db() → library_db
├── models/
│   └── schemas.py       # Pydantic models
├── routes/
│   ├── auth.py          # /auth/*
│   ├── books.py         # /books, /recommend, /train, AI
│   ├── users.py         # /user/*
│   └── ratings.py       # /ratings/*
└── services/
    ├── recommender.py   # TF-IDF engine
    └── hf_recommender.py # HuggingFace wrapper
```

---

## Startup sequence

1. `validate_runtime_config()` — fails if no `JWT_SECRET` / `SECRET_KEY`
2. `lifespan` context manager starts daemon thread
3. `train_recommender_on_startup()` loads all books, calls `train_model()`
4. Errors print to console; API still starts (recommendations empty until trained)

---

## Route → service mapping

| Route | Service / DB |
|-------|--------------|
| `GET /recommend/{id}` | `recommender.recommend()` |
| `GET /user/recommend/{id}` | `recommender.recommend_user()` |
| `POST /user/add-*`, `DELETE` | MongoDB + `train_user_model()` |
| `POST /books/ai-suggest-new` | `hf_recommender.recommend_books_hf()` |
| `POST /train` | `recommender.train_model()` |

---

## Authentication

- Scheme: OAuth2 bearer JWT
- Hash: `pbkdf2_sha256` (20000 rounds) — README incorrectly says bcrypt
- Expiry: 30 days
- `get_current_user` dependency on protected routes

---

## Production

| File | Purpose |
|------|---------|
| `Procfile` | Gunicorn + UvicornWorker, 1 worker |
| `requirements.txt` | Pinned dependencies |
| `runtime.txt` | Python 3.11.9 |
| `.env.example` | Env documentation |

Start locally:
```bash
uvicorn app.main:app --reload
```

Start production (via Procfile):
```bash
gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 1 --bind 0.0.0.0:$PORT
```

---

## Manual utilities (not part of app)

| File | Purpose |
|------|---------|
| `add_images.py` | Backfill cover URLs via Open Library |
| `add_docs.ipynb` | Bulk insert notebook |

---

## Interactive API docs

With server running: `http://localhost:8000/docs`

See [API.md](API.md) for endpoint reference.
