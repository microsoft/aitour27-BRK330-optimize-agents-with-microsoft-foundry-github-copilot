from __future__ import annotations

import json
from pathlib import Path

from src.training.trace_dataset import REQUIRED_GATES, curate, review_template, transform


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def _raw_row(index: int, query: str) -> dict:
    return {
        "TimeGenerated": f"2026-09-28T00:{index:02d}:00Z",
        "TraceId": f"trace-{index:02d}",
        "ModelName": "gpt-5.4-2026-03-05",
        "InputMessages": json.dumps(
            [{"role": "user", "parts": [{"type": "text", "content": query}]}]
        ),
        "OutputMessages": json.dumps(
            [
                {
                    "role": "assistant",
                    "parts": [{"type": "text", "content": f"Grounded response {index}"}],
                }
            ]
        ),
    }


def test_transform_excludes_holdout_and_deduplicates_latest(tmp_path: Path) -> None:
    raw = tmp_path / "raw.json"
    holdout = tmp_path / "holdout.jsonl"
    raw.write_text(
        json.dumps(
            [
                _raw_row(1, "Frozen prompt"),
                _raw_row(2, "Training prompt"),
                _raw_row(3, "Training   prompt"),
            ]
        ),
        encoding="utf-8",
    )
    _write_jsonl(holdout, [{"query": "Frozen prompt"}])

    candidates = transform(raw, holdout)

    assert len(candidates) == 1
    assert candidates[0]["trace_id"] == "trace-03"
    assert review_template(candidates)[0]["accepted"] is False


def test_transform_keeps_only_training_questions_and_prefills_review(tmp_path: Path) -> None:
    raw = tmp_path / "raw.json"
    holdout = tmp_path / "holdout.jsonl"
    questions = tmp_path / "training.jsonl"
    raw.write_text(json.dumps([_raw_row(1, "Training prompt"), _raw_row(2, "Exploring prompt")]), encoding="utf-8")
    _write_jsonl(holdout, [{"query": "Testing prompt"}])
    _write_jsonl(questions, [{"id": "TR-01", "category": "refusal", "split": "validation", "query": "Training prompt"}])

    candidates = transform(raw, holdout, questions)
    review = review_template(candidates)[0]

    assert [row["question_id"] for row in candidates] == ["TR-01"]
    assert review["category"] == "refusal"
    assert review["split"] == "validation"


def test_curate_enforces_review_gates_coverage_and_holdout_separation(tmp_path: Path) -> None:
    categories = {
        "compliant_planning": 6,
        "refusal": 4,
        "receipts": 4,
        "accessibility": 4,
        "numbers": 2,
    }
    candidates: list[dict] = []
    reviews: list[dict] = []
    index = 0
    for category, count in categories.items():
        for _ in range(count):
            index += 1
            candidate = {
                "trace_id": f"trace-{index:02d}",
                "timestamp": f"2026-09-28T00:{index:02d}:00Z",
                "model": "gpt-5.4-2026-03-05",
                "query": f"Training query {index}",
                "response": f"Grounded response {index}",
                "query_sha256": f"query-{index}",
                "response_sha256": f"response-{index}",
            }
            candidates.append(candidate)
            reviews.append(
                {
                    "trace_id": candidate["trace_id"],
                    "accepted": True,
                    "split": "train",
                    "category": category,
                    "rubric_score": 0.8,
                    "hard_gates": {gate: True for gate in REQUIRED_GATES},
                    "review_reason": "Reviewed synthetic trace.",
                }
            )
    for _ in range(4):
        index += 1
        candidate = {
            "trace_id": f"trace-{index:02d}",
            "timestamp": f"2026-09-28T00:{index:02d}:00Z",
            "model": "gpt-5.4-2026-03-05",
            "query": f"Validation query {index}",
            "response": f"Grounded response {index}",
            "query_sha256": f"query-{index}",
            "response_sha256": f"response-{index}",
        }
        candidates.append(candidate)
        reviews.append(
            {
                "trace_id": candidate["trace_id"],
                "accepted": True,
                "split": "validation",
                "category": "compliant_planning",
                "rubric_score": 0.8,
                "hard_gates": {gate: True for gate in REQUIRED_GATES},
                "review_reason": "Reviewed synthetic trace.",
            }
        )

    candidates_path = tmp_path / "candidates.jsonl"
    reviews_path = tmp_path / "reviews.jsonl"
    holdout_path = tmp_path / "holdout.jsonl"
    scope_path = tmp_path / "scope.json"
    instructions_path = tmp_path / "instructions.md"
    _write_jsonl(candidates_path, candidates)
    _write_jsonl(reviews_path, reviews)
    _write_jsonl(holdout_path, [{"query": "A different frozen query"}])
    scope_path.write_text(
        json.dumps(
            {
                "teacher_agent_version": "1",
                "teacher_model": "gpt-5.4",
                "student_base_model": "gpt-4.1-mini",
                "never_train_on": "holdout.jsonl",
                "minimum_training_examples": 20,
                "minimum_validation_examples": 4,
                "minimum_per_category": categories,
                "required_checks": list(REQUIRED_GATES),
                "minimum_review_score": 0.5,
            }
        ),
        encoding="utf-8",
    )
    instructions_path.write_text("Ground every answer.", encoding="utf-8")

    train, validation, provenance = curate(
        candidates_path,
        reviews_path,
        holdout_path,
        scope_path,
        instructions_path,
    )

    assert len(train) == 20
    assert len(validation) == 4
    assert provenance["train_count"] == 20
    assert provenance["validation_count"] == 4
    assert provenance["teacher_agent_version"] == "1"

    _, _, overridden = curate(
        candidates_path,
        reviews_path,
        holdout_path,
        scope_path,
        instructions_path,
        teacher_version="4",
        teacher_model="gpt-5.4",
    )
    assert overridden["teacher_agent_version"] == "4"