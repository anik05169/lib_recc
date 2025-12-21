from pymongo import MongoClient

MONGO_URL = "mongodb://localhost:27017/"
DB_NAME = "library_db"

def get_mongo_db():
    """
    Create and return a MongoDB database connection.
    Connection is created ONLY when this function is called.
    """
    client = MongoClient(MONGO_URL)
    return client[DB_NAME]
