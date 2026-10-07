from __future__ import annotations

import json
from pathlib import Path

from src.training.trace_dataset import REQUIRED_GATES, agent_tool_schemas, curate, review_template, transform


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


def test_transform_keeps_tool_calls_from_the_final_pass(tmp_path: Path) -> None:
    query = "Is Retiro Business in Madrid within policy?"
    user = {"role": "user", "parts": [{"type": "text", "content": query}]}
    call = {
        "role": "assistant",
        "parts": [
            {"type": "text", "content": "I'll look up Madrid hotels."},
            {"type": "tool_call", "id": "call_1", "name": "search_hotels", "arguments": {"city": "MAD"}},
        ],
    }
    result = {
        "role": "tool",
        "parts": [{"type": "tool_call_response", "id": "call_1", "response": '[{"id": "HT-016"}]'}],
    }
    final = {"role": "assistant", "parts": [{"type": "text", "content": "HT-016 totals $211 per night."}]}
    common = {"TraceId": "trace-loop", "ModelName": "gpt-5.4-2026-03-05"}
    raw = tmp_path / "raw.json"
    holdout = tmp_path / "holdout.jsonl"
    raw.write_text(
        json.dumps(
            [
                {**common, "TimeGenerated": "2026-10-06T00:00:01Z",
                 "InputMessages": json.dumps([user]), "OutputMessages": json.dumps([call])},
                {**common, "TimeGenerated": "2026-10-06T00:00:02Z",
                 "InputMessages": json.dumps([user, call, result]), "OutputMessages": json.dumps([final])},
            ]
        ),
        encoding="utf-8",
    )
    _write_jsonl(holdout, [{"query": "Testing prompt"}])

    [candidate] = transform(raw, holdout)

    assert candidate["response"] == "HT-016 totals $211 per night."
    assert candidate["tools_called"] == ["search_hotels"]
    assert [message["role"] for message in candidate["messages"]] == ["user", "assistant", "tool", "assistant"]
    assert candidate["messages"][1]["tool_calls"][0]["function"] == {
        "name": "search_hotels",
        "arguments": '{"city": "MAD"}',
    }
    assert candidate["messages"][2] == {"role": "tool", "tool_call_id": "call_1", "content": '[{"id": "HT-016"}]'}


def test_transform_pairs_tool_results_without_ids_in_order(tmp_path: Path) -> None:
    query = "Compare Seattle to Paris flights."
    user = {"role": "user", "parts": [{"type": "text", "content": query}]}
    calls = {
        "role": "assistant",
        "parts": [
            {"type": "tool_call", "name": "search_flights", "arguments": {"origin": "SEA", "destination": "PAR"}},
            {"type": "tool_call", "name": "check_travel_policy", "arguments": {"employee_id": "EMP-001"}},
        ],
    }
    results = {
        "role": "tool",
        "parts": [
            {"type": "tool_call_response", "response": "[]"},
            {"type": "tool_call_response", "response": '{"decisions": []}'},
            {"type": "tool_call_response", "response": "unmatched"},
        ],
    }
    final = {"role": "assistant", "parts": [{"type": "text", "content": "No Paris flights matched."}]}
    raw = tmp_path / "raw.json"
    holdout = tmp_path / "holdout.jsonl"
    raw.write_text(
        json.dumps(
            [
                {"TraceId": "trace-noid", "ModelName": "gpt-5.4", "TimeGenerated": "2026-10-06T00:00:02Z",
                 "InputMessages": json.dumps([user, calls, results]), "OutputMessages": json.dumps([final])},
            ]
        ),
        encoding="utf-8",
    )
    _write_jsonl(holdout, [{"query": "Testing prompt"}])

    [candidate] = transform(raw, holdout)

    call_ids = [call["id"] for call in candidate["messages"][1]["tool_calls"]]
    tool_rows = [message for message in candidate["messages"] if message["role"] == "tool"]
    assert len(set(call_ids)) == 2
    assert [row["tool_call_id"] for row in tool_rows] == call_ids
    assert [row["content"] for row in tool_rows] == ["[]", '{"decisions": []}']


def test_transform_unwraps_parallel_tool_calls(tmp_path: Path) -> None:
    query = "Plan a Seattle to Berlin trip."
    user = {"role": "user", "parts": [{"type": "text", "content": query}]}
    wrapper = {
        "role": "assistant",
        "parts": [
            {
                "type": "tool_call",
                "name": "multi_tool_use.parallel",
                "arguments": json.dumps(
                    {
                        "tool_uses": [
                            {"recipient_name": "functions.search_flights", "parameters": {"origin": "SEA", "destination": "CDG"}},
                            {"recipient_name": "functions.search_hotels", "parameters": {"city": "BER"}},
                        ]
                    }
                ),
            }
        ],
    }
    results = [
        {"role": "tool", "parts": [{"type": "tool_call_response", "response": '[{"id": "FL-001"}]'}]},
        {"role": "tool", "parts": [{"type": "tool_call_response", "response": '[{"id": "HT-005"}]'}]},
    ]
    final = {"role": "assistant", "parts": [{"type": "text", "content": "FL-001 and HT-005."}]}
    raw = tmp_path / "raw.json"
    holdout = tmp_path / "holdout.jsonl"
    raw.write_text(
        json.dumps(
            [
                {"TraceId": "trace-parallel", "ModelName": "gpt-5.4", "TimeGenerated": "2026-10-06T00:00:02Z",
                 "InputMessages": json.dumps([user, wrapper, *results]), "OutputMessages": json.dumps([final])},
            ]
        ),
        encoding="utf-8",
    )
    _write_jsonl(holdout, [{"query": "Testing prompt"}])

    [candidate] = transform(raw, holdout)

    calls = candidate["messages"][1]["tool_calls"]
    assert [call["function"]["name"] for call in calls] == ["search_flights", "search_hotels"]
    assert json.loads(calls[1]["function"]["arguments"]) == {"city": "BER"}
    assert candidate["tools_called"] == ["search_flights", "search_hotels"]
    tool_rows = [message for message in candidate["messages"] if message["role"] == "tool"]
    assert [row["tool_call_id"] for row in tool_rows] == [call["id"] for call in calls]


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


def test_agent_tool_schemas_match_the_hosted_agent() -> None:
    schemas = agent_tool_schemas()

    names = {schema["function"]["name"] for schema in schemas}
    assert {"search_hotels", "check_travel_policy"} <= names
    assert all(schema["type"] == "function" and "parameters" in schema["function"] for schema in schemas)