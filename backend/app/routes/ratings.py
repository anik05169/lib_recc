from fastapi import APIRouter, HTTPException, Depends, Body
from app.db.mongo import get_mongo_db
from app.models.schemas import Rating
from app.core.auth import get_current_user

router = APIRouter(prefix="/ratings", tags=["Ratings"])


@router.post("")
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


@router.get("/average")
def average_ratings():
    db = get_mongo_db()
    pipeline = [
        {"$group": {"_id": "$book_id", "avg_rating": {"$avg": "$rating"}}}
    ]
    return list(db.ratings.aggregate(pipeline))


@router.get("/mine")
def get_my_ratings(current_user: dict = Depends(get_current_user)):
    """Get the current user's ratings for all books they've rated."""
    db = get_mongo_db()
    user_id = str(current_user["_id"])
    return list(db.ratings.find({"user_id": user_id}, {"_id": 0, "book_id": 1, "rating": 1}))
