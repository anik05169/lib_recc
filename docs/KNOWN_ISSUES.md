# Known issues & tech debt

Severity: **High** | **Medium** | **Low**  
Status: ~~Fixed~~ | Open

---

## Fixed (recent sessions)

| Issue | Status |
|-------|--------|
| Search debounce re-fetch loop (`onSearch` unstable) | ~~Fixed~~ — `useCallback` + skip initial mount |
| `loadCatalog` depended on `searchQuery` → full reload on search | ~~Fixed~~ |
| Missing `res.ok` on catalog/recommendations fetches | ~~Fixed~~ |
| `BookCard` ignored `showDescription` prop | ~~Fixed~~ |
| Raw `dict` for AI suggest payload | ~~Fixed~~ — `AiSuggestionRequest` |
| Catalog search regex special chars | ~~Fixed~~ — `re.escape` |
| Broken `/placeholder.jpg` | ~~Fixed~~ — placehold.co URL |
| `api.js` crash at import without env | ~~Fixed~~ — config screen |
| No `/health` endpoint | ~~Fixed~~ |
| No `.env.example` files | ~~Fixed~~ |
| No deployment docs / Procfile | ~~Fixed~~ — see DEPLOYMENT.md |
| Hybrid ratings in recommender | ~~Fixed~~ — Phase 2 |
| Global model stale after catalog writes | ~~Fixed~~ |
| No automated tests / CI | ~~Fixed~~ — Phase 3 |
| No MongoDB indexes | ~~Fixed~~ — `ensure_indexes()` |
| Open admin on `POST /books`, `POST /train` | ~~Fixed~~ — `require_admin` |
| `InvalidId` JWT → 500 | ~~Fixed~~ |
| HF no timeout / silent missing key | ~~Fixed~~ |
| Delete errors silent | ~~Fixed~~ |
| Catalog search skeleton flicker | ~~Fixed~~ |
| No delete confirmation | ~~Fixed~~ |
| User name not in header | ~~Fixed~~ |

---

## High — Open

| Issue | Location | Notes |
|-------|----------|-------|
| In-memory recommender, single worker only | `recommender.py`, `Procfile` | By design; use `-w 1` on deploy |

---

## Medium — Open

| Issue | Location | Notes |
|-------|----------|-------|
| JWT 30-day expiry, no refresh | `auth.py` | |
| Public catalog API, login-gated UI | `App.jsx`, `books.py` | Intentional? |
| Monolithic `App.jsx` (~470 lines) | `App.jsx` | Defer |
| `user_books` denormalized, no sync from catalog | `users.py` | By design |
| `book_id` collision risk on heavy concurrent writes | `users.py`, `books.py` | Indexes help; UUID future |

---

## Low — Open

| Issue | Location | Notes |
|-------|----------|-------|
| No URL routing (tabs only) | `App.jsx` | |
| Limited a11y (partial `aria-live` only) | frontend | |
| Admin endpoints have no UI (`POST /books`, `POST /train`) | — | API-only |
| `Rating` schema unused | `schemas.py` | |
| `pagination.total` not displayed | `CatalogView.jsx` | |
| Google Fonts via CSS `@import` | `index.css` | |
| `Rating.user_id: int` wrong type in schema | `schemas.py` | |

---

## When fixing an issue

1. Fix the code
2. Strike through or move to Fixed section here
3. Add entry to [CHANGELOG.md](CHANGELOG.md)
