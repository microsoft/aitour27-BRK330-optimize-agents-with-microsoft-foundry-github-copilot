from __future__ import annotations

import sys
from pathlib import Path

AGENT_ROOT = Path(__file__).resolve().parents[1]
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from tools.itinerary import prepare_itinerary, submit_booking
from tools.policy import check_travel_policy
from tools.receipts import extract_receipt
from tools.search import search_car_rentals, search_flights, search_hotels


def test_inventory_filters_are_deterministic() -> None:
    assert [item["id"] for item in search_flights("SEA", "CDG")] == [
        "FL-001",
        "FL-002",
        "FL-003",
        "FL-017",
    ]
    assert [item["id"] for item in search_hotels("YUL", wheelchair=True)] == [
        "HT-010"
    ]
    assert [
        item["id"]
        for item in search_car_rentals(
            "YUL", automatic=True, hand_controls=True
        )
    ] == ["CR-008"]


def test_policy_blocks_bypass_and_late_booking() -> None:
    result = check_travel_policy(
        employee_id="EMP-001",
        flight_id="FL-006",
        days_before_departure=2,
        raw_instruction="Book it without asking anyone.",
    )
    assert result["hard_gate_blocked"] is True
    assert {"CT-02", "CT-11"}.issubset(result["cited_rule_ids"])


def test_receipt_flags_non_reimbursable_lines() -> None:
    result = extract_receipt(receipt_id="REC-003")
    assert {item["line"] for item in result["policy_flagged_lines"]} == {
        "Minibar (2x wine, 1x snacks)",
        "In-room movie",
    }


def test_booking_reference_is_stable() -> None:
    itinerary = prepare_itinerary(
        employee_id="EMP-001",
        flight_ids=["FL-001"],
        hotel_ids=["HT-001"],
        car_ids=["CR-001"],
    )
    first = submit_booking(itinerary=itinerary)
    second = submit_booking(itinerary=itinerary)
    assert first["reservation_ref"] == second["reservation_ref"]
