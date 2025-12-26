from fastapi import APIRouter, HTTPException
from app.db.mongo import get_mongo_db
from app.models.schemas import Book
from app.services.recommender import train_model

router = APIRouter(prefix="/user", tags=["Users"])

@router.get("/library/{user_id}")
def get_user_library(user_id: int):
    db = get_mongo_db()
    return list(db.user_books.find({"user_id": user_id}, {"_id": 0}))


@router.post("/add-from-catalog")
def add_from_catalog(user_id: int, book_id: int):
    db = get_mongo_db()

    book = db.books.find_one({"book_id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    db.user_books.update_one(
        {"user_id": user_id, "book_id": book_id},
        {"$set": {**book, "user_id": user_id, "source": "catalog"}},
        upsert=True,
    )

    return {"message": "Book added to user library"}

from fastapi import Body
@router.post("/add-custom-book")
def add_custom_book(
    user_id: int,
    book: Book = Body(...)
):
    db = get_mongo_db()

    if db.books.find_one({"book_id": book.book_id}):
        raise HTTPException(status_code=400, detail="Book already exists")

    db.books.insert_one(book.dict())

    books = list(db.books.find({}, {"_id": 0}))
    train_model(books)

    db.user_books.insert_one(
        {**book.dict(), "user_id": user_id, "source": "custom"}
    )

    return {"message": "Custom book added and model retrained"}
