#!/usr/bin/env python3
"""Load and check the three BRK330 question sets.

Usage:
    python src/scripts/questions.py

Read-only. Exits nonzero when a set has the wrong size or shape, when a
question repeats across sets, or when a testing scenario leaks into the
exploring or training sets.
"""
from __future__ import annotations

import ast
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
QUESTIONS = REPO_ROOT / "data" / "questions"
SETS = ("exploring", "training", "testing")
LEVELS = ("easy", "medium", "hard")
ATTACHMENT_PREFIX = "\n\nAttached receipt fixture IDs: "
PORTAL_IDS = ("HERO-01", "BLOCK-01", "EVIDENCE-01", "ACCESS-01")

# Scenarios reserved for testing; none of these may appear in exploring or training.
TEST_ONLY = {
    "toronto": ("Toronto", "YYZ", "FL-011", "FL-012", "HT-011", "HT-012"),
    "chicago": ("Chicago", "CHI", "FL-015", "HT-013", "CR-007"),
    "san-francisco": ("San Francisco", "SFO", "FL-013", "FL-014", "HT-014", "CR-009", "Union Square"),
    "madrid": ("Madrid", "MAD", "FL-020", "HT-016", "CR-014", "Retiro"),
    "zurich": ("Zurich", "ZRH", "FL-022", "HT-018", "CR-016", "Bahnhof"),
    "tokyo": ("Tokyo", "TYO", "FL-023", "HT-020"),
    "rec-003": ("REC-003",),
    "rec-004": ("REC-004",),
}
SIZES = {"exploring": 36, "training": 48, "testing": 24}


def path_for(name: str) -> Path:
    return QUESTIONS / f"{name}.jsonl"


def load(name: str) -> list[dict[str, Any]]:
    rows = []
    for number, line in enumerate(path_for(name).read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"{name}.jsonl:{number} must be a JSON object")
            rows.append(row)
    return rows


def row_id(row: dict[str, Any]) -> str:
    return str(row.get("name") or row.get("id") or "")


def normalized(text: str) -> str:
    return " ".join(text.casefold().split())


def portal_prompts() -> dict[str, str]:
    """Read the portal's sample prompts without importing the web app."""
    tree = ast.parse((REPO_ROOT / "src" / "web" / "main.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "SAMPLE_PROMPTS" for target in node.targets
        ):
            samples = ast.literal_eval(node.value)
            return {
                sample["id"]: sample["message"]
                + (ATTACHMENT_PREFIX + ", ".join(sample["attachments"]) if sample["attachments"] else "")
                for sample in samples
            }
    raise ValueError("SAMPLE_PROMPTS not found in src/web/main.py")


def _require(condition: bool, message: str, problems: list[str]) -> None:
    if not condition:
        problems.append(message)


def validate() -> dict[str, list[dict[str, Any]]]:
    sets = {name: load(name) for name in SETS}
    rules = json.loads((REPO_ROOT / "data" / "fine-tuning-review.json").read_text(encoding="utf-8"))
    problems: list[str] = []

    for name, rows in sets.items():
        _require(len(rows) == SIZES[name], f"{name} has {len(rows)} questions; expected {SIZES[name]}", problems)
        ids = [row_id(row) for row in rows]
        _require(all(ids) and len(ids) == len(set(ids)), f"{name} has missing or repeated IDs", problems)
        for row in rows:
            _require(bool(row.get("query")) and bool(row.get("family")), f"{name} {row_id(row)} needs query and family", problems)

    for name in ("exploring", "testing"):
        levels = Counter(row.get("level") for row in sets[name])
        expected = SIZES[name] // len(LEVELS)
        _require(all(levels[level] == expected for level in LEVELS) and sum(levels.values()) == SIZES[name],
                 f"{name} needs {expected} easy, medium, and hard questions; found {dict(levels)}", problems)
        for row in sets[name]:
            _require(bool(row.get("expected_behavior")), f"{name} {row_id(row)} needs expected_behavior", problems)

    practice = [row for row in sets["exploring"] if row.get("practice") is True]
    practice_levels = Counter(row["level"] for row in practice)
    _require(len(practice) == 12 and all(practice_levels[level] == 4 for level in LEVELS),
             f"exploring needs 12 practice questions, 4 per level; found {dict(practice_levels)}", problems)
    _require(sets["exploring"][: len(practice)] == practice, "practice questions must come first in exploring", problems)

    categories = set(rules["minimum_per_category"])
    for row in sets["training"]:
        _require(row.get("category") in categories, f"training {row_id(row)} has unknown category", problems)
        _require(row.get("split") in {"train", "validation"}, f"training {row_id(row)} needs split train or validation", problems)

    seen: dict[str, str] = {}
    for name, rows in sets.items():
        for row in rows:
            key = normalized(row["query"])
            _require(key not in seen, f"{name} {row_id(row)} repeats {seen.get(key)}", problems)
            seen.setdefault(key, f"{name} {row_id(row)}")

    for row in sets["testing"]:
        _require(row["family"] in TEST_ONLY, f"testing {row_id(row)} uses non-test family {row['family']}", problems)
    patterns = [re.compile(rf"\b{re.escape(term)}\b") for terms in TEST_ONLY.values() for term in terms]
    for name in ("exploring", "training"):
        for row in sets[name]:
            _require(row["family"] not in TEST_ONLY, f"{name} {row_id(row)} uses test family {row['family']}", problems)
            leaked = [pattern.pattern for pattern in patterns if pattern.search(row["query"])]
            _require(not leaked, f"{name} {row_id(row)} mentions a test-only scenario: {leaked}", problems)

    exploring = {row_id(row): row["query"] for row in sets["exploring"]}
    for portal_id, message in portal_prompts().items():
        _require(exploring.get(portal_id) == message, f"exploring {portal_id} must match the portal prompt exactly", problems)
    _require(set(PORTAL_IDS) <= set(exploring), "exploring must include all four portal prompts", problems)

    if problems:
        raise ValueError("Question sets are not ready:\n- " + "\n- ".join(problems))
    return sets


def main() -> int:
    try:
        sets = validate()
    except ValueError as error:
        print(error, file=sys.stderr)
        return 1
    for name, rows in sets.items():
        levels = Counter(row.get("level") or row.get("category") for row in rows)
        print(f"{name}: {len(rows)} questions {dict(sorted(levels.items()))}")
    print("Question sets: ready (no repeats, no testing scenarios in exploring or training)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
