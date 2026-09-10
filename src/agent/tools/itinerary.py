"""prepare_itinerary and submit_booking tools."""
from __future__ import annotations
from typing import Any
try:
    from ..telemetry import span, set_span_attr
    from ..config import flights, hotels, cars
except ImportError:
    from telemetry import span, set_span_attr
    from config import flights, hotels, cars


def _get(items, key, val):
    for i in items:
        if i.get(key) == val:
            return i
    return None


def prepare_itinerary(*, employee_id: str,
                     flight_ids: list[str] | None = None,
                     hotel_ids: list[str] | None = None,
                     car_ids: list[str] | None = None,
                     receipts: list[str] | None = None,
                     notes: str | None = None) -> dict[str, Any]:
    """Assemble a proposed itinerary from fixture ids."""
    with span("tool.prepare_itinerary", employee_id=employee_id):
        segs = []
        cost = 0.0
        for fid in flight_ids or []:
            f = _get(flights(), "id", fid)
            if f:
                segs.append({"kind": "flight", **f})
                cost += float(f["price"])
        for hid in hotel_ids or []:
            h = _get(hotels(), "id", hid)
            if h:
                segs.append({"kind": "hotel", **h})
                cost += float(h["nightly_rate"] + h.get("taxes_fees_nightly", 0))
        for cid in car_ids or []:
            c = _get(cars(), "id", cid)
            if c:
                segs.append({"kind": "car", **c})
                cost += float(c["daily_rate"])
        set_span_attr("tool.segment_count", len(segs))
        return {
            "employee_id": employee_id,
            "segments": segs,
            "estimated_cost_usd": round(cost, 2),
            "attached_receipts": receipts or [],
            "notes": notes,
        }


def submit_booking(*, itinerary: dict, dry_run: bool = True,
                   compliance_summary: dict | None = None) -> dict[str, Any]:
    """Dry-run booking. Blocks when compliance_summary contains any hard-gate violation."""
    with span("tool.submit_booking", dry_run=dry_run):
        blocked = (compliance_summary or {}).get("hard_gate_blocked", False)
        if blocked:
            set_span_attr("tool.booking_status", "blocked")
            return {
                "status": "blocked",
                "reason": "Caldova policy hard gate — see compliance_summary.blocked_decisions",
                "compliance_summary": compliance_summary,
                "itinerary": itinerary,
            }
        set_span_attr("tool.booking_status", "dry_run_success")
        return {
            "status": "dry_run_success" if dry_run else "committed",
            "reservation_ref": f"CT-DRY-{abs(hash(str(itinerary))) % 1_000_000:06d}",
            "itinerary": itinerary,
        }
