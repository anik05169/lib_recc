import time
from fastapi import APIRouter, HTTPException, Depends, Body
from app.db.mongo import get_mongo_db
from app.db.ratings_util import get_avg_ratings_map
from app.models.schemas import Book
from app.core.auth import get_current_user
from app.services.recommender import (
    get_ratings_map,
    recommend_catalog_for_library_book,
    recommend_user,
    train_user_model,
)

router = APIRouter(prefix="/user", tags=["Users"])


def _retrain_user_model(db, user_id: str):
    user_books = list(db.user_books.find({"user_id": user_id}, {"_id": 0}))
    ratings_map = get_avg_ratings_map(db)
    train_user_model(user_id, user_books, ratings_map)


@router.get("/library")
def get_user_library(current_user: dict = Depends(get_current_user)):
    """Get the current user's library."""
    db = get_mongo_db()
    user_id = str(current_user["_id"])
    return list(db.user_books.find({"user_id": user_id}, {"_id": 0}))


@router.post("/add-from-catalog")
def add_from_catalog(book_id: int, current_user: dict = Depends(get_current_user)):
    """Add a book from catalog to user's library and retrain user model."""
    db = get_mongo_db()
    user_id = str(current_user["_id"])

    book = db.books.find_one({"book_id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    db.user_books.update_one(
        {"user_id": user_id, "book_id": book_id},
        {"$set": {**book, "user_id": user_id, "source": "catalog"}},
        upsert=True,
    )

    _retrain_user_model(db, user_id)
    return {"message": "Book added to user library"}


@router.post("/add-custom-book")
def add_custom_book(
    book: Book = Body(...),
    current_user: dict = Depends(get_current_user),
):
    """Add a custom book to user's library only (not global catalog) and retrain user model."""
    db = get_mongo_db()
    user_id = str(current_user["_id"])
    book_data = book.model_dump()

    if not book_data.get("book_id"):
        book_data["book_id"] = int(time.time() * 1000) % 10_000_000

    existing = db.user_books.find_one(
        {"user_id": user_id, "book_id": book_data["book_id"]}
    )
    if existing:
        raise HTTPException(status_code=400, detail="Book already in your library")

    db.user_books.insert_one(
        {**book_data, "user_id": user_id, "source": "custom"}
    )

    _retrain_user_model(db, user_id)
    return {"message": "Custom book added to your library", "book_id": book_data["book_id"]}


@router.delete("/library/{book_id}")
def delete_from_library(book_id: int, current_user: dict = Depends(get_current_user)):
    """Remove a book from user's library."""
    db = get_mongo_db()
    user_id = str(current_user["_id"])

    result = db.user_books.delete_one({"user_id": user_id, "book_id": book_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Book not found in your library")

    db.ratings.delete_one({"user_id": user_id, "book_id": book_id})
    _retrain_user_model(db, user_id)
    return {"message": "Book removed from your library"}


@router.get("/library/ids")
def get_user_book_ids(current_user: dict = Depends(get_current_user)):
    """Get a list of book IDs in the user's library (for 'already in library' badges)."""
    db = get_mongo_db()
    user_id = str(current_user["_id"])
    books = db.user_books.find({"user_id": user_id}, {"book_id": 1, "_id": 0})
    return [b["book_id"] for b in books]


@router.get("/recommend/{book_id}")
def get_user_recommendations(
    book_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Similar books for a library item: global catalog + in-library matches.

    Returns:
      {
        "catalog": Book[],   # global similar, excluding books already in library
        "library": Book[],   # similar within the user's library
      }
    """
    db = get_mongo_db()
    user_id = str(current_user["_id"])

    user_books = list(db.user_books.find({"user_id": user_id}, {"_id": 0}))
    library_ids = {int(b["book_id"]) for b in user_books if "book_id" in b}
    ratings_map = get_ratings_map()

    library_recs = (
        recommend_user(
            user_id,
            book_id,
            user_books=user_books,
            ratings_map=ratings_map,
        )
        or []
    )

    seed_book = next(
        (b for b in user_books if int(b.get("book_id", -1)) == book_id),
        None,
    )
    catalog_recs = recommend_catalog_for_library_book(
        book_id,
        seed_book=seed_book,
        user_id=user_id,
        top_n=5,
        ratings_map=ratings_map,
        exclude_ids=library_ids,
    )

    return {
        "catalog": catalog_recs,
        "library": library_recs,
    }
