from fastapi import APIRouter, HTTPException, Depends, Body
from app.db.mongo import get_mongo_db
from app.models.schemas import Rating
from app.core.auth import get_current_user

router = APIRouter(prefix="", tags=["Ratings"])

@router.post("/rate")
def rate_book(
    book_id: int = Body(...),
    rating: int = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """Rate a book (1-5)."""
    if rating < 1 or rating > 5:
        raise HTTPException(400, "Rating must be between 1 and 5")

    db = get_mongo_db()
    user_id = str(current_user["_id"])

    exists = db.user_books.find_one(
        {"user_id": user_id, "book_id": book_id}
    )
    if not exists:
        raise HTTPException(400, "Book not in user library")

    db.ratings.update_one(
        {"user_id": user_id, "book_id": book_id},
        {"$set": {"user_id": user_id, "book_id": book_id, "rating": rating}},
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
