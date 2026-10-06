#!/usr/bin/env python3
"""Transform reviewed Foundry traces into deterministic SFT datasets."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REQUIRED_GATES = (
    "no_policy_hard_gate_violation",
    "policy_checks_before_recommendations",
    "no_unsupported_rule_attribution",
    "reported_totals_reconcile",
    "all_tool_outputs_fixture_grounded",
)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(json.dumps(row, ensure_ascii=True) for row in rows)
    path.write_text(f"{content}\n" if content else "", encoding="utf-8")


def _normalized(text: str) -> str:
    return " ".join(text.casefold().split())


def _message_text(message: dict[str, Any]) -> str:
    text: list[str] = []
    for part in message.get("parts", []):
        if part.get("type") == "text" and part.get("content"):
            text.append(str(part["content"]))
    return "\n".join(text).strip()


def _messages(raw: str | None) -> list[dict[str, Any]]:
    if not raw:
        return []
    value = json.loads(raw)
    if not isinstance(value, list):
        raise ValueError("Trace message content must be a JSON array.")
    return value


def _holdout_prompts(path: Path) -> set[str]:
    return {_normalized(row["query"]) for row in _load_jsonl(path)}


def _training_questions(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None:
        return {}
    return {_normalized(row["query"]): row for row in _load_jsonl(path)}


def transform(raw_path: Path, holdout_path: Path, questions_path: Path | None = None) -> list[dict[str, Any]]:
    raw_rows = json.loads(raw_path.read_text(encoding="utf-8"))
    holdout = _holdout_prompts(holdout_path)
    questions = _training_questions(questions_path)
    candidates: dict[str, dict[str, Any]] = {}
    for row in sorted(raw_rows, key=lambda item: item.get("TimeGenerated", "")):
        input_messages = _messages(row.get("InputMessages"))
        output_messages = _messages(row.get("OutputMessages"))
        users = [_message_text(message) for message in input_messages if message.get("role") == "user"]
        assistants = [
            _message_text(message) for message in output_messages if message.get("role") == "assistant"
        ]
        query = next((text for text in reversed(users) if text), "")
        response = next((text for text in reversed(assistants) if text), "")
        if not query or not response or _normalized(query) in holdout:
            continue
        trace_id = str(row.get("TraceId") or "")
        if not trace_id:
            continue
        prompt_key = _normalized(query)
        question = questions.get(prompt_key)
        if questions and question is None:
            continue
        candidates[prompt_key] = {
            "trace_id": trace_id,
            "timestamp": row.get("TimeGenerated"),
            "model": row.get("ModelName"),
            "query": query,
            "response": response,
            "question_id": (question or {}).get("id", ""),
            "category": (question or {}).get("category", ""),
            "split": (question or {}).get("split", ""),
            "query_sha256": hashlib.sha256(prompt_key.encode("utf-8")).hexdigest(),
            "response_sha256": hashlib.sha256(response.encode("utf-8")).hexdigest(),
        }
    return sorted(candidates.values(), key=lambda row: (row["timestamp"] or "", row["trace_id"]))


def review_template(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "trace_id": row["trace_id"],
            "question_id": row.get("question_id", ""),
            "accepted": False,
            "split": row.get("split", ""),
            "category": row.get("category", ""),
            "rubric_score": None,
            "hard_gates": {gate: False for gate in REQUIRED_GATES},
            "review_reason": "",
            "query_preview": row["query"][:160],
        }
        for row in candidates
    ]


def curate(
    candidates_path: Path,
    review_path: Path,
    holdout_path: Path,
    scope_path: Path,
    instruction_path: Path,
    teacher_version: str | None = None,
    teacher_model: str | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    candidates = {row["trace_id"]: row for row in _load_jsonl(candidates_path)}
    reviews = _load_jsonl(review_path)
    holdout = _holdout_prompts(holdout_path)
    scope = json.loads(scope_path.read_text(encoding="utf-8"))
    if tuple(scope["required_checks"]) != REQUIRED_GATES:
        raise ValueError("Review rules list different required checks than the curation code.")
    minimum_score = float(scope["minimum_review_score"])
    system_prompt = instruction_path.read_text(encoding="utf-8").strip()
    accepted: list[tuple[dict[str, Any], dict[str, Any]]] = []
    seen_reviews: set[str] = set()

    for review in reviews:
        trace_id = str(review.get("trace_id") or "")
        if trace_id in seen_reviews:
            raise ValueError(f"Duplicate review for trace {trace_id}.")
        seen_reviews.add(trace_id)
        if not review.get("accepted"):
            continue
        if trace_id not in candidates:
            raise ValueError(f"Accepted trace {trace_id} is not in the candidate file.")
        score = review.get("rubric_score")
        if not isinstance(score, (int, float)) or score < minimum_score:
            raise ValueError(f"Accepted trace {trace_id} does not meet review score {minimum_score}.")
        gates = review.get("hard_gates") or {}
        failed = [gate for gate in REQUIRED_GATES if gates.get(gate) is not True]
        if failed:
            raise ValueError(f"Accepted trace {trace_id} failed gates: {', '.join(failed)}")
        if review.get("split") not in {"train", "validation"}:
            raise ValueError(f"Accepted trace {trace_id} must select train or validation split.")
        candidate = candidates[trace_id]
        if _normalized(candidate["query"]) in holdout:
            raise ValueError(f"Accepted trace {trace_id} overlaps the testing questions.")
        accepted.append((candidate, review))

    prompts = [_normalized(candidate["query"]) for candidate, _ in accepted]
    if len(prompts) != len(set(prompts)):
        raise ValueError("Accepted traces contain duplicate prompts.")

    train_pairs = [(candidate, review) for candidate, review in accepted if review["split"] == "train"]
    validation_pairs = [
        (candidate, review) for candidate, review in accepted if review["split"] == "validation"
    ]
    minimum_train = int(scope["minimum_training_examples"])
    minimum_validation = int(scope["minimum_validation_examples"])
    if len(train_pairs) < minimum_train or len(validation_pairs) < minimum_validation:
        raise ValueError(
            f"Need at least {minimum_train} train and {minimum_validation} validation traces; "
            f"found {len(train_pairs)} and {len(validation_pairs)}."
        )
    coverage = Counter(review["category"] for _, review in train_pairs)
    missing_coverage = {
        category: minimum - coverage[category]
        for category, minimum in scope["minimum_per_category"].items()
        if coverage[category] < minimum
    }
    if missing_coverage:
        raise ValueError(f"Training coverage is incomplete: {missing_coverage}")

    def sft_rows(pairs: list[tuple[dict[str, Any], dict[str, Any]]]) -> list[dict[str, Any]]:
        return [
            {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": candidate["query"]},
                    {"role": "assistant", "content": candidate["response"]},
                ]
            }
            for candidate, _ in sorted(pairs, key=lambda pair: pair[0]["trace_id"])
        ]

    provenance_examples = [
        {
            "trace_id": candidate["trace_id"],
            "timestamp": candidate["timestamp"],
            "model": candidate["model"],
            "query_sha256": candidate["query_sha256"],
            "response_sha256": candidate["response_sha256"],
            "split": review["split"],
            "category": review["category"],
            "rubric_score": review["rubric_score"],
            "review_reason": review.get("review_reason", ""),
        }
        for candidate, review in accepted
    ]
    provenance = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "Application Insights AppGenAIContent",
        "teacher_agent_version": teacher_version or scope["teacher_agent_version"],
        "teacher_model": teacher_model or scope["teacher_model"],
        "student_base_model": scope["student_base_model"],
        "never_train_on": scope["never_train_on"],
        "instruction_sha256": hashlib.sha256(system_prompt.encode("utf-8")).hexdigest(),
        "train_count": len(train_pairs),
        "validation_count": len(validation_pairs),
        "coverage": dict(sorted(coverage.items())),
        "examples": sorted(provenance_examples, key=lambda row: row["trace_id"]),
    }
    return sft_rows(train_pairs), sft_rows(validation_pairs), provenance


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    transform_parser = subparsers.add_parser("transform")
    transform_parser.add_argument("--raw", type=Path, required=True)
    transform_parser.add_argument("--holdout", type=Path, required=True)
    transform_parser.add_argument("--questions", type=Path, help="Keep only traces for these training questions.")
    transform_parser.add_argument("--candidates", type=Path, required=True)
    transform_parser.add_argument("--review", type=Path, required=True)

    curate_parser = subparsers.add_parser("curate")
    curate_parser.add_argument("--candidates", type=Path, required=True)
    curate_parser.add_argument("--review", type=Path, required=True)
    curate_parser.add_argument("--holdout", type=Path, required=True)
    curate_parser.add_argument("--scope", type=Path, required=True)
    curate_parser.add_argument("--instructions", type=Path, required=True)
    curate_parser.add_argument("--teacher-version", help="Agent version that wrote the answers (defaults to the review rules).")
    curate_parser.add_argument("--teacher-model", help="Model behind the teacher version (defaults to the review rules).")
    curate_parser.add_argument("--train", type=Path, required=True)
    curate_parser.add_argument("--validation", type=Path, required=True)
    curate_parser.add_argument("--provenance", type=Path, required=True)

    args = parser.parse_args()
    if args.command == "transform":
        candidates = transform(args.raw, args.holdout, args.questions)
        _write_jsonl(args.candidates, candidates)
        _write_jsonl(args.review, review_template(candidates))
        print(f"Trace candidates: {len(candidates)}")
        print(f"Candidates: {args.candidates}")
        print(f"Review file: {args.review}")
        return

    train, validation, provenance = curate(
        args.candidates,
        args.review,
        args.holdout,
        args.scope,
        args.instructions,
        args.teacher_version,
        args.teacher_model,
    )
    _write_jsonl(args.train, train)
    _write_jsonl(args.validation, validation)
    args.provenance.parent.mkdir(parents=True, exist_ok=True)
    args.provenance.write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    print(f"Training examples: {len(train)}")
    print(f"Validation examples: {len(validation)}")
    print("Testing-question overlap: 0")
    print(f"Provenance: {args.provenance}")


if __name__ == "__main__":
    main()