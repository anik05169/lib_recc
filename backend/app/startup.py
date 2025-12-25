from app.db.mongo import get_mongo_db
from app.services.recommender import train_model

def train_on_startup():
    db = get_mongo_db()
    books = list(db.books.find({}, {"_id": 0}))

    if books:
        train_model(books)
        print("✅ Recommender trained on startup")
    else:
        print("⚠️ No books found, model not trained")
