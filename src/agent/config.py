"""Runtime configuration for the Contoso Travel Concierge hosted agent."""
from __future__ import annotations
import json, os
from dataclasses import dataclass
from pathlib import Path
from functools import lru_cache

_HERE = Path(__file__).resolve().parent
_REPO_ROOT_CANDIDATES = [_HERE.parents[i] for i in range(min(3, len(_HERE.parents)))]

# Prefer fixtures/ next to this module (container layout: azd prepackage hook
# mirrors data/ into src/agent/fixtures/). Fall back to repo-root data/ for
# local development.
_LOCAL_FIXTURES = _HERE / "fixtures"
if _LOCAL_FIXTURES.exists():
    DATA_DIR = _LOCAL_FIXTURES
    REPO_ROOT = _HERE
else:
    for _r in _REPO_ROOT_CANDIDATES:
        if (_r / "data").exists():
            REPO_ROOT = _r
            DATA_DIR = _r / "data"
            break
    else:
        REPO_ROOT = _HERE
        DATA_DIR = _HERE

@dataclass(frozen=True)
class AgentSettings:
    project_endpoint: str
    model_deployment: str
    variant: str  # "baseline" | "routed" | "student"
    app_insights_connection_string: str
    max_output_tokens: int
    fixture_currency: str

@lru_cache(maxsize=1)
def load_settings() -> AgentSettings:
    return AgentSettings(
        project_endpoint=os.getenv("AZURE_AI_PROJECT_ENDPOINT", ""),
        model_deployment=os.getenv("CONTOSO_MODEL_DEPLOYMENT", "gpt-5"),
        variant=os.getenv("CONTOSO_VARIANT", "baseline"),
        app_insights_connection_string=os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING", ""),
        max_output_tokens=int(os.getenv("CONTOSO_MAX_OUTPUT_TOKENS", "1600")),
        fixture_currency=os.getenv("CONTOSO_FIXTURE_CURRENCY", "USD"),
    )

@lru_cache(maxsize=1)
def load_json(name: str) -> dict:
    """Load a JSON fixture by relative path under data/."""
    with (DATA_DIR / name).open() as f:
        return json.load(f)

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
