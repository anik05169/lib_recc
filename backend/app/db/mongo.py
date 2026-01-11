import os
from pymongo import MongoClient

MONGODB_URI = os.getenv("MONGODB_URI")

if not MONGODB_URI:
    raise RuntimeError("MONGODB_URI environment variable is not set")

client = MongoClient(MONGODB_URI)

# Uses the database name from the URI
db = client.get_default_database()

def get_mongo_db():
    return db
