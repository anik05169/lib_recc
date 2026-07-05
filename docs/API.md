# API reference

Base URL: `VITE_API_BASE_URL` (e.g. `http://localhost:8000`)

Interactive docs: `{BASE}/docs` (FastAPI Swagger)

## Auth legend

| Symbol | Meaning |
|--------|---------|
| — | Public |
| JWT | `Authorization: Bearer <token>` required |

---

## Health

| Method | Path | Auth | Response |
|--------|------|------|----------|
| GET | `/` | — | `{ "message": "Personal Library API running" }` |
| GET | `/health` | — | `{ "status": "ok", "recommender_ready": bool }` |

**Frontend caller:** none (deploy/monitoring only)

---

## Authentication (`/auth`)

| Method | Path | Auth | Body | Response |
|--------|------|------|------|----------|
| POST | `/auth/register` | — | `{ email, password, name }` | `{ user_id, email, name }` |
| POST | `/auth/login` | — | `{ email, password }` | `{ access_token, token_type: "bearer" }` |
| GET | `/auth/me` | JWT | — | `{ user_id, email, name }` |

**Password rules:** min 8 chars, 1 uppercase, 1 digit.

**Frontend callers:**
- `Register.jsx` → register + auto-login
- `Login.jsx` → login
- `App.jsx` → `checkAuth()` validates token via `/auth/me`

---

## Books & recommendations

| Method | Path | Auth | Params / Body | Response |
|--------|------|------|---------------|----------|
| GET | `/books` | — | `?search=&page=1&limit=50` | `{ books[], total, page, pages }` |
| POST | `/books` | JWT | `Book` JSON | `{ status: "ok", book_id }` |
| GET | `/recommend/{book_id}` | — | — | `Book[]` (array) |
| POST | `/train` | JWT | — | `{ message }` |
| POST | `/books/ai-suggest-new` | JWT | `{ description }` | `{ recommendations: [{ title, author, description }] }` |

**Notes:**
- Search regex is escaped server-side (`re.escape`).
- `POST /books` and `POST /train` have **no UI** — any logged-in user can call them.
- AI returns empty `recommendations` if `HF_API_KEY` unset; errors → 502.

**Frontend callers:**
- `App.jsx` → `GET /books`, `GET /recommend/{id}`
- `AiBookSuggest.jsx` → `POST /books/ai-suggest-new`

---

## User library (`/user`)

| Method | Path | Auth | Params / Body | Response |
|--------|------|------|---------------|----------|
| GET | `/user/library` | JWT | — | `Book[]` (array) |
| POST | `/user/add-from-catalog` | JWT | `?book_id=` query | `{ message }` |
| POST | `/user/add-custom-book` | JWT | `Book` JSON | `{ message, book_id }` |
| DELETE | `/user/library/{book_id}` | JWT | — | `{ message }` |
| GET | `/user/library/ids` | JWT | — | `number[]` |
| GET | `/user/recommend/{book_id}` | JWT | — | `Book[]` |

**Frontend callers:**
- `App.jsx` → all except `/user/library/ids`

---

## Ratings (`/ratings`)

| Method | Path | Auth | Body | Response |
|--------|------|------|------|----------|
| POST | `/ratings` | JWT | `{ book_id, rating }` (1–5) | `{ message }` |
| GET | `/ratings/average` | — | — | `[{ _id: book_id, avg_rating }]` |
| GET | `/ratings/mine` | JWT | — | `[{ book_id, rating }]` |

**Rule:** Can only rate books in your library.

**Frontend callers:** `App.jsx` → all three

---

## Response shape inconsistencies

| Endpoint | Shape |
|----------|-------|
| `GET /books` | Paginated object |
| `GET /user/library`, `GET /recommend/*` | Raw array |
| Mutations | `{ message }` or `{ status }` |
| `GET /ratings/average` | `_id` field = `book_id` |

`App.jsx` handles legacy array response from `GET /books` via `Array.isArray(data)` check.

---

## Pydantic schemas (`backend/app/models/schemas.py`)

| Model | Used by |
|-------|---------|
| `Book` | POST bodies |
| `UserRegister`, `UserLogin` | Auth |
| `AiSuggestionRequest` | AI suggest |
| `Token`, `UserResponse` | Auth responses |
| `Rating` | **Unused** in routes (inline Body instead) |
