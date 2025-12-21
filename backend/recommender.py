import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

_books_df = None
_similarity = None

def train_model(books: list):
    global _books_df, _similarity

    _books_df = pd.DataFrame(books)

    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf = vectorizer.fit_transform(_books_df["description"])
    _similarity = cosine_similarity(tfidf)

def recommend(book_id: int, top_n=5):
    if _books_df is None:
        return []

    idx = _books_df[_books_df["book_id"] == book_id].index
    if len(idx) == 0:
        return []

    idx = idx[0]
    scores = list(enumerate(_similarity[idx]))
    scores.sort(key=lambda x: x[1], reverse=True)

    top = scores[1:top_n+1]
    return _books_df.iloc[[i[0] for i in top]].to_dict("records")

