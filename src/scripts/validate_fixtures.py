#!/usr/bin/env python3
"""Validate deterministic BRK330 fixtures and cross-file references.

Usage:
    python src/scripts/validate_fixtures.py
    python src/scripts/validate_fixtures.py --root data/fixtures

The command is read-only. It prints a summary and exits nonzero when fixture
JSON, dates, arithmetic, IDs, or references are inconsistent.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

DATE_PATTERN = re.compile(r"20\d{2}-\d{2}-\d{2}")
MINIMUM_DATE = date(2027, 7, 1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("data/fixtures"),
        help="Fixture root (default: data/fixtures).",
    )
    return parser.parse_args()


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Cannot load {path}: {error}") from error


def index_by_id(items: list[dict[str, Any]], label: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in items:
        item_id = item["id"]
        if item_id in result:
            raise ValueError(f"Duplicate {label} id: {item_id}")
        result[item_id] = item
    return result


def assert_close(actual: float, expected: float, label: str) -> None:
    if round(actual, 2) != round(expected, 2):
        raise ValueError(f"{label}: expected {expected:.2f}, got {actual:.2f}")


def validate_dates(json_files: list[Path]) -> None:
    for path in json_files:
        for value in DATE_PATTERN.findall(path.read_text(encoding="utf-8")):
            parsed = date.fromisoformat(value)
            if parsed < MINIMUM_DATE:
                raise ValueError(f"{path}: stale date {value}; expected {MINIMUM_DATE} or later")


def validate_receipts(root: Path, rules: set[str]) -> set[str]:
    receipt_ids: set[str] = set()
    for path in sorted((root / "receipts").glob("REC-*.json")):
        receipt = load_json(path)
        receipt_id = receipt["receipt_id"]
        if receipt_id in receipt_ids:
            raise ValueError(f"Duplicate receipt id: {receipt_id}")
        receipt_ids.add(receipt_id)
        if receipt.get("generated") != "deterministic-synthetic":
            raise ValueError(f"{path}: missing deterministic synthetic marker")
        image_path = path.with_suffix(".png")
        if not image_path.exists() or image_path.stat().st_size == 0:
            raise ValueError(f"{path}: missing generated image {image_path.name}")
        for line_item in receipt.get("line_items", []):
            rule_id = line_item.get("rule")
            if rule_id and rule_id not in rules:
                raise ValueError(f"{path}: unknown policy rule {rule_id}")

    receipt_1 = load_json(root / "receipts" / "REC-001.json")
    assert_close(
        receipt_1["subtotal_usd"] + receipt_1["tax_usd"] + receipt_1["fees_usd"],
        receipt_1["total_usd"],
        "REC-001 total",
    )
    if receipt_1["total_usd"] > 150:
        raise ValueError("REC-001 exceeds the CT-27 incidental cap")

    receipt_2 = load_json(root / "receipts" / "REC-002.json")
    assert_close(
        receipt_2["subtotal_ht_eur"] + receipt_2["tax_eur"] + receipt_2["fees_eur"],
        receipt_2["total_ttc_eur"],
        "REC-002 total",
    )
    assert_close(
        receipt_2["total_ttc_eur"] * receipt_2["conversion"]["fixture_rate_usd_per_eur"],
        receipt_2["conversion"]["total_usd_equivalent"],
        "REC-002 conversion",
    )

    for receipt_id in ("REC-003", "REC-004"):
        receipt = load_json(root / "receipts" / f"{receipt_id}.json")
        currency_key = "amount_eur" if receipt_id == "REC-003" else "amount_usd"
        totals_key = "totals_eur" if receipt_id == "REC-003" else "totals_usd"
        totals = receipt[totals_key]
        reimbursable = sum(
            item[currency_key] for item in receipt["line_items"] if item["reimbursable"]
        )
        not_reimbursable = sum(
            item[currency_key] for item in receipt["line_items"] if not item["reimbursable"]
        )
        assert_close(reimbursable, totals["reimbursable"], f"{receipt_id} reimbursable")
        assert_close(
            not_reimbursable,
            totals["not_reimbursable"],
            f"{receipt_id} not reimbursable",
        )
        assert_close(reimbursable + not_reimbursable, totals["grand_total"], f"{receipt_id} total")
    return receipt_ids


def validate_itineraries(
    root: Path,
    flights: dict[str, dict[str, Any]],
    hotels: dict[str, dict[str, Any]],
    cars: dict[str, dict[str, Any]],
    employees: set[str],
    receipts: set[str],
    rules: set[str],
) -> int:
    count = 0
    for path in sorted((root / "itineraries").glob("ITN-*.json")):
        itinerary = load_json(path)
        count += 1
        if itinerary.get("generated") != "deterministic-synthetic":
            raise ValueError(f"{path}: missing deterministic synthetic marker")
        if itinerary["traveler"] not in employees:
            raise ValueError(f"{path}: unknown traveler {itinerary['traveler']}")
        if not set(itinerary["receipts"]).issubset(receipts):
            raise ValueError(f"{path}: unknown receipt reference")
        if not {check["rule"] for check in itinerary["policy_checks"]}.issubset(rules):
            raise ValueError(f"{path}: unknown policy reference")
        start, end = (date.fromisoformat(value) for value in itinerary["trip_window"])
        previous_flight_destination: str | None = None
        for segment in itinerary["segments"]:
            kind = segment["kind"]
            if kind in {"flight", "return_flight"}:
                fixture = flights.get(segment["id"])
                if fixture is None:
                    raise ValueError(f"{path}: unknown flight {segment['id']}")
                if (segment["origin"], segment["dest"]) != (fixture["origin"], fixture["dest"]):
                    raise ValueError(f"{path}: route mismatch for {segment['id']}")
                if previous_flight_destination and segment["origin"] != previous_flight_destination:
                    raise ValueError(f"{path}: disconnected flight before {segment['id']}")
                previous_flight_destination = segment["dest"]
            elif kind == "hotel":
                fixture = hotels.get(segment["id"])
                if fixture is None or fixture["city"] != segment["city"]:
                    raise ValueError(f"{path}: invalid hotel reference {segment['id']}")
                if "nights" in segment:
                    nights = (
                        date.fromisoformat(segment["check_out"])
                        - date.fromisoformat(segment["check_in"])
                    ).days
                    if nights != segment["nights"]:
                        raise ValueError(f"{path}: hotel night count mismatch")
            elif kind == "car":
                fixture = cars.get(segment["id"])
                if fixture is None or fixture["city"] != segment["city"]:
                    raise ValueError(f"{path}: invalid car reference {segment['id']}")
            else:
                raise ValueError(f"{path}: unsupported segment kind {kind}")
            for field_name in ("date", "check_in", "check_out", "pickup", "return"):
                if field_name in segment:
                    segment_date = date.fromisoformat(segment[field_name])
                    if not start <= segment_date <= end:
                        raise ValueError(f"{path}: {field_name} outside trip window")

        estimated_cost = itinerary.get("estimated_cost_usd")
        if estimated_cost:
            expected_total = sum(
                value for key, value in estimated_cost.items() if key != "total_reimbursable"
            )
            assert_close(expected_total, estimated_cost["total_reimbursable"], f"{path.name} cost")
    return count


def validate(root: Path) -> dict[str, int]:
    root = root.resolve()
    required_files = [
        "catalogs/flights.json",
        "catalogs/hotels.json",
        "catalogs/car_rentals.json",
        "catalogs/exchange_rates.json",
        "employees/profiles.json",
        "policy/rules.json",
        "policy/caldova-travel-policy.md",
    ]
    for relative_path in required_files:
        if not (root / relative_path).exists():
            raise ValueError(f"Missing fixture: {relative_path}")

    json_files = sorted(root.rglob("*.json"))
    for path in json_files:
        load_json(path)
    validate_dates(json_files)

    flights = index_by_id(load_json(root / "catalogs" / "flights.json")["flights"], "flight")
    hotels = index_by_id(load_json(root / "catalogs" / "hotels.json")["hotels"], "hotel")
    cars = index_by_id(load_json(root / "catalogs" / "car_rentals.json")["cars"], "car")
    employee_data = load_json(root / "employees" / "profiles.json")
    employees = set(index_by_id(employee_data["employees"], "employee"))
    rule_data = load_json(root / "policy" / "rules.json")
    rules = set(index_by_id(rule_data["rules"], "rule"))
    receipts = validate_receipts(root, rules)
    itinerary_count = validate_itineraries(
        root, flights, hotels, cars, employees, receipts, rules
    )
    return {
        "json_files": len(json_files),
        "flights": len(flights),
        "hotels": len(hotels),
        "cars": len(cars),
        "employees": len(employees),
        "rules": len(rules),
        "receipts": len(receipts),
        "itineraries": itinerary_count,
    }


def main() -> None:
    args = parse_args()
    try:
        summary = validate(args.root)
    except (KeyError, TypeError, ValueError) as error:
        raise SystemExit(f"Fixture validation failed: {error}") from error
    details = ", ".join(f"{name}={count}" for name, count in summary.items())
    print(f"Fixture validation passed: {details}")


if __name__ == "__main__":
    main()
