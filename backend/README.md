# Backend

FastAPI API for Library AI.

## Quick start

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env         # set MONGODB_URI, JWT_SECRET
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs  
Health: http://localhost:8000/health

## Production

Uses `Procfile` with Gunicorn — **must run 1 worker** (in-memory recommender).

See [../docs/DEPLOYMENT.md](../docs/DEPLOYMENT.md) and [../docs/BACKEND.md](../docs/BACKEND.md).

## Environment

Copy `.env.example` → `.env`. Required: `MONGODB_URI`, `JWT_SECRET`.

## Recommender stats (offline eval + latency)

Use labeled query relevance to compute `Precision@k`, `Recall@k`, `HitRate@k`, `MRR@k`, and latency (`mean/p50/p95`):

```bash
cd backend
python scripts/calc_recommender_stats.py --labels eval/relevance_labels.example.json --k 5 --runs 20
```

Update `eval/relevance_labels.example.json` with your own labels first.

Seed catalog (first deploy): `python scripts/seed_catalog.py` — see [../DEPLOY.md](../DEPLOY.md).
