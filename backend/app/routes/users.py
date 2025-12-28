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

    # Check if user already has this book in their library
    existing = db.user_books.find_one(
        {"user_id": user_id, "book_id": book.book_id}
    )
    if existing:
        raise HTTPException(status_code=400, detail="Book already in your library")

    # Add only to user's library, not to global catalog
    db.user_books.insert_one(
        {**book.dict(), "user_id": user_id, "source": "custom"}
    )

    # Retrain the user's personal recommendation model
    user_books = list(db.user_books.find({"user_id": user_id}, {"_id": 0}))
    train_user_model(user_id, user_books)

    return {"message": "Custom book added to your library"}


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
