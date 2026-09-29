"""check_travel_policy tool — thin wrapper over the policy engine."""
from __future__ import annotations
from typing import Any
try:
    from ..config import flights, hotels, cars, employees
    from .. import policy_engine as pe
except ImportError:
    from config import flights, hotels, cars, employees
    import policy_engine as pe


def _get(items, key, value):
    for item in items:
        if item.get(key) == value:
            return item
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
    decisions: list[pe.PolicyDecision] = []
    errors: list[str] = []

    blanket = pe.refuse_blanket(raw_instruction or "")
    if blanket:
        decisions.append(blanket)

    traveler = _get(employees(), "id", employee_id) if employee_id else None
    if employee_id and traveler is None:
        errors.append(f"Unknown employee_id: {employee_id}")
    if flight_id:
        flight = _get(flights(), "id", flight_id)
        if flight:
            decisions.extend(pe.check_flight(flight, traveler or {}))
        else:
            errors.append(f"Unknown flight_id: {flight_id}")
    if hotel_id:
        hotel = _get(hotels(), "id", hotel_id)
        if hotel:
            decisions.extend(pe.check_hotel(hotel))
        else:
            errors.append(f"Unknown hotel_id: {hotel_id}")
    if car_id:
        car = _get(cars(), "id", car_id)
        if car:
            decisions.extend(pe.check_car(car, travelers=travelers, exception=car_exception))
        else:
            errors.append(f"Unknown car_id: {car_id}")
    if days_before_departure is not None:
        decisions.extend(pe.check_advance_booking(days_before_departure, disruption=disruption))

    return {
        **pe.summarize(decisions),
        "decisions": [decision.to_dict() for decision in decisions],
        "errors": errors,
    }
