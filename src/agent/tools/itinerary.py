"""prepare_itinerary and submit_booking tools."""
from __future__ import annotations
import hashlib
import json
from typing import Any
try:
    from ..config import flights, hotels, cars
except ImportError:
    from config import flights, hotels, cars


def _get(items, key, value):
    for item in items:
        if item.get(key) == value:
            return item
    return None


def prepare_itinerary(*, employee_id: str,
                     flight_ids: list[str] | None = None,
                     hotel_ids: list[str] | None = None,
                     car_ids: list[str] | None = None,
                     receipts: list[str] | None = None,
                     notes: str | None = None) -> dict[str, Any]:
    """Assemble a proposed itinerary from fixture ids."""
    segments = []
    missing_ids = []
    cost = 0.0
    for flight_id in flight_ids or []:
        flight = _get(flights(), "id", flight_id)
        if flight:
            segments.append({"kind": "flight", **flight})
            cost += float(flight["price"])
        else:
            missing_ids.append(flight_id)
    for hotel_id in hotel_ids or []:
        hotel = _get(hotels(), "id", hotel_id)
        if hotel:
            segments.append({"kind": "hotel", **hotel})
            cost += float(hotel["nightly_rate"] + hotel.get("taxes_fees_nightly", 0))
        else:
            missing_ids.append(hotel_id)
    for car_id in car_ids or []:
        car = _get(cars(), "id", car_id)
        if car:
            segments.append({"kind": "car", **car})
            cost += float(car["daily_rate"])
        else:
            missing_ids.append(car_id)
    return {
        "employee_id": employee_id,
        "segments": segments,
        "missing_fixture_ids": missing_ids,
        "estimated_cost_usd": round(cost, 2),
        "attached_receipts": receipts or [],
        "notes": notes,
    }


def submit_booking(*, itinerary: dict, dry_run: bool = True,
                   compliance_summary: dict | None = None) -> dict[str, Any]:
    """Dry-run booking. Blocks when compliance_summary contains any hard-gate violation."""
    if not dry_run:
        return {
            "status": "blocked",
            "reason": "Live booking is disabled; use dry_run=true.",
            "itinerary": itinerary,
        }
    if compliance_summary is None or "hard_gate_blocked" not in compliance_summary:
        return {
            "status": "blocked",
            "reason": "Explicit policy compliance evidence is required before a booking dry-run.",
            "itinerary": itinerary,
        }
    blocked = compliance_summary["hard_gate_blocked"]
    if blocked:
        return {
            "status": "blocked",
            "reason": "Caldova policy hard gate; see compliance_summary.blocked_decisions",
            "compliance_summary": compliance_summary,
            "itinerary": itinerary,
        }
    serialized = json.dumps(itinerary, sort_keys=True, separators=(",", ":"))
    reference = hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:10].upper()
    return {
        "status": "dry_run_success",
        "reservation_ref": f"CT-DRY-{reference}",
        "itinerary": itinerary,
    }
