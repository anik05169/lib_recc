from app.db.mongo import get_mongo_db
from app.services.recommender import train_model

def train_recommender_on_startup():
    """
    Train recommender once when FastAPI starts
    """
    db = get_mongo_db()
    books = list(db.books.find({}, {"_id": 0}))

    if not books:
        print("⚠️ No books found. Recommender not trained.")
        return

    train_model(books)
    print(f"✅ Recommender trained on startup with {len(books)} books")

