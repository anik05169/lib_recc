#!/usr/bin/env python3
"""
Fetch ~9.8k unique Goodreads books, seed MongoDB, sync Pinecone, benchmark latency.

Designed for GitHub Actions (workflow_dispatch). Writes JSON + Markdown reports
with per-step timing and CI duration estimates for visualization.

Usage (from backend/):
  python scripts/run_catalog_benchmark.py
  python scripts/run_catalog_benchmark.py --runs 20 --skip-api
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent
EVAL_DIR = BACKEND_DIR / "eval"
DEFAULT_BOOKS_JSON = REPO_ROOT / "library_db.books.goodreads.json"

# Rough CI estimates (minutes) — cold run without HuggingFace pip/cache warmup.
CI_ESTIMATE_MINUTES: dict[str, float] = {
    "install_dependencies": 3.0,
    "fetch_goodreads_catalog": 0.2,
    "seed_mongodb": 0.5,
    "sync_pinecone_embeddings": 8.0,
    "inprocess_latency_benchmark": 1.5,
    "api_latency_benchmark": 2.0,
    "report_generation": 0.1,
}
CI_ESTIMATE_WARM_HF_CACHE_MINUTES: dict[str, float] = {
    **CI_ESTIMATE_MINUTES,
    "sync_pinecone_embeddings": 5.0,
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Full catalog fetch + latency benchmark pipeline")
    parser.add_argument(
        "--books-json",
        default=str(DEFAULT_BOOKS_JSON),
        help="Path to catalog JSON (fetched if missing)",
    )
    parser.add_argument("--runs", type=int, default=20, help="Latency runs per query book")
    parser.add_argument("--k", type=int, default=5, help="Top-k for in-process benchmark")
    parser.add_argument(
        "--labels",
        default="eval/relevance_labels.example.json",
        help="Relevance labels for benchmark queries",
    )
    parser.add_argument(
        "--json-out",
        default="eval/benchmark_report.json",
        help="Combined JSON report path (relative to backend/)",
    )
    parser.add_argument(
        "--md-out",
        default="eval/benchmark_report.md",
        help="Markdown report with timing chart (relative to backend/)",
    )
    parser.add_argument("--skip-fetch", action="store_true", help="Reuse existing books JSON")
    parser.add_argument("--skip-api", action="store_true", help="Skip API uvicorn benchmark")
    parser.add_argument("--api-port", type=int, default=8000)
    return parser.parse_args()


def _resolve(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    if path_str.startswith("eval/"):
        return (BACKEND_DIR / path).resolve()
    return (REPO_ROOT / path).resolve()


def _env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("JWT_SECRET", "ci-benchmark-secret")
    env.setdefault("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    env.setdefault("HF_HOME", str(REPO_ROOT / ".cache" / "huggingface"))
    env.setdefault("TRANSFORMERS_CACHE", env["HF_HOME"])
    return env


def _run_step(name: str, cmd: list[str], cwd: Path | None = None) -> dict[str, Any]:
    cwd = cwd or BACKEND_DIR
    print(f"\n=== {name} ===")
    print(" ".join(cmd))
    started = time.perf_counter()
    proc = subprocess.run(cmd, cwd=cwd, env=_env(), check=True, text=True)
    elapsed = time.perf_counter() - started
    record = {
        "step": name,
        "duration_seconds": round(elapsed, 2),
        "duration_minutes": round(elapsed / 60, 2),
        "command": " ".join(cmd),
        "exit_code": proc.returncode,
    }
    print(f"Done in {record['duration_seconds']}s")
    return record


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _bar(seconds: float, max_seconds: float, width: int = 24) -> str:
    if max_seconds <= 0:
        return "░" * width
    filled = min(width, max(1, int(round((seconds / max_seconds) * width))))
    return "█" * filled + "░" * (width - filled)


def _format_timing_md(steps: list[dict[str, Any]], estimates: dict[str, float]) -> str:
    total_s = sum(s["duration_seconds"] for s in steps)
    max_s = max((s["duration_seconds"] for s in steps), default=1.0)
    est_total = sum(estimates.values())

    lines = [
        "# Catalog latency benchmark report",
        "",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "## Pipeline timing (actual)",
        "",
        "| Step | Actual | % of run | Bar |",
        "|------|--------|----------|-----|",
    ]
    for step in steps:
        pct = (step["duration_seconds"] / total_s * 100) if total_s else 0
        bar = _bar(step["duration_seconds"], max_s)
        lines.append(
            f"| {step['step']} | {step['duration_seconds']}s ({step['duration_minutes']} min) "
            f"| {pct:.1f}% | `{bar}` |"
        )
    lines.extend(
        [
            "",
            f"**Total pipeline time:** {total_s:.1f}s ({total_s / 60:.1f} min)",
            "",
            "## CI time estimate (before run)",
            "",
            "Use this to plan GitHub Actions `timeout-minutes`. Warm HF cache is faster.",
            "",
            "| Step | Cold est. (min) | Warm HF est. (min) |",
            "|------|-----------------|---------------------|",
        ]
    )
    for key, cold in CI_ESTIMATE_MINUTES.items():
        warm = CI_ESTIMATE_WARM_HF_CACHE_MINUTES.get(key, cold)
        lines.append(f"| {key} | {cold:.1f} | {warm:.1f} |")
    lines.extend(
        [
            "",
            f"**Estimated CI total (cold):** {est_total:.1f} min (+ ~3 min pip install)",
            f"**Estimated CI total (warm HF cache):** {sum(CI_ESTIMATE_WARM_HF_CACHE_MINUTES.values()):.1f} min (+ ~3 min pip install)",
            "",
            "```mermaid",
            "gantt",
            "    title Estimated CI pipeline (cold, minutes)",
            "    dateFormat X",
            "    axisFormat %M min",
        ]
    )
    offset = 0
    for key, minutes in CI_ESTIMATE_MINUTES.items():
        lines.append(f"    {key} : {offset}, {offset + minutes}")
        offset += minutes
    lines.extend(["```", ""])

    return "\n".join(lines)


def _wait_for_health(base_url: str, timeout_s: int = 300) -> dict[str, Any]:
    import requests

    deadline = time.time() + timeout_s
    last = None
    while time.time() < deadline:
        try:
            res = requests.get(f"{base_url}/health", timeout=5)
            last = res.json()
            if res.ok and last.get("recommender_ready"):
                return last
        except requests.RequestException:
            pass
        time.sleep(2)
    raise RuntimeError(f"API not ready after {timeout_s}s. Last health: {last}")


def main() -> int:
    args = _parse_args()
    load_dotenv(BACKEND_DIR / ".env")

    books_json = _resolve(args.books_json)
    labels_path = _resolve(args.labels)
    json_out = _resolve(args.json_out)
    md_out = _resolve(args.md_out)
    stats_out = EVAL_DIR / "stats_goodreads.json"
    api_out = EVAL_DIR / "api_latency_goodreads.json"

    steps: list[dict[str, Any]] = []
    python = sys.executable

    if not args.skip_fetch or not books_json.exists():
        steps.append(
            _run_step(
                "fetch_goodreads_catalog",
                [python, "scripts/fetch_goodreads_catalog.py", "--output", str(books_json)],
            )
        )
    else:
        print(f"Reusing catalog JSON: {books_json}")

    catalog = _load_json(books_json)
    book_count = len(catalog)

    steps.append(
        _run_step(
            "seed_mongodb",
            [
                python,
                "scripts/seed_catalog.py",
                "--books-file",
                str(books_json.relative_to(REPO_ROOT)),
                "--force",
            ],
        )
    )

    steps.append(
        _run_step(
            "sync_pinecone_embeddings",
            [python, "scripts/sync_pinecone_index.py", "--scope", "catalog"],
        )
    )

    steps.append(
        _run_step(
            "inprocess_latency_benchmark",
            [
                python,
                "scripts/calc_recommender_stats.py",
                "--labels",
                str(labels_path.relative_to(BACKEND_DIR)),
                "--k",
                str(args.k),
                "--runs",
                str(args.runs),
                "--skip-train",
                "--output",
                str(stats_out.relative_to(BACKEND_DIR)),
            ],
        )
    )

    health: dict[str, Any] | None = None
    if not args.skip_api:
        api_env = _env()
        api_env["SKIP_EMBEDDING_SYNC"] = "true"
        api_cmd = [
            python,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(args.api_port),
        ]
        print(f"\n=== api_latency_benchmark (starting uvicorn) ===")
        proc = subprocess.Popen(
            api_cmd,
            cwd=BACKEND_DIR,
            env=api_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        try:
            base_url = f"http://127.0.0.1:{args.api_port}"
            health = _wait_for_health(base_url)
            steps.append(
                _run_step(
                    "api_latency_benchmark",
                    [
                        python,
                        "scripts/benchmark_api_latency.py",
                        "--labels",
                        str(labels_path.relative_to(BACKEND_DIR)),
                        "--runs",
                        str(args.runs),
                        "--base-url",
                        base_url,
                        "--output",
                        str(api_out.relative_to(BACKEND_DIR)),
                    ],
                )
            )
        finally:
            proc.send_signal(signal.SIGTERM)
            try:
                proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                proc.kill()
    else:
        api_out = None

    inprocess = _load_json(stats_out)
    api_report = _load_json(api_out) if api_out and api_out.exists() else None

    total_seconds = sum(s["duration_seconds"] for s in steps)
    report: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "catalog": {
            "source": "goodbooks-10k (Goodreads)",
            "books_file": str(books_json),
            "book_count": book_count,
        },
        "pipeline_timing": {
            "steps": steps,
            "total_seconds": round(total_seconds, 2),
            "total_minutes": round(total_seconds / 60, 2),
        },
        "ci_time_estimate": {
            "cold_minutes": {
                "steps": CI_ESTIMATE_MINUTES,
                "pipeline_total": round(sum(CI_ESTIMATE_MINUTES.values()), 1),
                "with_pip_install": round(sum(CI_ESTIMATE_MINUTES.values()) + 3.0, 1),
            },
            "warm_hf_cache_minutes": {
                "steps": CI_ESTIMATE_WARM_HF_CACHE_MINUTES,
                "pipeline_total": round(sum(CI_ESTIMATE_WARM_HF_CACHE_MINUTES.values()), 1),
                "with_pip_install": round(sum(CI_ESTIMATE_WARM_HF_CACHE_MINUTES.values()) + 3.0, 1),
            },
            "recommended_workflow_timeout_minutes": 45,
            "notes": [
                "First CI run downloads torch + embedding model (~2-4 min extra).",
                "sync_pinecone_embeddings scales with book count (~8 min for ~9.8k books).",
                "HF actions/cache reduces model load on subsequent runs.",
            ],
        },
        "latency": {
            "inprocess": inprocess.get("latency_ms"),
            "inprocess_quality": inprocess.get("quality"),
            "api": api_report.get("latency_ms") if api_report else None,
            "api_health": health or (api_report.get("health") if api_report else None),
        },
        "artifacts": {
            "stats_json": str(stats_out),
            "api_latency_json": str(api_out) if api_out else None,
            "combined_json": str(json_out),
            "markdown": str(md_out),
        },
    }

    json_out.parent.mkdir(parents=True, exist_ok=True)
    with json_out.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    md_body = _format_timing_md(steps, CI_ESTIMATE_MINUTES)
    if inprocess.get("latency_ms"):
        lat = inprocess["latency_ms"]
        md_body += (
            "## In-process latency (`recommend()`)\n\n"
            f"| mean | p50 | p95 |\n|------|-----|-----|\n"
            f"| {lat['mean_ms']:.1f} ms | {lat['p50_ms']:.1f} ms | {lat['p95_ms']:.1f} ms |\n\n"
        )
    if api_report and api_report.get("latency_ms"):
        lat = api_report["latency_ms"]
        md_body += (
            "## API latency (`GET /recommend/{book_id}`)\n\n"
            f"| mean | p50 | p95 | errors |\n|------|-----|-----|--------|\n"
            f"| {lat['mean_ms']:.1f} ms | {lat['p50_ms']:.1f} ms | {lat['p95_ms']:.1f} ms | {lat.get('errors', 0)} |\n"
        )

    with md_out.open("w", encoding="utf-8") as f:
        f.write(md_body)

    print("\n=== Benchmark complete ===")
    print(f"Books: {book_count}")
    print(f"Pipeline: {total_seconds:.1f}s ({total_seconds / 60:.1f} min)")
    print(f"JSON report: {json_out}")
    print(f"Markdown report: {md_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
