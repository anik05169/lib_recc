#!/usr/bin/env python3
"""
Compute offline recommender quality + latency statistics.

Metrics:
- Precision@k
- Recall@k
- HitRate@k
- MRR@k
- Latency (ms): mean, p50, p95

Usage:
  python scripts/calc_recommender_stats.py --labels eval/relevance_labels.example.json
  python scripts/calc_recommender_stats.py --labels eval/relevance_labels.example.json --k 5 --runs 30
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

from dotenv import load_dotenv

# Allow running as: python scripts/calc_recommender_stats.py
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
load_dotenv(BACKEND_DIR / ".env")

from app.db.mongo import get_mongo_db  # noqa: E402
from app.db.ratings_util import get_avg_ratings_map  # noqa: E402
from app.services.recommender import recommend, train_model  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute recommender quality and latency stats")
    parser.add_argument(
        "--labels",
        required=True,
        help="Path to relevance labels JSON file (see backend/eval/relevance_labels.example.json)",
    )
    parser.add_argument("--k", type=int, default=5, help="Top-k cutoff (default: 5)")
    parser.add_argument(
        "--runs",
        type=int,
        default=20,
        help="Benchmark runs per query for latency stats (default: 20)",
    )
    parser.add_argument(
        "--output",
        default="eval/stats_latest.json",
        help="Where to save JSON report (default: eval/stats_latest.json)",
    )
    return parser.parse_args()


def _load_labels(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Labels file not found: {path}")

    with path.open(encoding="utf-8") as f:
        payload = json.load(f)

    queries = payload.get("queries")
    if not isinstance(queries, list) or not queries:
        raise ValueError("Labels JSON must contain non-empty 'queries' list")

    parsed: list[dict[str, Any]] = []
    for idx, q in enumerate(queries):
        if not isinstance(q, dict):
            raise ValueError(f"queries[{idx}] must be an object")
        if "book_id" not in q or "relevant" not in q:
            raise ValueError(f"queries[{idx}] must include 'book_id' and 'relevant'")
        if not isinstance(q["relevant"], list):
            raise ValueError(f"queries[{idx}].relevant must be a list")

        parsed.append(
            {
                "book_id": int(q["book_id"]),
                "relevant": {int(x) for x in q["relevant"]},
            }
        )
    return parsed


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


def _evaluate_quality(
    queries: list[dict[str, Any]],
    ratings_map: dict[int, float],
    k: int,
) -> dict[str, float]:
    precision_vals: list[float] = []
    recall_vals: list[float] = []
    hit_vals: list[float] = []
    reciprocal_ranks: list[float] = []

    skipped = 0
    for q in queries:
        book_id = q["book_id"]
        relevant = q["relevant"]
        if not relevant:
            skipped += 1
            continue

        recs = recommend(book_id, top_n=k, ratings_map=ratings_map) or []
        rec_ids = [int(b["book_id"]) for b in recs if "book_id" in b]
        hits = len(set(rec_ids).intersection(relevant))

        precision_vals.append(hits / k)
        recall_vals.append(hits / len(relevant))
        hit_vals.append(1.0 if hits > 0 else 0.0)

        rr = 0.0
        for rank, rec_id in enumerate(rec_ids, start=1):
            if rec_id in relevant:
                rr = 1.0 / rank
                break
        reciprocal_ranks.append(rr)

    denom = len(precision_vals)
    if denom == 0:
        raise RuntimeError("No valid labeled queries to evaluate")

    return {
        "precision_at_k": sum(precision_vals) / denom,
        "recall_at_k": sum(recall_vals) / denom,
        "hit_rate_at_k": sum(hit_vals) / denom,
        "mrr_at_k": sum(reciprocal_ranks) / denom,
        "evaluated_queries": denom,
        "skipped_queries": skipped,
    }


def _benchmark_latency(
    query_book_ids: list[int],
    ratings_map: dict[int, float],
    k: int,
    runs: int,
) -> dict[str, float]:
    latencies_ms: list[float] = []
    for _ in range(runs):
        for book_id in query_book_ids:
            start = time.perf_counter()
            _ = recommend(book_id, top_n=k, ratings_map=ratings_map)
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            latencies_ms.append(elapsed_ms)

    if not latencies_ms:
        raise RuntimeError("No latency samples captured")

    latencies_ms.sort()
    return {
        "samples": len(latencies_ms),
        "mean_ms": statistics.fmean(latencies_ms),
        "p50_ms": _percentile(latencies_ms, 50),
        "p95_ms": _percentile(latencies_ms, 95),
        "min_ms": latencies_ms[0],
        "max_ms": latencies_ms[-1],
    }


def main() -> int:
    args = _parse_args()
    labels_path = (BACKEND_DIR / args.labels).resolve() if not Path(args.labels).is_absolute() else Path(args.labels)
    output_path = (BACKEND_DIR / args.output).resolve() if not Path(args.output).is_absolute() else Path(args.output)

    if args.k <= 0:
        raise ValueError("--k must be > 0")
    if args.runs <= 0:
        raise ValueError("--runs must be > 0")

    queries = _load_labels(labels_path)
    db = get_mongo_db()
    books = list(db.books.find({}, {"_id": 0}))
    if not books:
        raise RuntimeError("No books in catalog. Seed books before running stats.")

    ratings_map = get_avg_ratings_map(db)
    train_model(books, ratings_map)

    quality = _evaluate_quality(queries, ratings_map, args.k)
    latency = _benchmark_latency([q["book_id"] for q in queries], ratings_map, args.k, args.runs)

    report = {
        "config": {
            "k": args.k,
            "runs": args.runs,
            "labels_file": str(labels_path),
        },
        "quality": quality,
        "latency_ms": latency,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("=== Recommender Stats ===")
    print(f"Precision@{args.k}: {quality['precision_at_k']:.4f}")
    print(f"Recall@{args.k}:    {quality['recall_at_k']:.4f}")
    print(f"HitRate@{args.k}:   {quality['hit_rate_at_k']:.4f}")
    print(f"MRR@{args.k}:       {quality['mrr_at_k']:.4f}")
    print("--- Latency (ms) ---")
    print(f"mean: {latency['mean_ms']:.3f}  p50: {latency['p50_ms']:.3f}  p95: {latency['p95_ms']:.3f}")
    print(f"Report written to: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
