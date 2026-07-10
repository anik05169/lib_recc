"""Pinecone-backed embedding recommender with hybrid content + rating re-rank."""

import threading

from app.db.mongo import get_mongo_db
from app.services import pinecone_store

_lock = threading.Lock()
_ratings_map: dict = {}

CONTENT_WEIGHT = 0.7
RATING_WEIGHT = 0.3

DEFAULT_PLACEHOLDER_IMAGE = "https://placehold.co/150x200?text=No+Image"


def is_model_ready() -> bool:
    return pinecone_store.is_namespace_ready(pinecone_store.CATALOG_NAMESPACE)


def get_health_details() -> dict:
    return {
        "pinecone_configured": pinecone_store.is_configured(),
        "pinecone_connected": pinecone_store.is_connected(),
        "catalog_vector_count": pinecone_store.get_namespace_vector_count(
            pinecone_store.CATALOG_NAMESPACE
        ),
    }


def set_ratings_map(ratings_map: dict) -> None:
    global _ratings_map
    with _lock:
        _ratings_map = ratings_map or {}


def get_ratings_map() -> dict:
    with _lock:
        return dict(_ratings_map)


def _rating_norm(book_id: int, ratings_map: dict) -> float:
    rating = ratings_map.get(book_id)
    if rating is None:
        return 0.0
    return float(rating) / 5.0


def _hybrid_score(cosine_score: float, book_id: int, ratings_map: dict) -> float:
    return CONTENT_WEIGHT * cosine_score + RATING_WEIGHT * _rating_norm(book_id, ratings_map)


def _hydrate_books(book_ids: list[int]) -> dict[int, dict]:
    if not book_ids:
        return {}
    db = get_mongo_db()
    books = list(
        db.books.find({"book_id": {"$in": book_ids}}, {"_id": 0})
    )
    catalog = {int(b["book_id"]): b for b in books}

    missing = [bid for bid in book_ids if bid not in catalog]
    if missing:
        user_books = list(
            db.user_books.find({"book_id": {"$in": missing}}, {"_id": 0})
        )
        for book in user_books:
            catalog[int(book["book_id"])] = book

    return catalog


def _recommend_in_namespace(
    namespace: str,
    book_id: int,
    top_n: int,
    ratings_map: dict,
) -> list[dict]:
    seed_vector = pinecone_store.fetch_vector(namespace, book_id)
    if not seed_vector:
        return []

    hits = pinecone_store.query_similar(
        namespace,
        seed_vector,
        top_k=max(top_n * 3, top_n + 5),
        exclude_id=book_id,
    )
    if not hits:
        return []

    ranked = [
        (hit["book_id"], _hybrid_score(hit["score"], hit["book_id"], ratings_map))
        for hit in hits
    ]
    ranked.sort(key=lambda x: x[1], reverse=True)
    top_ids = [bid for bid, _ in ranked[:top_n]]

    catalog = _hydrate_books(top_ids)
    results = []
    for bid in top_ids:
        book = catalog.get(bid)
        if book:
            results.append(book)
    return results


def recommend(book_id: int, top_n: int = 5, ratings_map: dict = None) -> list[dict] | None:
    if not is_model_ready():
        return None

    ratings = ratings_map if ratings_map is not None else get_ratings_map()
    return _recommend_in_namespace(
        pinecone_store.CATALOG_NAMESPACE,
        book_id,
        top_n,
        ratings,
    )


def recommend_user(
    user_id: str,
    book_id: int,
    top_n: int = 5,
    user_books=None,
    ratings_map: dict = None,
) -> list[dict]:
    namespace = pinecone_store.user_namespace(user_id)
    if not pinecone_store.is_namespace_ready(namespace):
        if user_books:
            from app.services.vector_sync import sync_user_library_to_pinecone

            sync_user_library_to_pinecone(user_id, user_books)
        if not pinecone_store.is_namespace_ready(namespace):
            return []

    ratings = ratings_map if ratings_map is not None else get_ratings_map()
    return _recommend_in_namespace(namespace, book_id, top_n, ratings)
