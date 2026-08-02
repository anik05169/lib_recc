# Frontend

**Stack:** React 19, Vite 7, native `fetch` (not Axios)

Entry: `frontend/src/main.jsx` → `ErrorBoundary` → `App.jsx`

**Look:** Warm charcoal UI (`index.css` / `App.css`) with Fraunces (display) + Figtree (body), teal accent. Auth uses a brand-first split layout (`Login.css`).

---

## Component tree

```
App.jsx
├── Login / Register          (unauthenticated)
├── CatalogView               (view === "catalog")
│   ├── BookCard
│   └── SkeletonCard
└── LibraryView               (view === "library")
    ├── AiBookSuggest
    │   └── BookCard
    ├── AddCustomBook
    └── UserLibrary
        └── BookCard
```

---

## App.jsx state map

| State | Purpose |
|-------|---------|
| `token` | JWT; null = logged out |
| `view` | `"catalog"` \| `"library"` |
| `catalogBooks` | Paginated catalog results |
| `userBooks` | User library array |
| `userBookIds` | Set for "Collected ✓" badges |
| `userRatings` | `{ book_id: rating }` |
| `avgRatings` | `{ book_id: "4.2" }` |
| `expandedBookId` | Catalog recommendation panel |
| `expandedLibraryBookId` | Library recommendation panel |
| `recommendations` | Global recs cache by book_id |
| `libraryRecommendations` | User recs cache by book_id |
| `loading` | `{ catalog, library }` |
| `searchQuery` | Current catalog search |
| `pagination` | `{ page, pages, total }` |
| `toasts` | Toast notification queue |
| `newBook` | Form state for custom book |

### Loaders (on token set)

`loadCatalog`, `loadUserLibrary`, `loadAverageRatings`, `loadUserRatings`

### Key callbacks

| Function | API |
|----------|-----|
| `handleSearch` | `GET /books?search=` |
| `addFromCatalog` | `POST /user/add-from-catalog` |
| `addCustomBook` | `POST /user/add-custom-book` |
| `rateBook` | `POST /ratings` |
| `deleteFromLibrary` | `DELETE /user/library/{id}` |
| `openBookDetails` | `GET /recommend/{id}` |
| `openLibraryBookDetails` | `GET /user/recommend/{id}` |

---

## api.js

```javascript
export const isApiConfigured    // false if VITE_API_BASE_URL missing
export const API_BASE_URL       // trimmed, no trailing slash
export const PLACEHOLDER_IMAGE_URL
export function getApiBaseUrl() // throws if not configured
```

If `!isApiConfigured`, `App.jsx` shows configuration screen (build succeeds without env).

---

## CatalogView search

- Local `localSearch` state with 400ms debounce
- Skips debounce on initial mount (parent already loads catalog)
- `handleSearch` wrapped in `useCallback` in App to avoid re-fetch loops

---

## Toast system

`showToast(message, type)` — types: `info`, `success`, `error`, `warning`  
Auto-dismiss after 4 seconds.

---

## API usage matrix

| Endpoint | Component |
|----------|-----------|
| `/auth/login` | Login.jsx, Register.jsx |
| `/auth/register` | Register.jsx |
| `/auth/me` | App.jsx |
| `/books` | App.jsx |
| `/recommend/{id}` | App.jsx |
| `/books/ai-suggest-new` | AiBookSuggest.jsx |
| `/user/*` | App.jsx |
| `/ratings/*` | App.jsx |

### Unused backend endpoints (no UI)

- `POST /books` — add to global catalog
- `POST /train` — retrain global model
- `GET /user/library/ids` — redundant with full library fetch

---

## Config files

| File | Role |
|------|------|
| `vite.config.js` | Default Vite + React plugin |
| `vercel.json` | SPA rewrite to index.html |
| `.env.example` | Required env documentation |
| `eslint.config.js` | ESLint flat config + react-hooks |

---

## Scripts

```bash
npm run dev      # localhost:5173
npm run build    # dist/
npm run lint
npm run preview
```

No test script yet (Phase 3).
