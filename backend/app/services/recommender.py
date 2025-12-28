import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Global model (for catalog)
_books_df = None
_similarity = None

# Per-user models
_user_models = {}  # {user_id: {"df": DataFrame, "similarity": array}}


def train_model(books: list):
    """Train global model for catalog recommendations."""
    global _books_df, _similarity

    print("TRAIN CALLED (Global)")
    print("Number of books:", len(books))

    if not books:
        print("No books to train on")
        return

    _books_df = pd.DataFrame(books)

    print("Columns:", _books_df.columns)

    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf = vectorizer.fit_transform(_books_df["description"])
    _similarity = cosine_similarity(tfidf)

    print("Similarity shape:", _similarity.shape)


def train_user_model(user_id: str, books: list):
    """Train a model for a specific user based on their library."""
    global _user_models

    print(f"TRAIN USER MODEL CALLED for user {user_id}")
    print(f"Number of books in user library: {len(books)}")

    if not books:
        print(f"No books to train on for user {user_id}")
        # Remove model if user has no books
        if user_id in _user_models:
            del _user_models[user_id]
        return

    try:
        df = pd.DataFrame(books)
        
        if "description" not in df.columns or df["description"].isna().all():
            print(f"Warning: No valid descriptions for user {user_id}")
            return

        vectorizer = TfidfVectorizer(stop_words="english")
        tfidf = vectorizer.fit_transform(df["description"])
        similarity = cosine_similarity(tfidf)

        _user_models[user_id] = {
            "df": df,
            "similarity": similarity
        }

        print(f"User model trained. Similarity shape: {similarity.shape}")
    except Exception as e:
        print(f"Error training user model for {user_id}: {e}")


def recommend(book_id: int, top_n=5):
    """Recommend books from global catalog."""
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


def recommend_user(user_id: str, book_id: int, top_n=5, user_books=None):
    """Recommend books from user's personal library."""
    # If model doesn't exist and user_books provided, train it
    if user_id not in _user_models and user_books is not None:
        train_user_model(user_id, user_books)
    
    if user_id not in _user_models:
        return []

    model = _user_models[user_id]
    df = model["df"]
    similarity = model["similarity"]

    idx = df[df["book_id"] == book_id].index
    if len(idx) == 0:
        return []

    idx = idx[0]
    scores = list(enumerate(similarity[idx]))
    scores.sort(key=lambda x: x[1], reverse=True)

    # Get top recommendations (excluding the book itself)
    top = scores[1:top_n+1]
    if not top:
        return []
    
    return df.iloc[[i[0] for i in top]].to_dict("records")

