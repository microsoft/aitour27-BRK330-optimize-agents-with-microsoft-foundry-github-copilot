"""check_travel_policy tool — thin wrapper over the policy engine."""
from __future__ import annotations
from typing import Any
try:
    from ..config import flights, hotels, cars, employees
    from ..telemetry import span
    from .. import policy_engine as pe
except ImportError:
    from config import flights, hotels, cars, employees
    from telemetry import span
    import policy_engine as pe


def _get(items, key, val):
    for i in items:
        if i.get(key) == val:
            return i
    return None


def check_travel_policy(*, employee_id: str | None = None,
                       flight_id: str | None = None,
                       hotel_id: str | None = None,
                       car_id: str | None = None,
                       travelers: int = 1,
                       car_exception: str | None = None,
                       declared_uncertainty: bool = False,
                       days_before_departure: int | None = None,
                       disruption: bool = False,
                       raw_instruction: str | None = None) -> dict[str, Any]:
    """Apply Caldova policy to a proposed booking action. Every violation is
    returned as a structured blocked decision that the UI must surface."""
    with span("tool.check_travel_policy",
              employee_id=employee_id or "-",
              flight_id=flight_id or "-",
              hotel_id=hotel_id or "-",
              car_id=car_id or "-"):
        decisions: list[pe.PolicyDecision] = []

        blanket = pe.refuse_blanket(raw_instruction or "")
        if blanket:
            decisions.append(blanket)

        traveler = _get(employees(), "id", employee_id) if employee_id else None

        if flight_id:
            fl = _get(flights(), "id", flight_id)
            if fl:
                decisions.extend(pe.check_flight(fl, traveler or {}))
        if hotel_id:
            h = _get(hotels(), "id", hotel_id)
            if h:
                decisions.extend(pe.check_hotel(h))
        if car_id:
            c = _get(cars(), "id", car_id)
            if c:
                decisions.extend(pe.check_car(c, travelers=travelers, exception=car_exception))
        if days_before_departure is not None:
            decisions.extend(pe.check_advance_booking(days_before_departure, disruption=disruption))

        return {
            **pe.summarize(decisions),
            "decisions": [d.to_dict() for d in decisions],
        }
