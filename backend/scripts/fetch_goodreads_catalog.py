#!/usr/bin/env python3
"""Download goodbooks-10k CSV and export unique English titles to seed JSON."""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

import requests

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "scripts"))

from csv_to_books_json import convert  # noqa: E402

GOODBOOKS_10K_URL = (
    "https://raw.githubusercontent.com/zygmuntz/goodbooks-10k/master/books.csv"
)
DEFAULT_OUTPUT = REPO_ROOT / "library_db.books.goodreads.json"


def download_csv(url: str, dest: Path) -> None:
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    dest.write_bytes(response.content)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch Goodreads goodbooks-10k and write library seed JSON"
    )
    parser.add_argument("--url", default=GOODBOOKS_10K_URL, help="CSV download URL")
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Output JSON path (default: library_db.books.goodreads.json)",
    )
    parser.add_argument(
        "--csv",
        default="",
        help="Use an existing CSV instead of downloading",
    )
    args = parser.parse_args()

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = (REPO_ROOT / output_path).resolve()

    if args.csv:
        csv_path = Path(args.csv)
        if not csv_path.is_absolute():
            csv_path = (REPO_ROOT / csv_path).resolve()
    else:
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            csv_path = Path(tmp.name)
        print(f"Downloading {args.url} ...")
        download_csv(args.url, csv_path)

    count = convert(csv_path, output_path, limit=0)
    print(f"Wrote {count} unique English books to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
