# Machine learning & recommendations

## Overview

Three recommendation paths:

1. **Global catalog** — TF-IDF + cosine similarity on all `books`
2. **User library** — separate TF-IDF model per user on their `user_books`
3. **AI assistant** — HuggingFace Llama-3 via chat completions (natural language → 3 book JSON)

Ratings are used in **hybrid scoring**: `0.7 * cosine + 0.3 * normalized_rating`.

---

## Evaluation & benchmark toolkit

You can now calculate measurable recommender metrics locally from labeled relevance data:

- `Precision@k`
- `Recall@k`
- `HitRate@k`
- `MRR@k`
- Latency stats: `mean`, `p50`, `p95` (ms)

Files:

- `backend/scripts/calc_recommender_stats.py`
- `backend/eval/relevance_labels.example.json`

Run:

```bash
cd backend
python scripts/calc_recommender_stats.py --labels eval/relevance_labels.example.json --k 5 --runs 20
```

Output report is written to `backend/eval/stats_latest.json` by default.

---

## Content-based recommender (`backend/app/services/recommender.py`)

### Algorithm

1. Tokenize text: lowercase alpha words from `split()`
2. Build TF-IDF matrix (custom implementation, no scikit-learn)
3. Compute pairwise cosine similarity (O(n²) matrix)
4. For query `book_id`, return top 5 similar books (excluding self)

### Current feature

**Title + description** — text uses `f"{title} {description}"`.

### Global model

| Variable | Purpose |
|----------|---------|
| `_books_df` | pandas DataFrame of all catalog books |
| `_similarity` | n×n cosine matrix |

**Train triggers:**
- App startup (`startup.py` daemon thread)
- Manual `POST /train` (JWT, no UI)

**Not retrained** when `POST /books` adds to catalog (known issue — Phase 2).

### Per-user model

| Variable | Purpose |
|----------|---------|
| `_user_models[user_id]` | `{ "df", "similarity" }` |

**Train triggers:**
- `POST /user/add-from-catalog`
- `POST /user/add-custom-book`
- `DELETE /user/library/{book_id}`

**Lazy train:** `recommend_user()` trains if model missing and `user_books` passed.

### Thread safety

`_lock` threading.Lock wraps read/write of global and user models.

### Health check

`is_model_ready()` → `_books_df is not None`  
Exposed via `GET /health`.

---

## HuggingFace AI (`backend/app/services/hf_recommender.py`)

| Setting | Value |
|---------|-------|
| Model | `meta-llama/Meta-Llama-3-8B-Instruct` |
| API | `https://router.huggingface.co/v1/chat/completions` |
| Env | `HF_API_KEY` |

Returns strict JSON: `{ recommendations: [{ title, author, description }] }` (exactly 3).

If `HF_API_KEY` missing → `{ recommendations: [] }` (no error).

Frontend enriches with Google Books cover images (`AiBookSuggest.jsx`).

Phase 2 plan: `timeout=30` on requests; 503 when key missing.

---

## Planned: hybrid scoring (Phase 2)

```
final_score = 0.7 * cosine_similarity + 0.3 * normalized_avg_rating
```

Requires loading `GET /ratings/average` aggregates at train or recommend time.

---

## Interview talking points

- Custom TF-IDF keeps dependencies light (pandas only for DataFrame indexing)
- Dual models separate public catalog discovery from private library taste
- LLM handles cold-start / natural language; TF-IDF handles "similar to this book"
- In-memory tradeoff: fast, simple, but single-worker deploy and restart clears models

See [ARCHITECTURE.md](ARCHITECTURE.md) for system diagram.
