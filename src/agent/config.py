"""Runtime configuration and deterministic fixture loading."""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_LOCAL_FIXTURES = _HERE / "fixtures"


def fixture_dir() -> Path:
    """Resolve packaged fixtures first, then the repository development path."""
    configured = os.getenv("CONTOSO_FIXTURES_DIR")
    candidates = [Path(configured)] if configured else []
    candidates.append(_LOCAL_FIXTURES)
    if len(_HERE.parents) > 1:
        candidates.append(_HERE.parents[1] / "data" / "fixtures")
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    attempted = ", ".join(str(path) for path in candidates)
    raise FileNotFoundError(f"Contoso fixtures not found; checked: {attempted}")

@lru_cache(maxsize=1)
def load_json(name: str) -> Any:
    """Load a JSON fixture by relative path under the resolved fixture root."""
    with (fixture_dir() / name).open(encoding="utf-8") as file_handle:
        return json.load(file_handle)

@lru_cache(maxsize=1)
def policy_rules() -> dict:
    return load_json("policy/rules.json")

@lru_cache(maxsize=1)
def airports() -> list:
    return load_json("catalogs/airports.json")

@lru_cache(maxsize=1)
def cities() -> list:
    return load_json("catalogs/cities.json")

@lru_cache(maxsize=1)
def flights() -> list:
    return load_json("catalogs/flights.json")["flights"]

@lru_cache(maxsize=1)
def hotels() -> list:
    return load_json("catalogs/hotels.json")["hotels"]

@lru_cache(maxsize=1)
def cars() -> list:
    return load_json("catalogs/car_rentals.json")["cars"]

@lru_cache(maxsize=1)
def exchange_rates() -> dict:
    return load_json("catalogs/exchange_rates.json")

@lru_cache(maxsize=1)
def employees() -> list:
    return load_json("employees/profiles.json")["employees"]
