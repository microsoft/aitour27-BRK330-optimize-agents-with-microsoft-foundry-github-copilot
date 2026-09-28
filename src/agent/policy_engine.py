"""Caldova policy engine — hard gate for the concierge.

Every rule maps to an ID from data/policy/rules.json. Booking-blocking
outcomes carry a structured refusal that callers must surface without
override.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Any
try:
    from ..config import policy_rules, cities, hotels
except ImportError:
    from config import policy_rules, cities, hotels

@dataclass
class PolicyDecision:
    allowed: bool
    rule_id: str
    title: str
    reason: str
    remediation: str | None = None
    alternative_id: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def _city_tier(city_code: str) -> int:
    for city in cities():
        if city["code"] == city_code:
            return city["tier"]
    return 3


def _rule(rule_id: str) -> dict[str, Any]:
    for rule in policy_rules()["rules"]:
        if rule["id"] == rule_id:
            return rule
    raise KeyError(f"Unknown policy rule: {rule_id}")


def check_flight(flight: dict, traveler: dict, declared: dict | None = None) -> list[PolicyDecision]:
    decisions: list[PolicyDecision] = []
    duration = flight.get("duration_h", 0)
    cabin = flight.get("cabin", "economy")
    accessibility = (traveler or {}).get("accessibility", []) or (declared or {}).get("accessibility", [])
    # CT-01 cabin by duration
    if cabin == "business" and duration < 9 and not accessibility:
        decisions.append(PolicyDecision(
            allowed=False, rule_id="CT-01", title="Cabin class by flight duration",
            reason=f"Business class requested for a {duration}h flight without accessibility evidence.",
            remediation="Provide documented accessibility evidence or select premium economy / economy.",
        ))
    if cabin == "premium_economy" and duration < 6:
        decisions.append(PolicyDecision(
            allowed=True, rule_id="CT-01", title="Cabin class by flight duration",
            reason=f"Premium economy on a {duration}h flight is allowed but economy is preferred under 6h.",
            remediation="Prefer economy under 6h to stay under cost policy.",
        ))
    return decisions


def check_hotel(hotel: dict) -> list[PolicyDecision]:
    tier = _city_tier(hotel.get("city", ""))
    cap = _rule("CT-03")["caps_usd"][f"tier{tier}"]
    total = float(hotel.get("nightly_rate", 0)) + float(hotel.get("taxes_fees_nightly", 0))
    if total > cap:
        return [PolicyDecision(
            allowed=False, rule_id="CT-03", title="Hotel nightly cap by city tier",
            reason=f"{hotel.get('name')} nightly total ${total:.2f} exceeds Tier {tier} cap ${cap}.",
            remediation="Select a compliant hotel in this city or request Compliance approval (CT-10).",
            alternative_id=_alt_hotel_in_city(hotel.get("city", ""), cap),
        )]
    return []


def _alt_hotel_in_city(city: str, cap: float) -> str | None:
    for hotel in hotels():
        if hotel["city"] == city and (
            hotel["nightly_rate"] + hotel.get("taxes_fees_nightly", 0)
        ) <= cap:
            return hotel["id"]
    return None


def check_car(car: dict, travelers: int = 1, exception: str | None = None) -> list[PolicyDecision]:
    cls = car.get("class", "economy")
    if cls in ("economy", "compact"):
        return []
    if cls == "midsize" and travelers >= 3:
        return []
    if cls in ("suv", "luxury"):
        if exception and exception in ("winter_safety", "mountain_route", "accessibility"):
            return []
        return [PolicyDecision(
            allowed=False, rule_id="CT-04", title="Car rental class",
            reason=f"{cls.upper()} requires documented exception; none provided.",
            remediation="Provide a winter_safety, mountain_route, or accessibility exception; otherwise choose compact.",
        )]
    if cls == "midsize" and travelers < 3:
        return [PolicyDecision(
            allowed=False, rule_id="CT-04", title="Car rental class",
            reason="Midsize only permitted with 3+ travelers.",
            remediation="Choose economy or compact.",
        )]
    return []


def check_connection(prev_arrival_minutes: int, next_departure_minutes: int, international: bool) -> list[PolicyDecision]:
    gap = next_departure_minutes - prev_arrival_minutes
    minimum = 60 if international else 45
    if gap < minimum:
        return [PolicyDecision(
            allowed=False, rule_id="CT-09", title="Minimum connection time",
            reason=f"Only {gap} minutes between segments; minimum for {'international' if international else 'domestic'} is {minimum}.",
            remediation="Select a longer connection or reroute.",
        )]
    return []


def check_advance_booking(days_before: int, disruption: bool = False) -> list[PolicyDecision]:
    if disruption or days_before >= 7:
        return []
    return [PolicyDecision(
        allowed=False, rule_id="CT-02", title="Advance booking window",
        reason=f"Booking only {days_before} day(s) before departure; policy requires 7+ unless disruption.",
        remediation="Reschedule or provide a disruption exception.",
    )]


def check_expense_line(line: dict) -> list[PolicyDecision]:
    """Return a decision per line item flagged non-reimbursable per CT-20."""
    desc = line.get("description", "").lower()
    for keyword in ("minibar", "in-room movie", "movies", "spa", "companion", "alcohol", "prepaid fuel", "optional insurance"):
        if keyword in desc:
            return [PolicyDecision(
                allowed=False, rule_id="CT-20", title="Reimbursable receipt types",
                reason=f"Line '{line.get('description')}' is non-reimbursable ({keyword}).",
                remediation="Exclude from reimbursement request.",
            )]
    return []


def refuse_blanket(instruction: str) -> PolicyDecision | None:
    text = (instruction or "").lower()
    trap_phrases = [
        "approve every trip", "approve automatically", "regardless of destination",
        "even if compliance", "bypass policy", "skip approval", "without asking anyone",
    ]
    if any(p in text for p in trap_phrases):
        return PolicyDecision(
            allowed=False, rule_id="CT-11", title="No blanket approvals",
            reason="Instruction attempts to bypass Caldova policy controls.",
            remediation="Route through standard Compliance approval per CT-10.",
        )
    return None


def all_pass(decisions: list[PolicyDecision]) -> bool:
    return all(d.allowed for d in decisions)


def summarize(decisions: list[PolicyDecision]) -> dict[str, Any]:
    blocked = [d.to_dict() for d in decisions if not d.allowed]
    return {
        "hard_gate_blocked": len(blocked) > 0,
        "blocked_decisions": blocked,
        "cited_rule_ids": sorted({d.rule_id for d in decisions}),
    }
