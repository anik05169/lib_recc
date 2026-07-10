#books.py

import re
import time
from fastapi import APIRouter, Depends, HTTPException, Query
from app.db.mongo import get_mongo_db
from app.db.ratings_util import get_avg_ratings_map
from app.models.schemas import AiSuggestionRequest, Book
from app.services.recommender import (
    DEFAULT_PLACEHOLDER_IMAGE,
    get_ratings_map,
    is_model_ready,
    recommend,
    set_ratings_map,
    train_model,
    upsert_book,
)
from app.services.hf_recommender import HFNotConfiguredError, recommend_books_hf
from app.core.auth import get_current_user, require_admin


router = APIRouter(prefix="", tags=["Books"])


@router.get("/books")
def get_books(
    search: str = Query(None, description="Search books by title or description"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Books per page"),
):
    db = get_mongo_db()
    query = {}
    normalized_search = search.strip() if search else None
    if normalized_search:
        escaped_search = re.escape(normalized_search)
        query = {
            "$or": [
                {"title": {"$regex": escaped_search, "$options": "i"}},
                {"description": {"$regex": escaped_search, "$options": "i"}},
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
def add_book(book: Book, _admin: dict = Depends(require_admin)):
    """Add a book to the global catalog (admin only)."""
    db = get_mongo_db()
    book_data = book.model_dump()
    book_data.setdefault("image_url", DEFAULT_PLACEHOLDER_IMAGE)
    if not book_data.get("book_id"):
        book_data["book_id"] = int(time.time() * 1000) % 10_000_000
    db.books.insert_one(book_data)

    ratings_map = get_avg_ratings_map(db)
    upsert_book(book_data)
    set_ratings_map(ratings_map)

    return {"status": "ok", "book_id": book_data["book_id"]}


@router.get("/recommend/{book_id}")
def recommend_books(book_id: int):
    if not is_model_ready():
        raise HTTPException(
            status_code=503,
            detail="Recommender model is not ready yet",
        )
    ratings_map = get_ratings_map()
    result = recommend(book_id, ratings_map=ratings_map)
    if result is None:
        raise HTTPException(
            status_code=503,
            detail="Recommender model is not ready yet",
        )
    return result


@router.post("/train")
def train(_admin: dict = Depends(require_admin)):
    """Retrain the global recommender model (admin only)."""
    db = get_mongo_db()
    books = list(db.books.find({}, {"_id": 0}))
    ratings_map = get_avg_ratings_map(db)
    train_model(books, ratings_map)
    return {"message": "Recommender trained successfully"}


@router.post("/books/ai-suggest-new")
def ai_suggest_new_books(
    payload: AiSuggestionRequest,
    current_user: dict = Depends(get_current_user),
):
    """Get AI-powered book suggestions (authenticated)."""
    try:
        return recommend_books_hf(payload.description)
    except HFNotConfiguredError:
        raise HTTPException(
            status_code=503,
            detail="AI suggestions are not configured",
        )
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="AI suggestion service unavailable",
        )
