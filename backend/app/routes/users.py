import time
from fastapi import APIRouter, HTTPException, Depends, Body
from app.db.mongo import get_mongo_db
from app.models.schemas import Book
from app.core.auth import get_current_user
from app.services.recommender import train_user_model, recommend_user

router = APIRouter(prefix="/user", tags=["Users"])


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

    # Retrain the user's personal recommendation model
    user_books = list(db.user_books.find({"user_id": user_id}, {"_id": 0}))
    train_user_model(user_id, user_books)

    return {"message": "Book added to user library"}


@router.post("/add-custom-book")
def add_custom_book(
    book: Book = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """Add a custom book to user's library only (not global catalog) and retrain user model."""
    db = get_mongo_db()
    user_id = str(current_user["_id"])
    book_data = book.model_dump()

    # Auto-generate book_id if not provided
    if not book_data.get("book_id"):
        book_data["book_id"] = int(time.time() * 1000) % 10_000_000

    # Check if user already has this book in their library
    existing = db.user_books.find_one(
        {"user_id": user_id, "book_id": book_data["book_id"]}
    )
    if existing:
        raise HTTPException(status_code=400, detail="Book already in your library")

    # Add only to user's library, not to global catalog
    db.user_books.insert_one(
        {**book_data, "user_id": user_id, "source": "custom"}
    )

    # Retrain the user's personal recommendation model
    user_books = list(db.user_books.find({"user_id": user_id}, {"_id": 0}))
    train_user_model(user_id, user_books)

    return {"message": "Custom book added to your library", "book_id": book_data["book_id"]}


@router.delete("/library/{book_id}")
def delete_from_library(book_id: int, current_user: dict = Depends(get_current_user)):
    """Remove a book from user's library."""
    db = get_mongo_db()
    user_id = str(current_user["_id"])

    result = db.user_books.delete_one({"user_id": user_id, "book_id": book_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Book not found in your library")

    # Also remove the user's rating for this book
    db.ratings.delete_one({"user_id": user_id, "book_id": book_id})

    # Retrain the user's personal recommendation model
    user_books = list(db.user_books.find({"user_id": user_id}, {"_id": 0}))
    train_user_model(user_id, user_books)

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
    current_user: dict = Depends(get_current_user)
):
    """Get recommendations for a book from user's personal library."""
    db = get_mongo_db()
    user_id = str(current_user["_id"])
    
    # Get user's books to train model if needed
    user_books = list(db.user_books.find({"user_id": user_id}, {"_id": 0}))
    recommendations = recommend_user(user_id, book_id, user_books=user_books)
    return recommendations or []
