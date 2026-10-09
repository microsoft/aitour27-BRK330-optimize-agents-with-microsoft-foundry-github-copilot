from __future__ import annotations

from src.scripts.questions import TEST_ONLY, load, validate


def test_question_sets_are_ready() -> None:
    sets = validate()
    assert {name: len(rows) for name, rows in sets.items()} == {"exploring": 36, "training": 48, "testing": 24}


def test_testing_questions_only_use_reserved_scenarios() -> None:
    assert {row["family"] for row in load("testing")} <= set(TEST_ONLY)
