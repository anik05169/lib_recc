from fastapi import APIRouter
from app.db.mongo import get_mongo_db
from app.services.recommender import recommend
from app.services.ai_recommender import suggest_books_from_description

router = APIRouter(prefix="", tags=["Books"])

@router.get("/books")
def get_books():
    db = get_mongo_db()
    return list(db.books.find({}, {"_id": 0}))


@router.get("/recommend/{book_id}")
def recommend_books(book_id: int):
    return recommend(book_id) or []

from app.services.recommender import train_model

@router.post("/train")
def train():
    db = get_mongo_db()
    books = list(db.books.find({}, {"_id": 0}))
    train_model(books)
    return {"message": "Recommender trained successfully"}

@router.post("/books/ai-suggest")
def ai_suggest_books(payload: dict):
    """
    payload = {
        "description": "...",
        "user_id": "..."
    }
    """

    db = get_mongo_db()
    user_description = payload["description"]

    # You can restrict to user's library later if needed
    books = list(
        db.books.find(
            {},
            {"_id": 0, "title": 1, "description": 1}
        )
    )

    suggestions = suggest_books_from_description(
        user_description=user_description,
        books=books
    )

    return {"suggestions": suggestions}

from app.services.hf_recommender import recommend_books_hf

@router.post("/books/ai-suggest-new")
def ai_suggest_new_books(payload: dict):
    description = payload["description"]
    return {"recommendations": recommend_books_hf(description)}
