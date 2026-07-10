"""Sync MongoDB book records to Pinecone (embedding encode + upsert)."""

import os

from app.services.embedding_service import book_text_from_record, encode_texts
from app.services import pinecone_store


def _skip_embedding_sync() -> bool:
    return os.getenv("SKIP_EMBEDDING_SYNC", "").strip().lower() in {"1", "true", "yes"}


def _books_to_vectors(books: list[dict]) -> list[dict]:
    texts = [book_text_from_record(book) for book in books]
    vectors = encode_texts(texts)
    items = []
    for book, vector in zip(books, vectors):
        book_id = int(book["book_id"])
        items.append(
            {
                "id": str(book_id),
                "values": vector,
                "metadata": {
                    "book_id": book_id,
                    "title": (book.get("title") or "")[:200],
                },
            }
        )
    return items


def sync_catalog_to_pinecone(books: list[dict]) -> int:
    if _skip_embedding_sync():
        return 0
    if not books:
        pinecone_store.delete_namespace(pinecone_store.CATALOG_NAMESPACE)
        return 0

    items = _books_to_vectors(books)
    pinecone_store.delete_namespace(pinecone_store.CATALOG_NAMESPACE)
    pinecone_store.upsert_vectors(pinecone_store.CATALOG_NAMESPACE, items)
    return len(items)


def sync_user_library_to_pinecone(user_id: str, books: list[dict]) -> int:
    if _skip_embedding_sync():
        return 0

    namespace = pinecone_store.user_namespace(user_id)
    if not books:
        pinecone_store.delete_namespace(namespace)
        return 0

    items = _books_to_vectors(books)
    pinecone_store.delete_namespace(namespace)
    pinecone_store.upsert_vectors(namespace, items)
    return len(items)


def upsert_catalog_book(book: dict) -> int:
    if _skip_embedding_sync():
        return 0

    items = _books_to_vectors([book])
    pinecone_store.upsert_vectors(pinecone_store.CATALOG_NAMESPACE, items)
    return 1
