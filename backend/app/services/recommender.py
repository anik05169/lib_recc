import math
import pandas as pd
from collections import Counter, defaultdict

# Global model
_books_df = None
_similarity = None

# Per-user models
_user_models = {}  # user_id -> {"df": DataFrame, "similarity": matrix}


def _tokenize(text: str):
    return [
        w.lower()
        for w in text.split()
        if w.isalpha()
    ]


def _tfidf_matrix(texts):
    docs = [_tokenize(t or "") for t in texts]
    n_docs = len(docs)

    term_freqs = [Counter(doc) for doc in docs]
    df = defaultdict(int)

    for doc in docs:
        for word in set(doc):
            df[word] += 1

    vocab = list(df.keys())
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


# -----------------------
# GLOBAL CATALOG MODEL
# -----------------------

def train_model(books: list):
    global _books_df, _similarity

    if not books:
        return

    _books_df = pd.DataFrame(books)
    tfidf = _tfidf_matrix(_books_df["description"].fillna(""))
    _similarity = [
        [_cosine(a, b) for b in tfidf]
        for a in tfidf
    ]


def recommend(book_id: int, top_n=5):
    if _books_df is None:
        return []

    idxs = _books_df.index[_books_df["book_id"] == book_id].tolist()
    if not idxs:
        return []

    idx = idxs[0]
    scores = list(enumerate(_similarity[idx]))
    scores.sort(key=lambda x: x[1], reverse=True)

    top = scores[1:top_n + 1]
    return _books_df.iloc[[i for i, _ in top]].to_dict("records")


# -----------------------
# USER-SPECIFIC MODEL
# -----------------------

def train_user_model(user_id: str, books: list):
    if not books:
        _user_models.pop(user_id, None)
        return

    df = pd.DataFrame(books)

    if "description" not in df.columns:
        return

    tfidf = _tfidf_matrix(df["description"].fillna(""))
    similarity = [
        [_cosine(a, b) for b in tfidf]
        for a in tfidf
    ]

    _user_models[user_id] = {
        "df": df,
        "similarity": similarity
    }


def recommend_user(user_id: str, book_id: int, top_n=5, user_books=None):
    if user_id not in _user_models:
        if user_books is not None:
            train_user_model(user_id, user_books)

    model = _user_models.get(user_id)
    if not model:
        return []

    df = model["df"]
    similarity = model["similarity"]

    idxs = df.index[df["book_id"] == book_id].tolist()
    if not idxs:
        return []

    idx = idxs[0]
    scores = list(enumerate(similarity[idx]))
    scores.sort(key=lambda x: x[1], reverse=True)

    top = scores[1:top_n + 1]
    return df.iloc[[i for i, _ in top]].to_dict("records")

