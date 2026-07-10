"""Public recommender API — facade over Pinecone vector retrieval."""

from app.services import vector_recommender
from app.services.vector_sync import (
    sync_catalog_to_pinecone,
    sync_user_library_to_pinecone,
    upsert_catalog_book,
)

DEFAULT_PLACEHOLDER_IMAGE = vector_recommender.DEFAULT_PLACEHOLDER_IMAGE
CONTENT_WEIGHT = vector_recommender.CONTENT_WEIGHT
RATING_WEIGHT = vector_recommender.RATING_WEIGHT


def is_model_ready() -> bool:
    return vector_recommender.is_model_ready()


def get_health_details() -> dict:
    return vector_recommender.get_health_details()


def set_ratings_map(ratings_map: dict) -> None:
    vector_recommender.set_ratings_map(ratings_map)


def get_ratings_map() -> dict:
    return vector_recommender.get_ratings_map()


def train_model(books: list, ratings_map: dict = None, mode: str = None) -> int:
    """Sync catalog embeddings to Pinecone and refresh cached ratings."""
    if ratings_map is not None:
        set_ratings_map(ratings_map)
    return sync_catalog_to_pinecone(books)


def train_user_model(user_id: str, books: list, ratings_map: dict = None, mode: str = None) -> int:
    """Sync user library embeddings to Pinecone."""
    if ratings_map is not None:
        set_ratings_map(ratings_map)
    return sync_user_library_to_pinecone(user_id, books)


def recommend(book_id: int, top_n: int = 5, ratings_map: dict = None):
    return vector_recommender.recommend(book_id, top_n=top_n, ratings_map=ratings_map)


def recommend_user(
    user_id: str,
    book_id: int,
    top_n: int = 5,
    user_books=None,
    ratings_map: dict = None,
    mode: str = None,
):
    return vector_recommender.recommend_user(
        user_id,
        book_id,
        top_n=top_n,
        user_books=user_books,
        ratings_map=ratings_map,
    )


def upsert_book(book: dict) -> int:
    """Upsert a single catalog book vector (after POST /books)."""
    return upsert_catalog_book(book)
