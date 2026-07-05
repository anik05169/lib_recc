import math
import threading
import pandas as pd
from collections import Counter, defaultdict

# Thread lock for safe concurrent access
_lock = threading.Lock()

# Global model
_books_df = None
_similarity = None
_ratings_map = {}  # book_id -> avg_rating (1-5)

# Per-user models
_user_models = {}  # user_id -> {"df": DataFrame, "similarity": matrix, "ratings_map": dict}

DEFAULT_PLACEHOLDER_IMAGE = "https://placehold.co/150x200?text=No+Image"

CONTENT_WEIGHT = 0.7
RATING_WEIGHT = 0.3


def is_model_ready() -> bool:
    with _lock:
        return _books_df is not None


def _tokenize(text: str):
    return [
        w.lower()
        for w in text.split()
        if w.isalpha()
    ]


def _book_texts(df: pd.DataFrame):
    titles = df["title"].fillna("") if "title" in df.columns else ""
    descs = df["description"].fillna("") if "description" in df.columns else ""
    return (titles + " " + descs).str.strip()


def _tfidf_matrix(texts):
    docs = [_tokenize(t or "") for t in texts]
    n_docs = len(docs)
    if n_docs == 0:
        return []

    term_freqs = [Counter(doc) for doc in docs]
    df = defaultdict(int)

    for doc in docs:
        for word in set(doc):
            df[word] += 1

    vocab = list(df.keys())
    if not vocab:
        return [[] for _ in docs]

    idf = {
        word: math.log(n_docs / (1 + df[word]))
        for word in vocab
    }

    matrix = []
    for tf in term_freqs:
        vec = [tf[word] * idf[word] for word in vocab]
        matrix.append(vec)

    return matrix


def _cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def _rating_norm(book_id, ratings_map: dict) -> float:
    rating = ratings_map.get(book_id)
    if rating is None:
        return 0.0
    return float(rating) / 5.0


def _hybrid_score(cosine_score: float, book_id, ratings_map: dict) -> float:
    return CONTENT_WEIGHT * cosine_score + RATING_WEIGHT * _rating_norm(book_id, ratings_map)


def _top_similar(idx, df, similarity, ratings_map, top_n=5):
    scores = list(enumerate(similarity[idx]))
    ranked = []
    for i, cos_score in scores:
        if i == idx:
            continue
        book_id = df.iloc[i]["book_id"]
        ranked.append((i, _hybrid_score(cos_score, book_id, ratings_map)))
    ranked.sort(key=lambda x: x[1], reverse=True)
    top = ranked[:top_n]
    return df.iloc[[i for i, _ in top]].to_dict("records")


# -----------------------
# GLOBAL CATALOG MODEL
# -----------------------

def train_model(books: list, ratings_map: dict = None):
    global _books_df, _similarity, _ratings_map

    if not books:
        with _lock:
            _books_df = None
            _similarity = None
            _ratings_map = {}
        return

    df = pd.DataFrame(books)
    texts = _book_texts(df)
    tfidf = _tfidf_matrix(texts.tolist())
    sim = [
        [_cosine(a, b) for b in tfidf]
        for a in tfidf
    ]

    with _lock:
        _books_df = df
        _similarity = sim
        _ratings_map = ratings_map or {}


def set_ratings_map(ratings_map: dict):
    global _ratings_map
    with _lock:
        _ratings_map = ratings_map or {}


def recommend(book_id: int, top_n=5, ratings_map: dict = None):
    with _lock:
        if _books_df is None:
            return None

        ratings = ratings_map if ratings_map is not None else _ratings_map
        idxs = _books_df.index[_books_df["book_id"] == book_id].tolist()
        if not idxs:
            return []

        idx = idxs[0]
        return _top_similar(idx, _books_df, _similarity, ratings, top_n)


# -----------------------
# USER-SPECIFIC MODEL
# -----------------------

def train_user_model(user_id: str, books: list, ratings_map: dict = None):
    if not books:
        with _lock:
            _user_models.pop(user_id, None)
        return

    df = pd.DataFrame(books)

    if "description" not in df.columns:
        return

    texts = _book_texts(df)
    tfidf = _tfidf_matrix(texts.tolist())
    similarity = [
        [_cosine(a, b) for b in tfidf]
        for a in tfidf
    ]

    with _lock:
        _user_models[user_id] = {
            "df": df,
            "similarity": similarity,
            "ratings_map": ratings_map or {},
        }


def recommend_user(user_id: str, book_id: int, top_n=5, user_books=None, ratings_map: dict = None):
    with _lock:
        needs_train = user_id not in _user_models

    if needs_train and user_books is not None:
        train_user_model(user_id, user_books, ratings_map)

    with _lock:
        model = _user_models.get(user_id)
        if not model:
            return []

        df = model["df"]
        similarity = model["similarity"]
        ratings = ratings_map if ratings_map is not None else model.get("ratings_map", {})

        idxs = df.index[df["book_id"] == book_id].tolist()
        if not idxs:
            return []

        idx = idxs[0]
        return _top_similar(idx, df, similarity, ratings, top_n)
