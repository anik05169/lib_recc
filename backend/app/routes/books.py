from fastapi import APIRouter
from app.db.mongo import get_mongo_db
from app.services.recommender import recommend

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
