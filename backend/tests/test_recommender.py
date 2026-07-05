import pytest
from app.services import recommender as rec


@pytest.fixture(autouse=True)
def reset_model():
    rec._books_df = None
    rec._similarity = None
    rec._ratings_map = {}
    rec._user_models = {}
    yield


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
