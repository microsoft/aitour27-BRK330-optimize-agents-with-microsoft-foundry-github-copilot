#!/usr/bin/env python3
"""Compare scored versions using their actual Foundry evaluation results.

Usage:
    python src/scripts/compare_scores.py

Reads the runs recorded by step 07 from .azure/<environment>/scores/runs.jsonl,
downloads each run's row results, and prints one comparison table. Read-only
against Azure; writes a private summary under .azure/<environment>/scores/.
"""
from __future__ import annotations

import json
import os
import statistics
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from src.scripts.questions import load  # noqa: E402

LABEL_ORDER = ("v1", "v2", "v2-quality", "v2-alt", "v3", "v3-router", "v3-student", "v3-tools", "v3-tools-student")


def azd_value(name: str) -> str | None:
    result = subprocess.run(["azd", "env", "get-value", name], capture_output=True, text=True, check=False)
    value = result.stdout.strip()
    return value if result.returncode == 0 and value else None


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round(fraction * (len(ordered) - 1)))]


def fmt(value: float | None, digits: int = 2) -> str:
    return "—" if value is None else f"{value:.{digits}f}"


def summarize(label: str, version: str, items: list[dict[str, Any]], levels: dict[str, str]) -> dict[str, Any]:
    scores, passed, latencies, tokens, errors = [], 0, [], [], 0
    by_level: dict[str, list[float]] = defaultdict(list)
    dimensions: dict[str, list[float]] = defaultdict(list)
    for item in items:
        result = next(iter(item.get("results") or []), None)
        if not result or result.get("score") is None:
            errors += 1
            continue
        score = float(result["score"])
        scores.append(score)
        passed += bool(result.get("passed"))
        source = item.get("datasource_item") or {}
        level = source.get("level") or levels.get(source.get("name", ""), "unknown")
        by_level[level].append(score)
        for dimension in (result.get("properties") or {}).get("dimension_scores") or []:
            if dimension.get("applicable") and dimension.get("score") is not None:
                dimensions[dimension["id"]].append(float(dimension["score"]))
        sample = item.get("sample") or {}
        if sample.get("latency_ms"):
            latencies.append(float(sample["latency_ms"]) / 1000)
        usage = sample.get("usage") or {}
        if usage.get("total_tokens"):
            tokens.append(float(usage["total_tokens"]))
    weakest = min(dimensions.items(), key=lambda pair: statistics.mean(pair[1]), default=(None, []))
    return {
        "label": label,
        "version": version,
        "scored": len(scores),
        "errors": errors,
        "mean": statistics.mean(scores) if scores else None,
        "pass_rate": passed / len(scores) if scores else None,
        "levels": {level: statistics.mean(values) for level, values in by_level.items()},
        "weakest": (weakest[0], statistics.mean(weakest[1])) if weakest[0] else None,
        "dimensions": {name: statistics.mean(values) for name, values in dimensions.items()},
        "p50": percentile(latencies, 0.5),
        "p95": percentile(latencies, 0.95),
        "tokens": statistics.mean(tokens) if tokens else None,
    }


def table(rows: list[dict[str, Any]]) -> str:
    baseline = next((row["mean"] for row in rows if row["label"] == "v1"), None)
    lines = [
        "| Version | Agent | Rows scored | Mean score | Change vs v1 | Pass rate | Easy | Medium | Hard | Weakest area | P50 s | P95 s | Avg agent tokens |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|",
    ]
    for row in rows:
        change = row["mean"] - baseline if baseline is not None and row["mean"] is not None else None
        weakest = f"{row['weakest'][0]} ({row['weakest'][1]:.1f})" if row["weakest"] else "—"
        pass_rate = "—" if row["pass_rate"] is None else f"{row['pass_rate']:.0%}"
        change_text = "—" if change is None else f"{change:+.2f}"
        tokens = "—" if row["tokens"] is None else str(round(row["tokens"]))
        lines.append(
            f"| {row['label']} | {row['version']} | {row['scored']} | {fmt(row['mean'])} | "
            f"{change_text} | {pass_rate} | "
            + " | ".join(fmt(row["levels"].get(level)) for level in ("easy", "medium", "hard"))
            + f" | {weakest} | {fmt(row['p50'], 1)} | {fmt(row['p95'], 1)} | {tokens} |"
        )
    return "\n".join(lines)


def dimension_table(rows: list[dict[str, Any]]) -> str:
    names = sorted({name for row in rows for name in row["dimensions"]})
    lines = [
        "| Dimension (1-5) | " + " | ".join(row["label"] for row in rows) + " |",
        "|---|" + "---:|" * len(rows),
    ]
    for name in names:
        lines.append(f"| `{name}` | " + " | ".join(fmt(row["dimensions"].get(name)) for row in rows) + " |")
    return "\n".join(lines)


def main() -> int:
    from azure.ai.projects import AIProjectClient
    from azure.identity import AzureCliCredential

    environment = azd_value("AZURE_ENV_NAME")
    endpoint = os.getenv("FOUNDRY_PROJECT_ENDPOINT") or azd_value("FOUNDRY_PROJECT_ENDPOINT")
    if not environment or not endpoint:
        raise SystemExit("Select the session azd environment first.")
    folder = REPO_ROOT / ".azure" / environment / "scores"
    runs_file = folder / "runs.jsonl"
    if not runs_file.exists():
        raise SystemExit("No scored runs yet. Run step 07 for v1 first.")
    runs = [json.loads(line) for line in runs_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    levels = {row["name"]: row["level"] for row in load("testing")}

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for run in runs:
        grouped[run["label"]].append(run)
    rows = []
    with AzureCliCredential() as credential, AIProjectClient(endpoint=endpoint, credential=credential) as project:
        client = project.get_openai_client()
        for label in sorted(grouped, key=lambda value: LABEL_ORDER.index(value) if value in LABEL_ORDER else 99):
            items: list[dict[str, Any]] = []
            for run in grouped[label]:
                items.extend(
                    item.model_dump()
                    for item in client.evals.runs.output_items.list(eval_id=run["eval_id"], run_id=run["run_id"])
                )
            rows.append(summarize(label, grouped[label][-1]["version"], items, levels))

    output = table(rows) + "\n\n" + dimension_table(rows)
    print(output)
    print("\nQuality comes from the locked scorecard; speed and tokens are measured separately.")
    print("A version is only an improvement if it keeps the policy decisions right. Check the policy dimensions.")
    (folder / "summary.md").write_text(output + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
