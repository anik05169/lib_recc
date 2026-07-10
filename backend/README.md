# Backend

FastAPI API for Library AI.

## Quick start

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
pip install -r requirements-embeddings.txt   # for sync script / local encoding
cp .env.example .env         # set MONGODB_URI, JWT_SECRET, PINECONE_*
```

### Pinecone setup (one-time)

1. Create a Pinecone index: **384 dimensions**, **cosine** metric (e.g. `libra-books`)
2. Add `PINECONE_API_KEY` and `PINECONE_INDEX_NAME` to `.env`
3. Sync catalog vectors (does **not** run automatically on first clone):

```bash
python scripts/sync_pinecone_index.py --scope catalog
```

```bash
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs  
Health: http://localhost:8000/health (checks `recommender_ready` + Pinecone)

## Production

Uses `Procfile` with Gunicorn — **1 worker** recommended while ratings cache is in-process.

Set `SKIP_EMBEDDING_SYNC=true` on Render; run `sync_pinecone_index.py` from your machine or CI before/after catalog changes.

See [../docs/DEPLOYMENT.md](../docs/DEPLOYMENT.md) and [../docs/BACKEND.md](../docs/BACKEND.md).

## Environment

Copy `.env.example` → `.env`. Required: `MONGODB_URI`, `JWT_SECRET`, `PINECONE_API_KEY`, `PINECONE_INDEX_NAME`.

## Recommender stats (offline eval + latency)

```bash
cd backend
python scripts/calc_recommender_stats.py --labels eval/relevance_labels.example.json --k 5 --runs 20
python scripts/benchmark_api_latency.py --labels eval/relevance_labels.example.json --wait-health
```

Seed catalog: `python scripts/seed_catalog.py` — see [../DEPLOY.md](../DEPLOY.md).
