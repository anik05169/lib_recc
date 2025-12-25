import random
import requests
from pymongo import MongoClient

# ---------------- DB CONFIG ----------------
client = MongoClient("mongodb://localhost:27017/")
db = client["library_db"]
books_collection = db["books"]

# ---------------- SETTINGS ----------------
NUM_BOOKS = 50
SEARCH_URL = "https://openlibrary.org/search.json"

# ---------------- EXISTING IDS ----------------
existing_ids = list(books_collection.find({}, {"book_id": 1}))
start_id = max([b["book_id"] for b in existing_ids], default=0) + 1

# ---------------- FETCH MULTIPLE PAGES ----------------
all_docs = []

print("📡 Fetching books from Open Library...")

for page in range(1, 6):  # 5 pages × ~20 results = ~100 books
    params = {
        "q": "fiction",
        "page": page
    }
    res = requests.get(SEARCH_URL, params=params, timeout=10)
    res.raise_for_status()
    data = res.json()
    all_docs.extend(data.get("docs", []))

if len(all_docs) < NUM_BOOKS:
    raise Exception("Not enough books fetched from Open Library")

selected = random.sample(all_docs, NUM_BOOKS)

# ---------------- INSERT ----------------
inserted = 0

for i, book in enumerate(selected):
    title = book.get("title")
    if not title:
        continue

    description = (
        book.get("first_sentence")
        or book.get("subtitle")
        or "No description available."
    )

    # Handle list/dict formats
    if isinstance(description, list):
        description = description[0]
    if isinstance(description, dict):
        description = description.get("value", "No description available.")

    cover_id = book.get("cover_i")
    image_url = (
        f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
        if cover_id
        else "https://via.placeholder.com/128x192?text=No+Cover"
    )

    doc = {
        "book_id": start_id + i,
        "title": title,
        "description": description,
        "image_url": image_url,
    }

    books_collection.insert_one(doc)
    inserted += 1

print(f"✅ Inserted {inserted} books into MongoDB")
