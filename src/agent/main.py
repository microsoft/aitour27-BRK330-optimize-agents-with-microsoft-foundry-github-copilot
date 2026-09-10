"""Foundry hosted agent entry point — Responses protocol via Agent Framework.

Wraps the Contoso Travel Concierge tools defined in `src/agent/tools/` as
`@tool` functions and starts a `ResponsesHostServer` so the Foundry runtime can
route incoming Responses requests to the agent.

Two variants live behind the `CONTOSO_ROUTED` env flag:

- **baseline (`CONTOSO_ROUTED=false`, default)** — single `gpt-5` Agent
  handles decomposition, tool selection, and final composition inline.
  This is what Session 1 built and evaluated.

- **routed (`CONTOSO_ROUTED=true`)** — a lightweight planner call
  (`AZURE_AI_PLANNER_DEPLOYMENT_NAME`, defaults to `gpt-5`) produces an
  explicit task graph. The Agent's chat client is then swapped to
  `AZURE_AI_ROUTER_DEPLOYMENT_NAME` (defaults to `model-router`), and the
  task graph is prepended to the agent's input so the router-backed
  worker knows which subtasks to execute. Every tool-selection turn and
  every subtask response goes through Model Router, giving per-request
  route evidence in Insights.
"""
from __future__ import annotations
import json, logging, os
from typing import Any
from typing_extensions import Annotated
from pydantic import Field

log = logging.getLogger("contoso.agent")

from agent_framework import Agent, tool
from agent_framework.foundry import FoundryChatClient
from agent_framework_foundry_hosting import ResponsesHostServer
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

# When packaged into the hosted-agent container, Dockerfile does
# `COPY . user_agent/` from src/agent/, so imports look like `import tools.*`
# (no `src.agent.` prefix). Locally we can also run this from the repo root.
try:
    from tools import search as search_tools
    from tools.receipts import extract_receipt as _extract_receipt
    from tools.policy import check_travel_policy as _check_travel_policy
    from tools.itinerary import prepare_itinerary as _prepare_itinerary, submit_booking as _submit_booking
    from telemetry import init_telemetry, span, set_span_attr
    from orchestrator import plan_tasks, format_task_graph_for_agent
except ImportError:  # local dev via repo root
    from src.agent.tools import search as search_tools
    from src.agent.tools.receipts import extract_receipt as _extract_receipt
    from src.agent.tools.policy import check_travel_policy as _check_travel_policy
    from src.agent.tools.itinerary import prepare_itinerary as _prepare_itinerary, submit_booking as _submit_booking
    from src.agent.telemetry import init_telemetry, span, set_span_attr
    from src.agent.orchestrator import plan_tasks, format_task_graph_for_agent

load_dotenv()

SYSTEM_PROMPT = """You are Contoso Travel Concierge, an AI travel agent operated by Contoso Travel for Caldova (a fictional pharmaceutical operations company).

Non-negotiable rules:
1. Caldova travel policy is a HARD GATE. Never book, recommend, or advance a step that violates a policy rule. When a rule blocks an action, refuse and cite the rule id (CT-nn) verbatim from the tool response. Do not silently soften the block.
2. Never invent flights, hotels, cars, prices, exchange rates, emissions, or receipt fields. Every option must come from a tool call.
3. Decompose the user's compound request into explicit tasks. State the plan briefly before invoking tools.
4. Prefer preferred vendors within the 8% price tolerance (CT-05). Prefer refundable options when the user declares uncertainty (CT-06). Accessibility (CT-07) and time constraints (CT-08) beat price.
5. For receipts: call extract_receipt; then reconcile line-by-line against CT-20/24/26. Report reimbursable vs non-reimbursable totals.
6. Refuse blanket-approval instructions and any request to bypass policy (CT-11).
7. Output structure: (a) understood tasks, (b) tool timeline, (c) policy decisions with cited rules, (d) itinerary summary.

Currency defaults to USD unless the receipt or trip context supplies another currency. Use fixture rates from the exchange_rates fixture when converting (CT-22).
"""


