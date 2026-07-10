#!/usr/bin/env python3
"""
Sync MongoDB book vectors to Pinecone (run locally or in CI — not on Render API).

Usage:
  python scripts/sync_pinecone_index.py --scope catalog
  python scripts/sync_pinecone_index.py --scope user --user-id <mongo_user_id>
  python scripts/sync_pinecone_index.py --scope all
  python scripts/sync_pinecone_index.py --scope catalog --books-file library_db.books.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))
load_dotenv(BACKEND_DIR / ".env")

from app.db.mongo import get_mongo_db  # noqa: E402
from app.services import pinecone_store  # noqa: E402
from app.services.vector_sync import (  # noqa: E402
    sync_catalog_to_pinecone,
    sync_user_library_to_pinecone,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync book embeddings to Pinecone")
    parser.add_argument(
        "--scope",
        choices=["catalog", "user", "all"],
        default="catalog",
        help="What to sync (default: catalog)",
    )
    parser.add_argument("--user-id", default="", help="Required when --scope user")
    parser.add_argument(
        "--books-file",
        default="",
        help="Optional JSON array of books (catalog scope only, skips MongoDB)",
    )
    return parser.parse_args()


def _load_catalog_books(books_file: str) -> list[dict]:
    if books_file:
        path = Path(books_file)
        if not path.is_absolute():
            path = (REPO_ROOT / path).resolve()
        with path.open(encoding="utf-8") as f:
            raw = json.load(f)
        if not isinstance(raw, list):
            raise ValueError("Books file must be a JSON array")
        return [{k: v for k, v in b.items() if k != "_id"} for b in raw if isinstance(b, dict)]

    db = get_mongo_db()
    return list(db.books.find({}, {"_id": 0}))


def main() -> int:
    args = _parse_args()

    if not pinecone_store.is_configured():
        print("Error: set PINECONE_API_KEY and PINECONE_INDEX_NAME in backend/.env")
        return 1

    # Ensure sync runs even when production API sets SKIP_EMBEDDING_SYNC
    os.environ.pop("SKIP_EMBEDDING_SYNC", None)

    if args.scope in {"catalog", "all"}:
        books = _load_catalog_books(args.books_file)
        if not books:
            print("No catalog books found.")
            return 1
        count = sync_catalog_to_pinecone(books)
        print(f"Synced {count} vectors to namespace '{pinecone_store.CATALOG_NAMESPACE}'")

    if args.scope in {"user", "all"}:
        if not args.user_id:
            print("Error: --user-id is required for user scope")
            return 1
        db = get_mongo_db()
        user_books = list(db.user_books.find({"user_id": args.user_id}, {"_id": 0}))
        count = sync_user_library_to_pinecone(args.user_id, user_books)
        ns = pinecone_store.user_namespace(args.user_id)
        print(f"Synced {count} vectors to namespace '{ns}'")

    stats = pinecone_store.get_namespace_vector_count(pinecone_store.CATALOG_NAMESPACE)
    print(f"Catalog vector count: {stats}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
