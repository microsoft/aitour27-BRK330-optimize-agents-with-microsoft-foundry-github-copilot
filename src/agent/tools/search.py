"""Search fixtures deterministically. No real APIs, no invented inventory."""
from __future__ import annotations
from typing import Any
try:
    from ..config import flights, hotels, cars, cities
    from ..telemetry import span, set_span_attr
except ImportError:
    from config import flights, hotels, cars, cities
    from telemetry import span, set_span_attr


def search_flights(origin: str, dest: str, cabin: str | None = None,
                   depart_after_hhmm: str | None = None,
                   refundable: bool | None = None,
                   preferred_only: bool = False) -> list[dict]:
    """Return matching flights from fixture data. Never fabricates a route."""
    with span("tool.search_flights", origin=origin, dest=dest, cabin=cabin or "*"):
        out = []
        for f in flights():
            if origin and f["origin"] != origin:
                continue
            if dest and f["dest"] != dest:
                continue
            if cabin and f["cabin"] != cabin:
                continue
            if refundable is True and not f.get("refundable"):
                continue
            if preferred_only and not f.get("preferred_vendor"):
                continue
            if depart_after_hhmm:
                if f["departure"].replace(":", "") < depart_after_hhmm:
                    continue
            out.append(f)
        set_span_attr("tool.result_count", len(out))
        return out


def search_hotels(city: str, wheelchair: bool = False, quiet: bool = False,
                  late_checkin: bool = False, max_nightly_total: float | None = None) -> list[dict]:
    with span("tool.search_hotels", city=city):
        out = []
        for h in hotels():
            if city and h["city"] != city:
                continue
            am = set(h.get("amenities", []))
            if wheelchair and not (h.get("wheelchair_accessible") or "wheelchair_accessible" in am):
                continue
            if quiet and "quiet_room" not in am:
                continue
            if late_checkin and "late_checkin" not in am:
                continue
            if max_nightly_total is not None:
                total = h["nightly_rate"] + h.get("taxes_fees_nightly", 0)
                if total > max_nightly_total:
                    continue
            out.append(h)
        set_span_attr("tool.result_count", len(out))
        return out


def search_car_rentals(city: str, cls: str | None = None,
                       automatic: bool | None = None,
                       hand_controls: bool = False) -> list[dict]:
    with span("tool.search_car_rentals", city=city, requested_class=cls or "*"):
        out = []
        for c in cars():
            if city and c["city"] != city:
                continue
            if cls and c["class"] != cls:
                continue
            if automatic is True and not c.get("automatic"):
                continue
            if hand_controls and not c.get("hand_controls_available"):
                continue
            out.append(c)
        set_span_attr("tool.result_count", len(out))
        return out


def resolve_city(city_hint: str) -> dict | None:
    """Fuzzy match user-provided city name to fixture code."""
    hint = (city_hint or "").strip().lower()
    for c in cities():
        if c["code"].lower() == hint or c["name"].lower() == hint:
            return c
    for c in cities():
        if hint in c["name"].lower():
            return c
    return None
