import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI") or os.getenv("MONGO_URI") or "mongodb://localhost:27017/"

printed_uri = MONGO_URI.split("@")[-1] if "@" in MONGO_URI else MONGO_URI
print(f"Connecting to MongoDB at: ...@{printed_uri}")

client = None
db = None
_indexes_ensured = False


def get_mongo_db():
    global client, db, _indexes_ensured
    if db is None:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client["library_db"]
    if not _indexes_ensured:
        ensure_indexes(db)
        _indexes_ensured = True
    return db


def ensure_indexes(database):
    """Create indexes idempotently on first connection."""
    try:
        database.users.create_index("email", unique=True)
        database.books.create_index("book_id", unique=True)
        database.user_books.create_index(
            [("user_id", 1), ("book_id", 1)], unique=True
        )
        database.ratings.create_index(
            [("user_id", 1), ("book_id", 1)], unique=True
        )
        print("MongoDB indexes ensured")
    except Exception as e:
        print(f"Warning: could not ensure all indexes (duplicates may exist): {e}")
