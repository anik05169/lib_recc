from app.db.mongo import get_mongo_db
from app.services.recommender import train_model
from pymongo.errors import ServerSelectionTimeoutError

def train_recommender_on_startup():
    """
    Train recommender once when FastAPI starts
    """
    try:
        db = get_mongo_db()
        # Test connection with a short timeout
        books = list(db.books.find({}, {"_id": 0}))

        if not books:
            print("No books found. Recommender not trained.")
            return

        train_model(books)
        print(f"Recommender trained on startup with {len(books)} books")
    except ServerSelectionTimeoutError:
        print("Could not connect to MongoDB. Recommender not trained.")
        print("Hint: Check if your IP address is whitelisted in MongoDB Atlas.")
    except Exception as e:
        print(f"Error during recommender startup: {e}")



