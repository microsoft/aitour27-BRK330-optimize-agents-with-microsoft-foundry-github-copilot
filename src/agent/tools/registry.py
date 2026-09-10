"""OpenAI function-calling schema for the concierge tools.

Kept as pure Python so the same registry is used by both the Foundry hosted
agent and any local invoke for smoke tests.
"""
from __future__ import annotations
from .search import search_flights, search_hotels, search_car_rentals
from .policy import check_travel_policy
from .receipts import extract_receipt
from .itinerary import prepare_itinerary, submit_booking

TOOL_FUNCTIONS = {
    "search_flights": search_flights,
    "search_hotels": search_hotels,
    "search_car_rentals": search_car_rentals,
    "check_travel_policy": check_travel_policy,
    "extract_receipt": extract_receipt,
    "prepare_itinerary": prepare_itinerary,
    "submit_booking": submit_booking,
}

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_flights",
            "description": "Search deterministic flight fixtures. Never fabricates a route. Filter by origin/dest/cabin/refundable/preferred and optional depart_after_hhmm (HHMM string).",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {"type": "string", "description": "IATA-ish code, e.g. SEA"},
                    "dest":   {"type": "string"},
                    "cabin":  {"type": "string", "enum": ["economy", "premium_economy", "business"]},
                    "depart_after_hhmm": {"type": "string", "description": "HHMM string e.g. 0800"},
                    "refundable":    {"type": "boolean"},
                    "preferred_only":{"type": "boolean"},
                },
                "required": ["origin", "dest"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_hotels",
            "description": "Search hotels by city with optional accessibility / quiet / late checkin / rate cap.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city":   {"type": "string", "description": "City code, e.g. PAR"},
                    "wheelchair": {"type": "boolean"},
                    "quiet": {"type": "boolean"},
                    "late_checkin": {"type": "boolean"},
                    "max_nightly_total": {"type": "number"},
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_car_rentals",
            "description": "Search car rentals by city, class, transmission, hand controls.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "cls":  {"type": "string", "enum": ["economy", "compact", "midsize", "suv", "luxury"]},
                    "automatic": {"type": "boolean"},
                    "hand_controls": {"type": "boolean"},
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_travel_policy",
            "description": "Apply Caldova policy as a hard gate to a proposed booking. Returns cited_rule_ids and blocked_decisions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_id": {"type": "string"},
                    "flight_id":   {"type": "string"},
                    "hotel_id":    {"type": "string"},
                    "car_id":      {"type": "string"},
                    "travelers":   {"type": "integer"},
                    "car_exception": {"type": "string"},
                    "days_before_departure": {"type": "integer"},
                    "disruption":  {"type": "boolean"},
                    "raw_instruction": {"type": "string"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "extract_receipt",
            "description": "Extract structured fields from a receipt. Applies CT-20 line-level rules and returns policy_flagged_lines.",
            "parameters": {
                "type": "object",
                "properties": {
                    "receipt_id": {"type": "string"},
                    "image_path": {"type": "string"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "prepare_itinerary",
            "description": "Assemble a proposed itinerary from fixture ids.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_id": {"type": "string"},
                    "flight_ids": {"type": "array", "items": {"type": "string"}},
                    "hotel_ids":  {"type": "array", "items": {"type": "string"}},
                    "car_ids":    {"type": "array", "items": {"type": "string"}},
                    "receipts":   {"type": "array", "items": {"type": "string"}},
                    "notes":      {"type": "string"},
                },
                "required": ["employee_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "submit_booking",
            "description": "Dry-run booking. Hard-gate blocked when compliance_summary.hard_gate_blocked is true.",
            "parameters": {
                "type": "object",
                "properties": {
                    "itinerary": {"type": "object"},
                    "dry_run":   {"type": "boolean"},
                    "compliance_summary": {"type": "object"},
                },
                "required": ["itinerary"],
            },
        },
    },
]
