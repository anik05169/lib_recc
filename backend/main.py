from fastapi import FastAPI, HTTPException
from .db_mongo import get_mongo_db
from .recommender import train_model, recommend

app = FastAPI(title="Library Recommendation System")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
from pydantic import BaseModel

class Book(BaseModel):
    book_id: int
    title: str
    description: str

@app.post("/add-book")
def add_book(book: Book):
    db = get_mongo_db()

    # prevent duplicate book_id
    if db.books.find_one({"book_id": book.book_id}):
        raise HTTPException(status_code=400, detail="Book ID already exists")

    db.books.insert_one(book.dict())
    return {"message": "Book added"}




@app.get("/")
def root():
    return {"message": "Library Recommendation System API"}



@app.get("/books")
def get_books():
    db = get_mongo_db()
    return list(db.books.find({}, {"_id": 0}))


@app.post("/train")
def train():
    db = get_mongo_db()
    books = list(db.books.find({}, {"_id": 0}))

    if not books:
        raise HTTPException(status_code=400, detail="No books found in database")

    train_model(books)
    return {"message": "Model trained successfully"}



@app.get("/recommend/{book_id}")
def recommend_books(book_id: int):
    results = recommend(book_id)

    if not results:
        raise HTTPException(status_code=404, detail="No recommendations found")

    return results



@app.post("/activity")
def log_activity(user_id: int, book_id: int, action: str):
    db = get_mongo_db()
    db.user_activity.insert_one({
        "user_id": user_id,
        "book_id": book_id,
        "action": action
    })
    return {"status": "logged"}
#wow
class Rating(BaseModel):
    user_id: int
    book_id: int
    rating: int  # 1 to 5

@app.post("/rate")
def rate_book(rating: Rating):
    db = get_mongo_db()

    if rating.rating < 1 or rating.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be 1–5")

    db.ratings.update_one(
        {"user_id": rating.user_id, "book_id": rating.book_id},
        {"$set": rating.dict()},
        upsert=True
    )

    return {"message": "Rating saved"}

@app.get("/ratings/average")
def average_ratings():
    db = get_mongo_db()

    pipeline = [
        {"$group": {"_id": "$book_id", "avg_rating": {"$avg": "$rating"}}}
    ]

    return list(db.ratings.aggregate(pipeline))
