#books.py

import time
from fastapi import APIRouter, Depends, Query
from app.db.mongo import get_mongo_db
from app.models.schemas import Book
from app.services.recommender import recommend, train_model
from app.services.hf_recommender import recommend_books_hf
from app.core.auth import get_current_user


router = APIRouter(prefix="", tags=["Books"])


@router.get("/books")
def get_books(
    search: str = Query(None, description="Search books by title or description"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Books per page"),
):
    db = get_mongo_db()
    query = {}
    if search:
        query = {
            "$or": [
                {"title": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}},
            ]
        }

    skip = (page - 1) * limit
    total = db.books.count_documents(query)
    books = list(db.books.find(query, {"_id": 0}).skip(skip).limit(limit))
    return {
        "books": books,
        "total": total,
        "page": page,
        "pages": max(1, (total + limit - 1) // limit),
    }


@router.post("/books")
def add_book(book: Book, current_user: dict = Depends(get_current_user)):
    """Add a book to the global catalog (authenticated)."""
    db = get_mongo_db()
    book_data = book.model_dump()
    book_data.setdefault("image_url", "/placeholder.jpg")
    if not book_data.get("book_id"):
        book_data["book_id"] = int(time.time() * 1000) % 10_000_000
    db.books.insert_one(book_data)
    return {"status": "ok", "book_id": book_data["book_id"]}


@router.get("/recommend/{book_id}")
def recommend_books(book_id: int):
    return recommend(book_id) or []


@router.post("/train")
def train(current_user: dict = Depends(get_current_user)):
    """Retrain the recommender model (authenticated)."""
    db = get_mongo_db()
    books = list(db.books.find({}, {"_id": 0}))
    train_model(books)
    return {"message": "Recommender trained successfully"}


@router.post("/books/ai-suggest-new")
def ai_suggest_new_books(payload: dict, current_user: dict = Depends(get_current_user)):
    """Get AI-powered book suggestions (authenticated)."""
    description = payload["description"]
    return recommend_books_hf(description)