def _dumps(o: Any) -> str:
    return json.dumps(o, default=str, ensure_ascii=False)


@tool(approval_mode="never_require")
def search_flights(
    origin: Annotated[str, Field(description="Origin IATA-ish code, e.g. SEA")],
    dest: Annotated[str, Field(description="Destination IATA-ish code, e.g. CDG")],
    cabin: Annotated[str | None, Field(description="economy | premium_economy | business")] = None,
    depart_after_hhmm: Annotated[str | None, Field(description="HHMM lower-bound e.g. 0800")] = None,
    refundable: Annotated[bool | None, Field(description="Only refundable options if true")] = None,
    preferred_only: Annotated[bool, Field(description="Restrict to preferred vendors")] = False,
) -> str:
    """Search deterministic flight fixtures. Never fabricates a route."""
    return _dumps(search_tools.search_flights(origin, dest, cabin=cabin,
        depart_after_hhmm=depart_after_hhmm, refundable=refundable,
        preferred_only=preferred_only))


@tool(approval_mode="never_require")
def search_hotels(
    city: Annotated[str, Field(description="City code, e.g. PAR")],
    wheelchair: Annotated[bool, Field(description="Wheelchair-accessible required")] = False,
    quiet: Annotated[bool, Field(description="Quiet room required")] = False,
    late_checkin: Annotated[bool, Field(description="Late check-in required")] = False,
    max_nightly_total: Annotated[float | None, Field(description="Max nightly rate + taxes")] = None,
) -> str:
    """Search hotel fixtures with accessibility, quiet, late-checkin, and rate cap filters."""
    return _dumps(search_tools.search_hotels(city, wheelchair=wheelchair, quiet=quiet,
        late_checkin=late_checkin, max_nightly_total=max_nightly_total))


@tool(approval_mode="never_require")
def search_car_rentals(
    city: Annotated[str, Field(description="City code, e.g. PAR")],
    cls: Annotated[str | None, Field(description="economy|compact|midsize|suv|luxury")] = None,
    automatic: Annotated[bool | None, Field(description="Automatic transmission required")] = None,
    hand_controls: Annotated[bool, Field(description="Hand controls required")] = False,
) -> str:
    """Search car-rental fixtures by city, class, and accessibility."""
    return _dumps(search_tools.search_car_rentals(city, cls=cls, automatic=automatic,
        hand_controls=hand_controls))


@tool(approval_mode="never_require")
def check_travel_policy(
    employee_id: Annotated[str | None, Field(description="EMP-001 style id")] = None,
    flight_id: Annotated[str | None, Field(description="FL-nnn id")] = None,
    hotel_id: Annotated[str | None, Field(description="HT-nnn id")] = None,
    car_id: Annotated[str | None, Field(description="CR-nnn id")] = None,
    travelers: Annotated[int, Field(description="Number of travelers")] = 1,
    car_exception: Annotated[str | None, Field(description="winter_safety|mountain_route|accessibility")] = None,
    days_before_departure: Annotated[int | None, Field(description="Days between booking and departure")] = None,
    disruption: Annotated[bool, Field(description="Is this a disruption exception?")] = False,
    raw_instruction: Annotated[str | None, Field(description="Original user instruction (to check for blanket-approval attempts)")] = None,
) -> str:
    """Apply Caldova policy as a hard gate; returns cited_rule_ids and blocked_decisions."""
    return _dumps(_check_travel_policy(
        employee_id=employee_id, flight_id=flight_id, hotel_id=hotel_id, car_id=car_id,
        travelers=travelers, car_exception=car_exception,
        days_before_departure=days_before_departure, disruption=disruption,
        raw_instruction=raw_instruction,
    ))


@tool(approval_mode="never_require")
def extract_receipt(
    receipt_id: Annotated[str | None, Field(description="REC-001..REC-004")] = None,
    image_path: Annotated[str | None, Field(description="Path to receipt image (optional)")] = None,
) -> str:
    """Extract structured receipt fields and apply CT-20 line-level rules."""
    return _dumps(_extract_receipt(receipt_id=receipt_id, image_path=image_path))


