#!/usr/bin/env python3
"""Seed the books catalog from library_db.books.json (repo root).

Usage (from backend/ with venv active):
    python scripts/seed_catalog.py
    python scripts/seed_catalog.py --force   # replace existing catalog

Requires MONGODB_URI in environment or backend/.env
"""

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

# Allow running as: python scripts/seed_catalog.py
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from app.db.mongo import get_mongo_db  # noqa: E402


def load_seed_books() -> list[dict]:
    seed_path = Path(__file__).resolve().parents[2] / "library_db.books.json"
    if not seed_path.exists():
        raise FileNotFoundError(f"Seed file not found: {seed_path}")

    with seed_path.open(encoding="utf-8") as f:
        raw = json.load(f)

    books = []
    for doc in raw:
        book = {k: v for k, v in doc.items() if k != "_id"}
        books.append(book)
    return books


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed MongoDB books catalog")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Delete existing books and re-import seed data",
    )
    args = parser.parse_args()

    db = get_mongo_db()
    existing = db.books.count_documents({})

    if existing and not args.force:
        print(f"Catalog already has {existing} books. Use --force to replace.")
        return 0

    books = load_seed_books()
    if args.force and existing:
        db.books.delete_many({})
        print(f"Removed {existing} existing books.")

    if books:
        db.books.insert_many(books)

    print(f"Seeded {len(books)} books into library_db.books")
    print("Restart the API or POST /train (admin) to retrain the recommender.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
