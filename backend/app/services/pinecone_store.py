"""Pinecone vector store wrapper for catalog and per-user recommendation namespaces."""

import os
import threading
from typing import Any

_lock = threading.Lock()
_client = None
_index = None

CATALOG_NAMESPACE = "catalog"

# In-process caches — avoid describe_index_stats / fetch on the hot path.
_namespace_ready: dict[str, bool] = {}
_namespace_counts: dict[str, int] = {}
_vector_cache: dict[str, dict[str, list[float]]] = {}


def user_namespace(user_id: str) -> str:
    return f"user_{user_id}"


def _pinecone_disabled() -> bool:
    return os.getenv("PINECONE_DISABLED", "").strip().lower() in {"1", "true", "yes"}


def _get_index():
    global _client, _index
    if _pinecone_disabled():
        return None

    with _lock:
        if _index is not None:
            return _index

        api_key = os.getenv("PINECONE_API_KEY", "").strip()
        index_name = os.getenv("PINECONE_INDEX_NAME", "").strip()
        if not api_key or not index_name:
            return None

        from pinecone import Pinecone

        _client = Pinecone(api_key=api_key)
        _index = _client.Index(index_name)
        return _index


def _clear_namespace_cache(namespace: str) -> None:
    with _lock:
        _namespace_ready.pop(namespace, None)
        _namespace_counts.pop(namespace, None)
        _vector_cache.pop(namespace, None)


def _cache_vectors(namespace: str, items: list[dict[str, Any]]) -> None:
    with _lock:
        store = _vector_cache.setdefault(namespace, {})
        for item in items:
            values = item.get("values")
            if values is not None:
                store[item["id"]] = values


