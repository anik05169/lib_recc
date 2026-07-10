#!/usr/bin/env python3
"""Convert Goodreads books.csv to library_db.books JSON format."""

import argparse
import csv
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def norm_title(title: str) -> str:
    return re.sub(r"\s+", " ", (title or "").strip().lower())


def synth_description(row: dict) -> str:
    authors = (row.get("authors") or "").strip()
    original_title = (row.get("original_title") or "").strip()
    year = (row.get("original_publication_year") or row.get("publication_date") or "").strip()
    publisher = (row.get("publisher") or "").strip()
    pages = (row.get("num_pages") or "").strip()
    rating = (row.get("average_rating") or "").strip()

    parts = []
    if original_title and original_title.lower() != (row.get("title") or "").strip().lower():
        parts.append(f"Originally titled {original_title}.")
    if authors:
        parts.append(f"Written by {authors}.")
    if publisher:
        parts.append(f"Published by {publisher}.")
    if year:
        year_clean = year.split(".")[0] if "." in year else year
        parts.append(f"First published in {year_clean}.")
    if pages and str(pages).replace(".", "", 1).isdigit():
        parts.append(f"{int(float(pages))} pages.")
    if rating:
        parts.append(f"Goodreads average rating {rating} out of 5.")
    return " ".join(parts) if parts else "No description available."


def convert(csv_path: Path, out_path: Path, limit: int = 1000) -> int:
    books = []
    seen: set[str] = set()

    with csv_path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = (row.get("title") or "").strip()
            if not title:
                continue

            lang = (row.get("language_code") or "").strip().lower()
            if lang and not lang.startswith("en"):
                continue

            key = norm_title(title)
            if key in seen:
                continue
            seen.add(key)

            book = {
                "book_id": len(books) + 1,
                "title": title,
                "description": synth_description(row),
            }

            image_url = (row.get("image_url") or "").strip()
            if image_url and image_url.startswith("http"):
                book["image_url"] = image_url

            books.append(book)
            if len(books) >= limit:
                break

    if len(books) < limit:
        raise RuntimeError(f"Only found {len(books)} unique English books (wanted {limit})")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(books, f, indent=2, ensure_ascii=False)

    return len(books)


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert books.csv to seed JSON")
    parser.add_argument("--csv", default=str(REPO_ROOT / "books.csv"))
    parser.add_argument("--output", default=str(REPO_ROOT / "library_db.books.1000.json"))
    parser.add_argument("--limit", type=int, default=1000)
    args = parser.parse_args()

    count = convert(Path(args.csv), Path(args.output), limit=args.limit)
    print(f"Wrote {count} books to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
