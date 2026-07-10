#!/usr/bin/env python3
"""
Benchmark end-to-end API latency for GET /recommend/{book_id}.

Includes FastAPI + MongoDB ratings fetch + in-process retrieval.

Usage:
  # API must be running (e.g. uvicorn app.main:app --reload)
  python scripts/benchmark_api_latency.py --book-ids 1,2,3 --runs 20
  python scripts/benchmark_api_latency.py --labels eval/relevance_labels.example.json --runs 30
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
import time
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
load_dotenv(BACKEND_DIR / ".env")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark /recommend API latency")
    parser.add_argument("--base-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--book-ids", default="", help="Comma-separated book IDs to query")
    parser.add_argument("--labels", default="", help="JSON labels file; uses query book_ids")
    parser.add_argument("--runs", type=int, default=20, help="Runs per book ID")
    parser.add_argument("--warmup", type=int, default=3, help="Warmup requests per book ID")
    parser.add_argument(
        "--output",
        default="eval/api_latency_latest.json",
        help="Output JSON report path",
    )
    parser.add_argument(
        "--wait-health",
        action="store_true",
        help="Wait until /health reports recommender_ready before benchmarking",
    )
    return parser.parse_args()


def _percentile(sorted_values: list[float], p: float) -> float:
    if not sorted_values:
        return 0.0
    if p <= 0:
        return sorted_values[0]
    if p >= 100:
        return sorted_values[-1]
    pos = (len(sorted_values) - 1) * (p / 100.0)
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return sorted_values[lo]
    frac = pos - lo
    return sorted_values[lo] * (1 - frac) + sorted_values[hi] * frac


def _load_book_ids(args: argparse.Namespace) -> list[int]:
    if args.book_ids:
        return [int(x.strip()) for x in args.book_ids.split(",") if x.strip()]

    if args.labels:
        labels_path = (
            (BACKEND_DIR / args.labels).resolve()
            if not Path(args.labels).is_absolute()
            else Path(args.labels)
        )
        with labels_path.open(encoding="utf-8") as f:
            payload = json.load(f)
        return [int(q["book_id"]) for q in payload.get("queries", [])]

    return [1, 2, 3]


def _wait_for_health(base_url: str, timeout_s: int = 60) -> dict[str, Any]:
    deadline = time.time() + timeout_s
    last = None
    while time.time() < deadline:
        try:
            res = requests.get(f"{base_url.rstrip('/')}/health", timeout=5)
            last = res.json()
            if res.ok and last.get("recommender_ready") and last.get("pinecone_ready", True):
                return last
        except requests.RequestException:
            pass
        time.sleep(1)
    raise RuntimeError(f"API not ready after {timeout_s}s. Last health: {last}")


def _timed_get(url: str) -> tuple[float, int]:
    start = time.perf_counter()
    res = requests.get(url, timeout=30)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    return elapsed_ms, res.status_code


def main() -> int:
    args = _parse_args()
    base_url = args.base_url.rstrip("/")
    book_ids = _load_book_ids(args)
    output_path = (
        (BACKEND_DIR / args.output).resolve()
        if not Path(args.output).is_absolute()
        else Path(args.output)
    )

    if args.runs <= 0:
        raise ValueError("--runs must be > 0")

    health = None
    if args.wait_health:
        health = _wait_for_health(base_url)

    # Warmup
    for _ in range(args.warmup):
        for book_id in book_ids:
            _timed_get(f"{base_url}/recommend/{book_id}")

    latencies_ms: list[float] = []
    status_counts: dict[int, int] = {}
    errors = 0

    for _ in range(args.runs):
        for book_id in book_ids:
            elapsed_ms, status = _timed_get(f"{base_url}/recommend/{book_id}")
            latencies_ms.append(elapsed_ms)
            status_counts[status] = status_counts.get(status, 0) + 1
            if status != 200:
                errors += 1

    if not latencies_ms:
        raise RuntimeError("No latency samples captured")

    latencies_ms.sort()
    mongo_uri = __import__("os").getenv("MONGODB_URI") or __import__("os").getenv("MONGO_URI") or "mongodb://localhost:27017/"
    data_source = mongo_uri.split("@")[-1] if "@" in mongo_uri else mongo_uri

    report = {
        "config": {
            "base_url": base_url,
            "book_ids": book_ids,
            "runs": args.runs,
            "warmup": args.warmup,
            "endpoint": "/recommend/{book_id}",
            "data_source": data_source,
            "backend": "pinecone",
        },
        "health": health,
        "latency_ms": {
            "samples": len(latencies_ms),
            "errors": errors,
            "status_counts": status_counts,
            "mean_ms": statistics.fmean(latencies_ms),
            "p50_ms": _percentile(latencies_ms, 50),
            "p95_ms": _percentile(latencies_ms, 95),
            "min_ms": latencies_ms[0],
            "max_ms": latencies_ms[-1],
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("=== End-to-End API Latency (/recommend) ===")
    print(f"MongoDB: {data_source}")
    print(f"Book IDs: {book_ids}")
    print(f"Samples: {len(latencies_ms)}  errors: {errors}")
    print(f"mean: {report['latency_ms']['mean_ms']:.2f} ms")
    print(f"p50:  {report['latency_ms']['p50_ms']:.2f} ms")
    print(f"p95:  {report['latency_ms']['p95_ms']:.2f} ms")
    print(f"Report: {output_path}")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
