from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .db_mongo import get_mongo_db
from .recommender import train_model, recommend

app = FastAPI(title="Personal Library System")

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- MODELS ----------------

class Book(BaseModel):
    book_id: int
    title: str
    description: str


class Rating(BaseModel):
    user_id: int
    book_id: int
    rating: int  # 1–5


# ---------------- STARTUP AUTO-TRAIN ----------------

@app.on_event("startup")
def startup_train():
    """
    Automatically train model when backend starts
    """
    db = get_mongo_db()
    books = list(db.books.find({}, {"_id": 0}))

    if books:
        train_model(books)
        print("✅ Recommender model trained on startup")
    else:
        print("⚠️ No books found, model not trained")


# ---------------- ROOT ----------------

@app.get("/")
def root():
    return {"message": "Personal Library API running"}


# ---------------- CATALOG (GLOBAL BOOKS) ----------------

@app.get("/books")
def get_books():
    db = get_mongo_db()
    return list(db.books.find({}, {"_id": 0}))


@app.get("/recommend/{book_id}")
def recommend_books(book_id: int):
    results = recommend(book_id)

    if not results:
        return []  # return empty list instead of error

    return results


# ---------------- USER LIBRARY ----------------

@app.get("/user/library/{user_id}")
def get_user_library(user_id: int):
    db = get_mongo_db()
    return list(db.user_books.find({"user_id": user_id}, {"_id": 0}))


@app.post("/user/add-from-catalog")
def add_from_catalog(user_id: int, book_id: int):
    db = get_mongo_db()

    book = db.books.find_one({"book_id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    db.user_books.update_one(
        {"user_id": user_id, "book_id": book_id},
        {
            "$set": {
                **book,
                "user_id": user_id,
                "source": "catalog",
            }
        },
        upsert=True,
    )

    return {"message": "Book added to user library"}


@app.post("/user/add-custom-book")
def add_custom_book(user_id: int, book: Book):
    """
    Add a new book AND retrain model
    """
    db = get_mongo_db()

    if db.books.find_one({"book_id": book.book_id}):
        raise HTTPException(
            status_code=400,
            detail="Book ID already exists in catalog",
        )

    # Add to catalog
    db.books.insert_one(book.dict())

    # Retrain model
    books = list(db.books.find({}, {"_id": 0}))
    train_model(books)

    print("🔁 Model retrained after adding book")

    # Add to user's library as custom
    db.user_books.insert_one(
        {
            **book.dict(),
            "user_id": user_id,
            "source": "custom",
        }
    )

    return {"message": "Book added and model retrained"}


# ---------------- RATINGS ----------------

@app.post("/rate")
def rate_book(rating: Rating):
    db = get_mongo_db()

    if rating.rating < 1 or rating.rating > 5:
        raise HTTPException(
            status_code=400,
            detail="Rating must be between 1 and 5",
        )

    # Ensure book exists in user's library
    exists = db.user_books.find_one(
        {"user_id": rating.user_id, "book_id": rating.book_id}
    )
    if not exists:
        raise HTTPException(
            status_code=400,
            detail="Book must be in user's library before rating",
        )

    db.ratings.update_one(
        {"user_id": rating.user_id, "book_id": rating.book_id},
        {"$set": rating.dict()},
        upsert=True,
    )

    return {"message": "Rating saved"}


@app.get("/ratings/average")
def average_ratings():
    db = get_mongo_db()

    pipeline = [
        {
            "$group": {
                "_id": "$book_id",
                "avg_rating": {"$avg": "$rating"},
            }
        }
    ]

    return list(db.ratings.aggregate(pipeline))


