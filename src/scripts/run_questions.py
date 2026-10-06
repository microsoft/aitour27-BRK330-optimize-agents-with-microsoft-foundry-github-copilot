#!/usr/bin/env python3
"""Send a question set to one Hosted Agent version and record what happened.

Usage:
    python src/scripts/run_questions.py --set exploring --version 1 --repeats 2

Each question runs in a fresh session and conversation pinned to the chosen
version, so live portal traffic is unaffected. Questions run one at a time
unless --parallel is set. Results stay in ignored .azure/<environment>/questions/
storage. This makes billable calls.
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
import threading
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from src.scripts.questions import SETS, load, row_id, validate  # noqa: E402
from src.web.evidence import summarize_response  # noqa: E402


def azd_value(name: str) -> str:
    result = subprocess.run(["azd", "env", "get-value", name], capture_output=True, text=True, check=False)
    value = result.stdout.strip()
    if result.returncode != 0 or not value:
        raise SystemExit(f"azd environment value {name} is not set; select the session environment first.")
    return value


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def parse_payload(text: str) -> dict[str, Any] | None:
    # `--output raw` prints HTTP headers then a server-sent event stream; the final event holds the full response.
    final: dict[str, Any] | None = None
    for line in text.splitlines():
        if not line.startswith("data:"):
            continue
        try:
            event = json.loads(line[5:].strip())
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict) and event.get("type") in {"response.completed", "response.failed", "response.incomplete"}:
            final = event.get("response")
    if final is not None:
        return final if final.get("status") == "completed" else None
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        value = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def ask(query: str, version: str, timeout: int) -> dict[str, Any]:
    command = [
        "azd", "ai", "agent", "invoke",
        "--version", version,
        "--protocol", "responses",
        "--new-session", "--new-conversation",
        "--output", "raw", "--no-prompt",
        query,
    ]
    environment = {**os.environ, "AZURE_DEV_USER_AGENT": "microsoft_foundry_skill"}
    started = time.perf_counter()
    try:
        result = subprocess.run(
            command, cwd=REPO_ROOT / "src" / "agent", env=environment,
            capture_output=True, text=True, timeout=timeout, check=False,
        )
        output, error, code = result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        output, error, code = "", f"Timed out after {timeout} seconds", -1
    seconds = round(time.perf_counter() - started, 2)
    payload = parse_payload(output)
    if code != 0 or payload is None:
        return {"ok": False, "seconds": seconds, "error": (error or output)[-600:].strip()}
    summary = summarize_response(payload)
    usage = summary["usage"]
    return {
        "ok": True,
        "seconds": seconds,
        "outcome": summary["outcome"]["code"],
        "tools": [step["tool"] for step in summary["tool_timeline"]],
        "cited_rules": summary["policy"]["cited_rule_ids"],
        "input_tokens": usage.get("input_tokens") or usage.get("prompt_tokens"),
        "output_tokens": usage.get("output_tokens") or usage.get("completion_tokens"),
        "total_tokens": usage.get("total_tokens"),
        "model": summary["model"],
        "response_id": summary["response_id"],
        "answer": summary["assistant"],
    }


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round(fraction * (len(ordered) - 1)))]


def report(records: list[dict[str, Any]]) -> str:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        groups[record["group"]].append(record)
    lines = [
        "| Group | Asked | Answered | Errors | P50 s | P95 s | Avg tokens | Avg tool calls | Outcomes |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for group in sorted(groups, key=lambda value: ("easy", "medium", "hard").index(value) if value in ("easy", "medium", "hard") else 9):
        rows = groups[group]
        answered = [row for row in rows if row["ok"]]
        seconds = [row["seconds"] for row in answered]
        tokens = [row["total_tokens"] for row in answered if row.get("total_tokens")]
        tool_counts = [len(row["tools"]) for row in answered]
        outcomes = Counter(row["outcome"] for row in answered)
        p50, p95 = percentile(seconds, 0.5), percentile(seconds, 0.95)
        lines.append(
            f"| {group} | {len(rows)} | {len(answered)} | {len(rows) - len(answered)} | "
            f"{p50 if p50 is not None else '—'} | {p95 if p95 is not None else '—'} | "
            f"{round(statistics.mean(tokens)) if tokens else '—'} | "
            f"{round(statistics.mean(tool_counts), 1) if tool_counts else '—'} | "
            f"{', '.join(f'{key} {value}' for key, value in outcomes.most_common())} |"
        )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--set", dest="question_set", choices=SETS, required=True)
    parser.add_argument("--version", required=True, help="Immutable agent version to ask, for example 1.")
    parser.add_argument("--repeats", type=int, default=1, help="How many times to ask the whole set.")
    parser.add_argument("--limit", type=int, help="Ask only the first N questions (for a quick check).")
    parser.add_argument("--pause", type=float, default=2.0, help="Seconds to wait between questions.")
    parser.add_argument("--timeout", type=int, default=300, help="Seconds before one question is abandoned.")
    parser.add_argument("--parallel", type=int, default=1, help="How many questions to ask at once (1-4).")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.repeats < 1:
        raise SystemExit("--repeats must be at least 1")
    if not 1 <= args.parallel <= 4:
        raise SystemExit("--parallel must be between 1 and 4")
    validate()
    rows = load(args.question_set)[: args.limit]
    environment = azd_value("AZURE_ENV_NAME")
    folder = REPO_ROOT / ".azure" / environment / "questions"
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    results_file = folder / f"{args.question_set}-v{args.version}-{stamp}.jsonl"
    total = len(rows) * args.repeats
    window = {"set": args.question_set, "version": args.version, "repeats": args.repeats,
              "questions": len(rows), "started_at": now(), "results": str(results_file.relative_to(REPO_ROOT))}
    print(f"Asking {total} questions from '{args.question_set}' against agent version {args.version}"
          f"{f', {args.parallel} at a time' if args.parallel > 1 else ''}.")
    print(f"Results: {window['results']}")

    jobs = [(repeat, row) for repeat in range(1, args.repeats + 1) for row in rows]
    records: list[dict[str, Any]] = []
    lock = threading.Lock()

    with results_file.open("w", encoding="utf-8") as handle:
        def run(job: tuple[int, dict[str, Any]]) -> None:
            repeat, row = job
            result = ask(row["query"], args.version, args.timeout)
            record = {
                "question": row_id(row), "group": row.get("level") or row.get("category"),
                "family": row["family"], "repeat": repeat, "version": args.version,
                "asked_at": now(), **result,
            }
            with lock:
                records.append(record)
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
                handle.flush()
                count = len(records)
                status = record.get("outcome") if record["ok"] else "error"
                print(f"[{count:>3}/{total}] {record['question']:<12} {status:<20} {record['seconds']:>6}s", flush=True)
            if count < total:
                time.sleep(args.pause)

        with ThreadPoolExecutor(max_workers=args.parallel) as pool:
            list(pool.map(run, jobs))

    window["finished_at"] = now()
    window["errors"] = sum(1 for record in records if not record["ok"])
    (folder / f"{args.question_set}-v{args.version}-latest.json").write_text(json.dumps(window, indent=2) + "\n", encoding="utf-8")
    summary = report(records)
    (folder / f"{args.question_set}-v{args.version}-{stamp}.md").write_text(summary + "\n", encoding="utf-8")
    print()
    print(summary)
    if window["errors"]:
        print(f"\n{window['errors']} question(s) did not get an answer. They are recorded as errors, not as poor answers.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
