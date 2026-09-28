"""Agent Framework tool definitions over deterministic fixture helpers."""
from __future__ import annotations

import json
from typing import Annotated, Any

from agent_framework import tool
from pydantic import Field

from tools import search as search_tools
from tools.itinerary import prepare_itinerary as _prepare_itinerary
from tools.itinerary import submit_booking as _submit_booking
from tools.policy import check_travel_policy as _check_travel_policy
from tools.receipts import extract_receipt as _extract_receipt


def _serialize(value: Any) -> str:
    return json.dumps(value, default=str, ensure_ascii=False)


@tool(approval_mode="never_require")
def search_flights(
    origin: Annotated[str, Field(description="Origin code, for example SEA")],
    destination: Annotated[str, Field(description="Destination code, for example CDG")],
    cabin: Annotated[
        str | None, Field(description="economy, premium_economy, or business")
    ] = None,
    depart_after_hhmm: Annotated[
        str | None, Field(description="Optional HHMM lower bound, for example 0800")
    ] = None,
    refundable: Annotated[bool | None, Field(description="Require refundable inventory")] = None,
    preferred_only: Annotated[bool, Field(description="Restrict to preferred vendors")] = False,
) -> str:
    """Search deterministic flight inventory without fabricating routes."""
    return _serialize(
        search_tools.search_flights(
            origin,
            destination,
            cabin=cabin,
            depart_after_hhmm=depart_after_hhmm,
            refundable=refundable,
            preferred_only=preferred_only,
        )
    )


@tool(approval_mode="never_require")
def search_hotels(
    city: Annotated[str, Field(description="Fixture city code, for example PAR")],
    wheelchair: Annotated[bool, Field(description="Require wheelchair access")] = False,
    quiet: Annotated[bool, Field(description="Require a quiet room")] = False,
    late_checkin: Annotated[bool, Field(description="Require late check-in")] = False,
    max_nightly_total: Annotated[
        float | None, Field(description="Maximum nightly rate including taxes and fees")
    ] = None,
) -> str:
    """Search deterministic hotel inventory and accessibility attributes."""
    return _serialize(
        search_tools.search_hotels(
            city,
            wheelchair=wheelchair,
            quiet=quiet,
            late_checkin=late_checkin,
            max_nightly_total=max_nightly_total,
        )
    )


@tool(approval_mode="never_require")
def search_car_rentals(
    city: Annotated[str, Field(description="Fixture city code, for example YUL")],
    vehicle_class: Annotated[
        str | None, Field(description="economy, compact, midsize, suv, or luxury")
    ] = None,
    automatic: Annotated[bool | None, Field(description="Require automatic transmission")] = None,
    hand_controls: Annotated[bool, Field(description="Require hand controls")] = False,
) -> str:
    """Search deterministic car inventory and accessibility attributes."""
    return _serialize(
        search_tools.search_car_rentals(
            city,
            cls=vehicle_class,
            automatic=automatic,
            hand_controls=hand_controls,
        )
    )


@tool(approval_mode="never_require")
def check_travel_policy(
    employee_id: Annotated[str | None, Field(description="Employee id, for example EMP-001")] = None,
    flight_id: Annotated[str | None, Field(description="Flight fixture id")] = None,
    hotel_id: Annotated[str | None, Field(description="Hotel fixture id")] = None,
    car_id: Annotated[str | None, Field(description="Car fixture id")] = None,
    travelers: Annotated[int, Field(description="Number of travelers")] = 1,
    car_exception: Annotated[
        str | None, Field(description="winter_safety, mountain_route, or accessibility")
    ] = None,
    days_before_departure: Annotated[
        int | None, Field(description="Calendar days before departure")
    ] = None,
    disruption: Annotated[bool, Field(description="Whether a disruption exception applies")] = False,
    raw_instruction: Annotated[
        str | None, Field(description="Original instruction for bypass-attempt detection")
    ] = None,
) -> str:
    """Apply Caldova policy as a hard gate and return attributable CT rules."""
    return _serialize(
        _check_travel_policy(
            employee_id=employee_id,
            flight_id=flight_id,
            hotel_id=hotel_id,
            car_id=car_id,
            travelers=travelers,
            car_exception=car_exception,
            days_before_departure=days_before_departure,
            disruption=disruption,
            raw_instruction=raw_instruction,
        )
    )


@tool(approval_mode="never_require")
def extract_receipt(
    receipt_id: Annotated[str | None, Field(description="Receipt id, REC-001 through REC-004")] = None,
    image_path: Annotated[str | None, Field(description="Optional receipt image path")] = None,
) -> str:
    """Return structured receipt truth and line-level policy decisions."""
    return _serialize(_extract_receipt(receipt_id=receipt_id, image_path=image_path))


@tool(approval_mode="never_require")
def prepare_itinerary(
    employee_id: Annotated[str, Field(description="Employee id")],
    flight_ids: Annotated[list[str] | None, Field(description="Selected flight ids")] = None,
    hotel_ids: Annotated[list[str] | None, Field(description="Selected hotel ids")] = None,
    car_ids: Annotated[list[str] | None, Field(description="Selected car ids")] = None,
    receipts: Annotated[list[str] | None, Field(description="Attached receipt ids")] = None,
    notes: Annotated[str | None, Field(description="Evidence-based itinerary notes")] = None,
) -> str:
    """Assemble a proposed itinerary from fixture-backed selections."""
    return _serialize(
        _prepare_itinerary(
            employee_id=employee_id,
            flight_ids=flight_ids,
            hotel_ids=hotel_ids,
            car_ids=car_ids,
            receipts=receipts,
            notes=notes,
        )
    )


@tool(approval_mode="never_require")
def submit_booking(
    itinerary: Annotated[dict, Field(description="Prepared itinerary")],
    dry_run: Annotated[bool, Field(description="Keep true for this demo")] = True,
    compliance_summary: Annotated[
        dict | None, Field(description="Result from check_travel_policy")
    ] = None,
) -> str:
    """Perform a deterministic dry run, blocking policy violations."""
    return _serialize(
        _submit_booking(
            itinerary=itinerary,
            dry_run=dry_run,
            compliance_summary=compliance_summary,
        )
    )


ALL_TOOLS = [
    search_flights,
    search_hotels,
    search_car_rentals,
    check_travel_policy,
    extract_receipt,
    prepare_itinerary,
    submit_booking,
]
