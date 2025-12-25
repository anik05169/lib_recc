from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["library_db"]

def get_mongo_db():
    return db
