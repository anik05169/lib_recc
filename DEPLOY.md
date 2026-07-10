# Deploy checklist — Library AI

Use this when deploying to **MongoDB Atlas + Render (or Railway) + Vercel**.

---

## Environment variables (copy-paste reference)

### MongoDB Atlas (dashboard, not in app env)

| Setting | Value |
|---------|--------|
| Cluster | Free M0 is fine for demo |
| Network access | Allow `0.0.0.0/0` (or Render/Railway outbound IPs) |
| Database user | Create user with read/write on `library_db` |
| Connection string | Use as `MONGODB_URI` below |

### Backend — Render or Railway (`backend/` root)

| Variable | Required | Example / notes |
|----------|----------|-----------------|
| `MONGODB_URI` | **Yes** | `mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true&w=majority` |
| `JWT_SECRET` | **Yes** | Random string — e.g. `openssl rand -hex 32` |
| `ALLOWED_ORIGINS` | **Yes (prod)** | `https://your-app.vercel.app` — exact URL, no trailing slash |
| `HF_API_KEY` | No | HuggingFace token — AI suggestions need this |
| `PINECONE_API_KEY` | **Yes (recommendations)** | From Pinecone console |
| `PINECONE_INDEX_NAME` | **Yes** | e.g. `librasense` — 384 dims, cosine |
| `SKIP_EMBEDDING_SYNC` | **Yes on Render** | `true` — sync runs in GitHub Actions instead |
| `FRONTEND_URL` | No | Alternative to `ALLOWED_ORIGINS` (single URL) |

**Start command (must use 1 worker):**

```bash
gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 1 --bind 0.0.0.0:$PORT
```

**Health check path:** `/health`

### Frontend — Vercel (`frontend/` root)

| Variable | Required | Example / notes |
|----------|----------|-----------------|
| `VITE_API_BASE_URL` | **Yes** | `https://your-api.onrender.com` — no trailing slash |
| `VITE_GOOGLE_BOOKS_API_KEY` | No | Cover images for AI suggestions |

Set `VITE_*` in Vercel **before** build. Redeploy after any change.

---

## Deploy order

### 1. MongoDB Atlas

1. Create cluster + database user.
2. Network Access → **Add IP** → `0.0.0.0/0` (demo) or restrict later.
3. Copy connection string → save for `MONGODB_URI`.

### 2. Backend (Render example)

1. New **Web Service** → connect GitHub repo `anik05169/lib_recc`.
2. **Root directory:** `backend`
3. **Runtime:** Python 3.11 (`runtime.txt`)
4. **Build:** `pip install -r requirements.txt`
5. **Start:** use `Procfile` or command above (`-w 1` required).
6. Set env vars: `MONGODB_URI`, `JWT_SECRET`, `ALLOWED_ORIGINS` (can add after Vercel step).
7. Optional: `HF_API_KEY`
8. Deploy → note API URL, e.g. `https://lib-recc-api.onrender.com`
9. Verify: `GET https://<api>/health` → `{"status":"ok","recommender_ready":true}`  
   (`recommender_ready` may be `false` for ~15s until startup training finishes)

### 3. Seed catalog (first deploy only)

Empty MongoDB = empty catalog and no recommendations.

**Option A — from your machine:**

```bash
cd backend
# .env with MONGODB_URI pointing at Atlas
python scripts/seed_catalog.py
```

**Option B — mongoimport:**

```bash
mongoimport --uri "<MONGODB_URI>" --db library_db --collection books --file library_db.books.json --jsonArray
```

Then restart the backend or call `POST /train` as admin.

### 4. Frontend (Vercel)

1. Import repo → **Root directory:** `frontend`
2. Framework: **Vite**
3. Environment: `VITE_API_BASE_URL=https://<your-api-url>`
4. Deploy → note frontend URL, e.g. `https://lib-recc.vercel.app`

### 5. Fix CORS (if not done yet)

On the backend, set:

```
ALLOWED_ORIGINS=https://lib-recc.vercel.app
```

Include preview URLs if needed (comma-separated). Redeploy backend.

### 6. Admin user (optional)

In MongoDB Atlas → `library_db` → `users` → your user document:

```json
{ "is_admin": true }
```

Enables `POST /books` and `POST /train` via API.

### 7. Update README

Replace placeholder URLs in root `README.md` with your live frontend + API + health links.

---

## Post-deploy smoke test

1. Open frontend URL → register → login.
2. Catalog shows books (if seeded).
3. Add book to library → rate → see recommendations.
4. AI suggest works if `HF_API_KEY` is set.
5. `GET /health` shows `recommender_ready: true`.

---

## GitHub Actions — MongoDB seed + Pinecone sync

Workflow: [`.github/workflows/sync-data.yml`](.github/workflows/sync-data.yml)

Runs on **manual dispatch** or when `library_db.books*.json` changes on `main`.

### Repository secrets (Settings → Secrets and variables → Actions)

| Secret | Value |
|--------|--------|
| `MONGODB_URI` | Same Atlas connection string as production |
| `PINECONE_API_KEY` | Pinecone API key |
| `PINECONE_INDEX_NAME` | e.g. `librasense` |

### Atlas network access

GitHub Actions runners use dynamic IPs. Allow **`0.0.0.0/0`** in Atlas Network Access (or re-run when a run fails with connection timeout).

### Manual run

GitHub → **Actions** → **Sync MongoDB and Pinecone** → **Run workflow**

Steps performed:
1. `seed_catalog.py --force` → loads `library_db.books.1000.json` into MongoDB
2. `sync_pinecone_index.py --scope catalog` → encodes + upserts 1000 vectors to Pinecone
3. Verifies `catalog_vector_count >= 100`

First run may take **15–30 minutes** (torch + MiniLM model download). Later runs are faster with pip/HF cache.

---

## Common failures

| Symptom | Fix |
|---------|-----|
| CORS error in browser | `ALLOWED_ORIGINS` = exact Vercel URL |
| Config screen / blank app | `VITE_API_BASE_URL` set in Vercel, redeploy |
| `recommender_ready: false` forever | Run GitHub Actions **Sync MongoDB and Pinecone**; check Pinecone secrets |
| AI returns nothing | Set `HF_API_KEY` on backend |
| 401 everywhere | New deploy changed `JWT_SECRET` — log in again |
| Render slow first load | Free tier cold start (~30–60s) — normal |

---

## Files in this repo for deploy

| File | Purpose |
|------|---------|
| `backend/Procfile` | Gunicorn start (`-w 1`) |
| `backend/render.yaml` | Render blueprint |
| `railway.toml` | Railway start + health check |
| `backend/runtime.txt` | Python 3.11.9 |
| `frontend/vercel.json` | SPA rewrites + security headers |
| `backend/scripts/seed_catalog.py` | Import seed books |
| `backend/scripts/sync_pinecone_index.py` | Encode + upsert vectors to Pinecone |
| `.github/workflows/sync-data.yml` | CI: Mongo seed + Pinecone sync |
| `backend/.env.example` | Backend env template |
| `frontend/.env.example` | Frontend env template |

Full detail: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
