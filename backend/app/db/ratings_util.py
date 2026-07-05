def get_avg_ratings_map(db) -> dict:
    """Return { book_id: avg_rating } from ratings collection."""
    pipeline = [
        {"$group": {"_id": "$book_id", "avg_rating": {"$avg": "$rating"}}}
    ]
    return {
        doc["_id"]: doc["avg_rating"]
        for doc in db.ratings.aggregate(pipeline)
    }
