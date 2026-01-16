import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# Try common env var names
MONGO_URI = os.getenv("MONGODB_URI") or os.getenv("MONGO_URI") or "mongodb://localhost:27017/"

# Obfuscate URI for logging
printed_uri = MONGO_URI.split("@")[-1] if "@" in MONGO_URI else MONGO_URI
print(f"🔌 Connecting to MongoDB at: ...@{printed_uri}")

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client["library_db"]

def get_mongo_db():
    return db
