#!/usr/bin/env python3
"""Validate the reviewed gold corpus and emit deterministic v4 SFT artifacts."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.training.trace_dataset import REQUIRED_GATES


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=True) for row in rows) + "\n", encoding="utf-8")


def _normalized(text: str) -> str:
    return " ".join(text.casefold().split())


def prepare(gold_path: Path, holdout_path: Path, scope_path: Path, instruction_path: Path):
    rows = _load_jsonl(gold_path)
    holdout = {_normalized(row["query"]) for row in _load_jsonl(holdout_path)}
    scope = json.loads(scope_path.read_text(encoding="utf-8"))
    instructions = instruction_path.read_text(encoding="utf-8").strip()
    expected_roles = ["system", "user", "assistant"]
    prompts: list[str] = []
    ids: set[str] = set()
    traces: set[str] = set()

    for row in rows:
        if row.get("id") in ids:
            raise ValueError(f"Duplicate gold ID: {row.get('id')}")
        ids.add(row["id"])
        if row.get("source_trace_id") in traces:
            raise ValueError(f"Duplicate source trace: {row.get('source_trace_id')}")
        traces.add(row["source_trace_id"])
        messages = row.get("messages") or []
        if [message.get("role") for message in messages] != expected_roles:
            raise ValueError(f"{row['id']} must contain system, user, assistant messages in order.")
        if messages[0].get("content", "").strip() != instructions:
            raise ValueError(f"{row['id']} does not reuse the baseline instructions exactly.")
        if not messages[1].get("content", "").strip() or not messages[2].get("content", "").strip():
            raise ValueError(f"{row['id']} has an empty user or assistant message.")
        prompt = _normalized(messages[1]["content"])
        if prompt in holdout:
            raise ValueError(f"{row['id']} overlaps the frozen evaluation holdout.")
        prompts.append(prompt)
        review = row.get("review") or {}
        if review.get("rubric_score", 0) < 0.5:
            raise ValueError(f"{row['id']} is below the reviewed rubric threshold.")
        failed = [gate for gate in REQUIRED_GATES if (review.get("hard_gates") or {}).get(gate) is not True]
        if failed:
            raise ValueError(f"{row['id']} failed hard gates: {', '.join(failed)}")
        if row.get("split") not in {"train", "validation"}:
            raise ValueError(f"{row['id']} must select train or validation split.")

    if len(prompts) != len(set(prompts)):
        raise ValueError("Gold corpus contains duplicate prompts.")
    train_rows = [row for row in rows if row["split"] == "train"]
    validation_rows = [row for row in rows if row["split"] == "validation"]
    if len(train_rows) != scope["minimum_training_examples"] or len(validation_rows) != scope["minimum_validation_examples"]:
        raise ValueError(f"Expected exact 20/4 split; found {len(train_rows)}/{len(validation_rows)}.")
    coverage = Counter(row["category"] for row in train_rows)
    if dict(coverage) != scope["coverage"]:
        raise ValueError(f"Training category coverage differs from contract: {dict(coverage)}")

    sft = lambda selected: [{"messages": row["messages"]} for row in selected]
    provenance = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": str(gold_path),
        "lever": "curated_gold_responses",
        "student_base_model": scope["student_base_model"],
        "evaluation_holdout": scope["evaluation_holdout"],
        "instruction_sha256": hashlib.sha256(instructions.encode()).hexdigest(),
        "gold_sha256": hashlib.sha256(gold_path.read_bytes()).hexdigest(),
        "train_count": len(train_rows),
        "validation_count": len(validation_rows),
        "coverage": dict(sorted(coverage.items())),
        "examples": [
            {
                "id": row["id"],
                "source_trace_id": row["source_trace_id"],
                "split": row["split"],
                "category": row["category"],
                "rubric_score": row["review"]["rubric_score"],
                "prompt_sha256": hashlib.sha256(_normalized(row["messages"][1]["content"]).encode()).hexdigest(),
                "response_sha256": hashlib.sha256(row["messages"][2]["content"].encode()).hexdigest(),
            }
            for row in rows
        ],
    }
    return sft(train_rows), sft(validation_rows), provenance


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--holdout", type=Path, required=True)
    parser.add_argument("--scope", type=Path, required=True)
    parser.add_argument("--instructions", type=Path, required=True)
    parser.add_argument("--train", type=Path, required=True)
    parser.add_argument("--validation", type=Path, required=True)
    parser.add_argument("--provenance", type=Path, required=True)
    args = parser.parse_args()
    train, validation, provenance = prepare(args.gold, args.holdout, args.scope, args.instructions)
    _write_jsonl(args.train, train)
    _write_jsonl(args.validation, validation)
    args.provenance.parent.mkdir(parents=True, exist_ok=True)
    args.provenance.write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    print(f"Training examples: {len(train)}")
    print(f"Validation examples: {len(validation)}")
    print("Frozen evaluation overlap: 0")
    print(f"Gold SHA256: {provenance['gold_sha256']}")
    print(f"Provenance: {args.provenance}")


if __name__ == "__main__":
    main()