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


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = Path(__file__).resolve().parents[1]


def resolve_books_path(books_file: str | None) -> Path:
    if books_file:
        path = Path(books_file)
        if not path.is_absolute():
            path = (REPO_ROOT / path).resolve()
        return path

    for name in ("library_db.books.1000.json", "library_db.books.json"):
        candidate = REPO_ROOT / name
        if candidate.exists():
            return candidate

    raise FileNotFoundError(
        "No seed file found. Pass --books-file or add library_db.books.1000.json to the repo root."
    )


def load_seed_books(books_file: str | None = None) -> list[dict]:
    seed_path = resolve_books_path(books_file)
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
    parser.add_argument(
        "--books-file",
        default="",
        help="Path to books JSON (default: library_db.books.1000.json or library_db.books.json)",
    )
    args = parser.parse_args()

    db = get_mongo_db()
    existing = db.books.count_documents({})

    if existing and not args.force:
        print(f"Catalog already has {existing} books. Use --force to replace.")
        return 0

    books = load_seed_books(args.books_file or None)
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