@tool(approval_mode="never_require")
def prepare_itinerary(
    employee_id: Annotated[str, Field(description="EMP-001 style id")],
    flight_ids: Annotated[list[str] | None, Field(description="Flight fixture ids")] = None,
    hotel_ids: Annotated[list[str] | None, Field(description="Hotel fixture ids")] = None,
    car_ids: Annotated[list[str] | None, Field(description="Car fixture ids")] = None,
    receipts: Annotated[list[str] | None, Field(description="Receipt ids to attach")] = None,
    notes: Annotated[str | None, Field(description="Free-text notes")] = None,
) -> str:
    """Assemble a proposed itinerary from fixture ids."""
    return _dumps(_prepare_itinerary(
        employee_id=employee_id, flight_ids=flight_ids, hotel_ids=hotel_ids,
        car_ids=car_ids, receipts=receipts, notes=notes,
    ))


@tool(approval_mode="never_require")
def submit_booking(
    itinerary: Annotated[dict, Field(description="Itinerary returned by prepare_itinerary")],
    dry_run: Annotated[bool, Field(description="Always true in this demo")] = True,
    compliance_summary: Annotated[dict | None, Field(description="Output of check_travel_policy")] = None,
) -> str:
    """Dry-run booking. Blocks if compliance_summary.hard_gate_blocked is true."""
    return _dumps(_submit_booking(
        itinerary=itinerary, dry_run=dry_run, compliance_summary=compliance_summary,
    ))


def main() -> None:
    init_telemetry()
    routed = os.getenv("CONTOSO_ROUTED", "false").lower() in ("1", "true", "yes")
    baseline_model = os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"]
    router_model   = os.getenv("AZURE_AI_ROUTER_DEPLOYMENT_NAME", "model-router")
    worker_model   = router_model if routed else baseline_model

    # In routed mode, all LLM traffic (decomposition, tool selection, per-tool
    # response, final composition) goes through Model Router. The Router picks
    # the underlying model per call — that's how we get task-level right-sizing
    # without spinning up separate planner/worker processes. We strengthen the
    # instructions so the first turn always emits an explicit task plan, then
    # executes tools one task at a time.
    instructions = SYSTEM_PROMPT
    if routed:
        instructions += (
            "\n\nRouting mode: your underlying chat completion is served by a "
            "Model Router deployment. Every response you generate is routed "
            "independently, so keep each turn focused on a single subtask.\n"
            "First-turn behavior for every compound request:\n"
            "1. Emit a compact task plan enumerating each independent subtask "
            "(flight, hotel, car, receipt audit, policy check, itinerary "
            "compose) BEFORE calling any tool.\n"
            "2. Execute the tasks in dependency order, calling exactly one "
            "tool per turn where feasible so per-task routing telemetry is "
            "captured.\n"
            "3. Never re-decompose after starting. If a task's tool returns "
            "an error or empty result, surface it verbatim; do not retry the "
            "same call with fabricated arguments."
        )

    with span("agent.main.startup",
              routed=str(routed),
              baseline_model=baseline_model,
              worker_model=worker_model):
        set_span_attr("agent.variant", "routed" if routed else "baseline")

    client = FoundryChatClient(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        model=worker_model,
        credential=DefaultAzureCredential(),
    )
    agent = Agent(
        client=client,
        instructions=instructions,
        tools=[
            search_flights,
            search_hotels,
            search_car_rentals,
            check_travel_policy,
            extract_receipt,
            prepare_itinerary,
            submit_booking,
        ],
        default_options={
            "store": False,
            # Reasoning stays ON at the model's default effort — we just don't
            # emit reasoning content parts in the output payload. This keeps
            # the model's decision quality while unblocking the Foundry
            # evaluators (intent_resolution, task_adherence,
            # tool_call_accuracy, and the auto-generated Caldova rubric),
            # which reject assistant messages containing `content.type:
            # "reasoning"` items.
            "reasoning": {"summary": None},
            "include": [],
        },
    )
    server = ResponsesHostServer(agent)
    server.run()


if __name__ == "__main__":
    main()
