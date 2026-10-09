"""Search deterministic fixture inventory without external APIs."""
from __future__ import annotations

try:
    from ..config import airports, flights, hotels, cars, cities
except ImportError:
    from config import airports, flights, hotels, cars, cities


def place_code(value: str | None) -> str:
    """Normalize a city code, airport code, or city name to the fixture city code (CDG -> PAR)."""
    text = (value or "").strip()
    code = text.upper()
    by_name = {city["name"].lower(): city["code"] for city in cities()}
    if code in by_name.values():
        return code
    for airport in airports():
        if airport["iata"] == code:
            return by_name.get(airport["city"].lower(), code)
    return by_name.get(text.lower(), code)


def _same_place(fixture_value: str, requested: str | None) -> bool:
    return not requested or place_code(fixture_value) == place_code(requested)


def search_flights(origin: str, dest: str, cabin: str | None = None,
                   depart_after_hhmm: str | None = None,
                   refundable: bool | None = None,
                   preferred_only: bool = False) -> list[dict]:
    """Return matching flights from fixture data. Never fabricates a route."""
    results = []
    for flight in flights():
        if not _same_place(flight["origin"], origin):
            continue
        if not _same_place(flight["dest"], dest):
            continue
        if cabin and flight["cabin"] != cabin:
            continue
        if refundable is True and not flight.get("refundable"):
            continue
        if preferred_only and not flight.get("preferred_vendor"):
            continue
        if depart_after_hhmm and flight["departure"].replace(":", "") < depart_after_hhmm:
            continue
        results.append(flight)
    return results


def search_hotels(city: str, wheelchair: bool = False, quiet: bool = False,
                  late_checkin: bool = False, max_nightly_total: float | None = None,
                  step_free: bool = False) -> list[dict]:
    results = []
    for hotel in hotels():
        if not _same_place(hotel["city"], city):
            continue
        amenities = set(hotel.get("amenities", []))
        if wheelchair and not (
            hotel.get("wheelchair_accessible") or "wheelchair_accessible" in amenities
        ):
            continue
        # Step-free is weaker than wheelchair accessible; never treat it as wheelchair access.
        if step_free and "step_free" not in amenities:
            continue
        if quiet and "quiet_room" not in amenities:
            continue
        if late_checkin and "late_checkin" not in amenities:
            continue
        if max_nightly_total is not None:
            total = hotel["nightly_rate"] + hotel.get("taxes_fees_nightly", 0)
            if total > max_nightly_total:
                continue
        results.append(hotel)
    return results


def search_car_rentals(city: str, cls: str | None = None,
                       automatic: bool | None = None,
                       hand_controls: bool = False) -> list[dict]:
    results = []
    for car in cars():
        if not _same_place(car["city"], city):
            continue
        if cls and car["class"] != cls:
            continue
        if automatic is True and not car.get("automatic"):
            continue
        if hand_controls and not car.get("hand_controls_available"):
            continue
        results.append(car)
    return results


def lookup_fixtures(fixture_ids: list[str]) -> list[dict]:
    """Return flight, hotel, or car records by ID; hotels include the nightly total with taxes and fees."""
    catalog = {item["id"]: item for item in [*flights(), *hotels(), *cars()]}
    results = []
    for fixture_id in fixture_ids:
        item = catalog.get(str(fixture_id).strip().upper())
        if item is None:
            results.append({"id": fixture_id, "error": "Unknown fixture id"})
        elif "nightly_rate" in item:
            results.append({**item, "nightly_total": item["nightly_rate"] + item.get("taxes_fees_nightly", 0)})
        else:
            results.append(item)
    return results


def resolve_city(city_hint: str) -> dict | None:
    """Fuzzy match user-provided city name to fixture code."""
    hint = (city_hint or "").strip().lower()
    for city in cities():
        if city["code"].lower() == hint or city["name"].lower() == hint:
            return city
    for city in cities():
        if hint in city["name"].lower():
            return city
    return None
