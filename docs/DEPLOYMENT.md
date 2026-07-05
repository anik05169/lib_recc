# Deployment

## Overview

| Component | Platform | Root directory |
|-----------|----------|----------------|
| Frontend | Vercel | `frontend/` |
| Backend | Render or Railway | `backend/` |
| Database | MongoDB Atlas | — |

---

## Environment variables

### Backend (`backend/.env`)

Copy from `backend/.env.example`:

| Variable | Required | Description |
|----------|----------|-------------|
| `MONGODB_URI` | Yes (prod) | Atlas connection string |
| `JWT_SECRET` | Yes | Random string; validated at startup |
| `HF_API_KEY` | No | HuggingFace token for AI suggestions |
| `ALLOWED_ORIGINS` | Yes (prod) | Comma-separated frontend URLs for CORS |
| `FRONTEND_URL` | Alt to above | Single origin, also added to CORS |

Default CORS (if unset): `http://localhost:5173`, `http://localhost:3000`

### Frontend (`frontend/.env`)

Copy from `frontend/.env.example`:

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_BASE_URL` | Yes | Backend URL, no trailing slash |
| `VITE_GOOGLE_BOOKS_API_KEY` | No | Cover images for AI suggestions |

**Important:** Vite inlines `VITE_*` at **build time**. Set vars in Vercel dashboard before deploying.

---

## Backend deploy (Render example)

1. New **Web Service**, connect GitHub repo
2. **Root directory:** `backend`
3. **Runtime:** Python 3.11 (`runtime.txt` specifies 3.11.9)
4. **Start command:** uses `Procfile` automatically, or:
   ```
   gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 1 --bind 0.0.0.0:$PORT
   ```
5. Set env vars: `MONGODB_URI`, `JWT_SECRET`, `ALLOWED_ORIGINS=https://your-app.vercel.app`
6. Optional: `HF_API_KEY`
7. **Admin:** In MongoDB Atlas, set `is_admin: true` on your user document for `POST /books` / `POST /train`
8. Verify: `GET https://your-api.onrender.com/health`

### Single worker rule

**Always use `-w 1`.** The TF-IDF recommender stores state in process memory. Multiple Gunicorn workers each have separate models; recommendations will be inconsistent.

---

## Frontend deploy (Vercel)

1. Import repo, set **root directory** to `frontend`
2. Framework preset: Vite
3. Environment: `VITE_API_BASE_URL=https://your-api.onrender.com`
4. `vercel.json` handles SPA rewrites to `index.html`
5. Redeploy after changing env vars

---

## Local development

```bash
# Terminal 1 — backend
cd backend
pip install -r requirements.txt
cp .env.example .env   # edit values
uvicorn app.main:app --reload

# Terminal 2 — frontend
cd frontend
npm install
cp .env.example .env   # VITE_API_BASE_URL=http://localhost:8000
npm run dev
```

No Vite proxy — frontend calls backend directly via CORS.

---

## Health checks

```
GET /health
→ { "status": "ok", "recommender_ready": true }
```

`recommender_ready` may be `false` for ~5–15s after startup while the background training thread runs.

---

## Common deploy issues

| Symptom | Fix |
|---------|-----|
| CORS error in browser | Set `ALLOWED_ORIGINS` on backend to exact Vercel URL |
| Blank app / config screen | Set `VITE_API_BASE_URL` in Vercel, redeploy |
| AI returns nothing | Set `HF_API_KEY` on backend |
| Empty recommendations | Wait for `recommender_ready: true`; check MongoDB has books |
| 401 on all requests | Token expired or `JWT_SECRET` changed between deploys |

---

## Placeholder images

Books without covers use:

```
https://placehold.co/150x200?text=No+Image
```

Defined as `DEFAULT_PLACEHOLDER_IMAGE` (backend) and `PLACEHOLDER_IMAGE_URL` (frontend `api.js`).

Do not use `/placeholder.jpg` — file does not exist in `public/`.

---

## Live demo URLs

Update root `README.md` after deploying:

```markdown
- **Frontend:** https://your-app.vercel.app
- **API:** https://your-api.onrender.com
- **Health:** https://your-api.onrender.com/health
```
