from fastapi import APIRouter, HTTPException
from app.db.mongo import get_mongo_db
from app.models.schemas import Rating

router = APIRouter(prefix="", tags=["Ratings"])

@router.post("/rate")
def rate_book(rating: Rating):
    if rating.rating < 1 or rating.rating > 5:
        raise HTTPException(400, "Rating must be between 1 and 5")

    db = get_mongo_db()

    exists = db.user_books.find_one(
        {"user_id": rating.user_id, "book_id": rating.book_id}
    )
    if not exists:
        raise HTTPException(400, "Book not in user library")

    db.ratings.update_one(
        {"user_id": rating.user_id, "book_id": rating.book_id},
        {"$set": rating.dict()},
        upsert=True,
    )

    return {"message": "Rating saved"}


@router.get("/ratings/average")
def average_ratings():
    db = get_mongo_db()
    pipeline = [
        {"$group": {"_id": "$book_id", "avg_rating": {"$avg": "$rating"}}}
    ]
    return list(db.ratings.aggregate(pipeline))