def _field(obj: Any, key: str, default: Any = None) -> Any:
    """Read a field from a dict or Pinecone SDK dataclass/OpenAPI model."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    if hasattr(obj, key):
        value = getattr(obj, key)
        return default if value is None else value
    getter = getattr(obj, "get", None)
    if callable(getter):
        try:
            return getter(key, default)
        except TypeError:
            return getter(key) if getter(key) is not None else default
    return default


def mark_namespace_ready(namespace: str, vector_count: int) -> None:
    with _lock:
        _namespace_ready[namespace] = vector_count > 0
        _namespace_counts[namespace] = vector_count


def warm_namespace_cache(namespace: str) -> bool:
    """One-time Pinecone stats fetch to populate readiness caches (startup/health only)."""
    if _pinecone_disabled():
        ready = _test_store_has_namespace(namespace)
        count = len(_test_store.get(namespace, {}))
        mark_namespace_ready(namespace, count)
        return ready

    index = _get_index()
    if index is None:
        return False
    try:
        stats = index.describe_index_stats()
        namespaces = _field(stats, "namespaces") or {}
        if isinstance(namespaces, dict):
            ns_stats = namespaces.get(namespace) or {}
        else:
            ns_stats = _field(namespaces, namespace) or {}
        count = int(_field(ns_stats, "vector_count") or 0)
        mark_namespace_ready(namespace, count)
        return count > 0
    except Exception:
        return False


def is_configured() -> bool:
    if _pinecone_disabled():
        return True
    return bool(os.getenv("PINECONE_API_KEY", "").strip() and os.getenv("PINECONE_INDEX_NAME", "").strip())


def is_connected() -> bool:
    if _pinecone_disabled():
        return True
    index = _get_index()
    if index is None:
        return False
    try:
        index.describe_index_stats()
        return True
    except Exception:
        return False


def is_namespace_ready(namespace: str) -> bool:
    if _pinecone_disabled():
        return _test_store_has_namespace(namespace)

    with _lock:
        if namespace in _namespace_ready:
            return _namespace_ready[namespace]
    return False


def get_namespace_vector_count(namespace: str) -> int:
    if _pinecone_disabled():
        return len(_test_store.get(namespace, {}))

    with _lock:
        if namespace in _namespace_counts:
            return _namespace_counts[namespace]
    warm_namespace_cache(namespace)
    with _lock:
        return _namespace_counts.get(namespace, 0)


def upsert_vectors(namespace: str, items: list[dict[str, Any]]) -> None:
    if not items:
        return

    if _pinecone_disabled():
        store = _test_store.setdefault(namespace, {})
        for item in items:
            store[item["id"]] = item
        mark_namespace_ready(namespace, len(store))
        _cache_vectors(namespace, items)
        return

    index = _get_index()
    if index is None:
        raise RuntimeError("Pinecone is not configured. Set PINECONE_API_KEY and PINECONE_INDEX_NAME.")

    batch_size = 100
    for start in range(0, len(items), batch_size):
        batch = items[start : start + batch_size]
        index.upsert(vectors=batch, namespace=namespace)

    with _lock:
        prev = _namespace_counts.get(namespace, 0)
    mark_namespace_ready(namespace, prev + len(items))
    _cache_vectors(namespace, items)


def delete_namespace(namespace: str) -> None:
    if _pinecone_disabled():
        _test_store.pop(namespace, None)
        _clear_namespace_cache(namespace)
        return

    index = _get_index()
    if index is None:
        return
    try:
        index.delete(delete_all=True, namespace=namespace)
    except Exception:
        pass
    _clear_namespace_cache(namespace)


def fetch_vector(namespace: str, book_id: int) -> list[float] | None:
    vector_id = str(book_id)

    with _lock:
        cached = _vector_cache.get(namespace, {}).get(vector_id)
    if cached is not None:
        return cached

    if _pinecone_disabled():
        item = _test_store.get(namespace, {}).get(vector_id)
        if item:
            _cache_vectors(namespace, [item])
            return item["values"]
        return None

    index = _get_index()
    if index is None:
        return None

    try:
        result = index.fetch(ids=[vector_id], namespace=namespace)
        vectors = _field(result, "vectors") or {}
        if isinstance(vectors, dict):
            record = vectors.get(vector_id)
        else:
            record = _field(vectors, vector_id)
        if not record:
            return None
        values = _field(record, "values")
        if values is not None:
            values = list(values)
            _cache_vectors(namespace, [{"id": vector_id, "values": values}])
        return values
    except Exception:
        return None


def query_similar(
    namespace: str,
    vector: list[float],
    top_k: int,
    exclude_id: int | None = None,
) -> list[dict[str, Any]]:
    if _pinecone_disabled():
        return _test_query_similar(namespace, vector, top_k, exclude_id)

    index = _get_index()
    if index is None:
        return []

    try:
        result = index.query(
            vector=vector,
            top_k=top_k,
            namespace=namespace,
            include_metadata=True,
        )
        matches = _field(result, "matches") or []
        hits = []
        for match in matches:
            book_id = _book_id_from_match(match, exclude_id)
            if book_id is None:
                continue
            hits.append(
                {
                    "book_id": book_id,
                    "score": float(_field(match, "score") or 0.0),
                    "metadata": dict(_field(match, "metadata") or {}),
                }
            )
        return hits
    except Exception:
        return []


def _book_id_from_match(match: Any, exclude_id: int | None) -> int | None:
    metadata = _field(match, "metadata") or {}
    if not isinstance(metadata, dict):
        metadata = dict(metadata) if metadata else {}
    raw_id = metadata.get("book_id") if isinstance(metadata, dict) else _field(metadata, "book_id")
    if raw_id is None:
        raw_id = _field(match, "id")
    if raw_id is None:
        return None
    book_id = int(raw_id)
    if exclude_id is not None and book_id == exclude_id:
        return None
    return book_id


# In-memory store for unit tests (PINECONE_DISABLED=true)
_test_store: dict[str, dict[str, dict[str, Any]]] = {}


def reset_test_store() -> None:
    _test_store.clear()
    with _lock:
        _namespace_ready.clear()
        _namespace_counts.clear()
        _vector_cache.clear()


def _test_store_has_namespace(namespace: str) -> bool:
    return bool(_test_store.get(namespace))


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


def _test_query_similar(
    namespace: str,
    vector: list[float],
    top_k: int,
    exclude_id: int | None,
) -> list[dict[str, Any]]:
    store = _test_store.get(namespace, {})
    scored = []
    for vector_id, item in store.items():
        book_id = int((item.get("metadata") or {}).get("book_id") or vector_id)
        if exclude_id is not None and book_id == exclude_id:
            continue
        score = _cosine(vector, item["values"])
        scored.append(
            {
                "book_id": book_id,
                "score": score,
                "metadata": item.get("metadata") or {},
            }
        )
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]
