import os

import pytest

from app.services import pinecone_store
from app.services import recommender as rec


@pytest.fixture(autouse=True)
def reset_model(monkeypatch):
    os.environ["PINECONE_DISABLED"] = "true"
    os.environ.pop("SKIP_EMBEDDING_SYNC", None)
    pinecone_store.reset_test_store()
    rec.set_ratings_map({})
    yield


def _fake_encode(texts: list[str]) -> list[list[float]]:
    vectors = []
    for text in texts:
        t = text.lower()
        if "space" in t or "galaxy" in t or "astronaut" in t:
            vectors.append([0.0, 0.0, 1.0])
        elif "dark" in t:
            vectors.append([0.95, 0.05, 0.0])
        else:
            vectors.append([1.0, 0.0, 0.0])
    return vectors


@pytest.fixture(autouse=True)
def patch_hydrate(monkeypatch):
    def _hydrate(book_ids):
        all_books = SAMPLE_BOOKS
        return {b["book_id"]: b for b in all_books if b["book_id"] in book_ids}

    monkeypatch.setattr("app.services.vector_recommender._hydrate_books", _hydrate)


@pytest.fixture(autouse=True)
def patch_encoder(monkeypatch):
    monkeypatch.setattr(
        "app.services.vector_sync.encode_texts",
        _fake_encode,
    )


SAMPLE_BOOKS = [
    {
        "book_id": 1,
        "title": "Mystery Night",
        "description": "A detective solves crimes in the city",
    },
    {
        "book_id": 2,
        "title": "Dark Detective",
        "description": "A detective investigates murder mysteries",
    },
    {
        "book_id": 3,
        "title": "Space Odyssey",
        "description": "Astronauts travel across the galaxy",
    },
]


def test_train_and_recommend_similar_genre():
    rec.train_model(SAMPLE_BOOKS)
    assert rec.is_model_ready()

    results = rec.recommend(1, top_n=2)
    assert len(results) == 2
    ids = {b["book_id"] for b in results}
    assert 1 not in ids
    assert 2 in ids


def test_recommend_empty_when_untrained():
    assert rec.recommend(1) is None


def test_hybrid_rating_boost():
    rec.train_model(SAMPLE_BOOKS, ratings_map={2: 5.0, 3: 1.0})
    results = rec.recommend(1, top_n=1)
    assert results[0]["book_id"] == 2


def test_title_used_in_features():
    rec.train_model(SAMPLE_BOOKS)
    results = rec.recommend(3, top_n=1)
    assert results[0]["book_id"] != 3


def test_user_model_train_and_recommend():
    user_id = "user-1"
    rec.train_user_model(user_id, SAMPLE_BOOKS[:2])
    results = rec.recommend_user(user_id, 1, top_n=1)
    assert len(results) == 1
    assert results[0]["book_id"] == 2
