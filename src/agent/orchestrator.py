"""Session-2 routing: task decomposition + Model Router.

The baseline (Session 1) sends every prompt to a single frontier model
(`gpt-5`) that self-decomposes at inference time and executes every tool
call at frontier cost.

This module introduces the routed variant that Demo 2 hill-climbs to:

1. **Planner (gpt-5)** — a lightweight, no-tools JSON call that reads the
   user's compound request and returns an explicit task graph. Task
   graphs are strict JSON (`{tasks: [{id, kind, goal, needs, produces}]}`)
   so we can inspect decomposition in the trace before any tool call.
2. **Workers (model-router)** — the Agent Framework Agent's chat client
   is swapped from `gpt-5` to `model-router`. Every subsequent LLM turn
   (tool-selection reasoning, tool-argument construction, per-task
   response) goes through Model Router, which picks the underlying model
   per call. That gives the trace per-task route evidence rather than a
   single frontier-cost bill for the whole request.
3. **Composer** — the final assistant message stays on `model-router`
   too; empirical demos show Router escalates the final composition to a
   frontier model when policy citations are dense, and downshifts when
   the task graph reports "brief reply" cases.

The routed variant is behind the `CONTOSO_ROUTED` env flag so baseline
vs routed can be compared without a code fork.
"""
from __future__ import annotations
import json, logging, os
from typing import Any

try:
    from telemetry import span, set_span_attr
except ImportError:  # local dev via repo root
    from src.agent.telemetry import span, set_span_attr

log = logging.getLogger("contoso.orchestrator")


PLANNER_SYSTEM = """You are the task planner for the Contoso Travel Concierge.
Decompose the user's compound travel request into a strict JSON task graph.
Do not call any tools. Do not include prose. Return ONLY the JSON.

Schema:
{
  "tasks": [
    {
      "id":        "<short slug e.g. flight, hotel, car, receipt, policy, itinerary>",
      "kind":      "search_flight" | "search_hotel" | "search_car" | "extract_receipt" | "check_policy" | "prepare_itinerary" | "compose",
      "goal":      "<one sentence>",
      "needs":     ["<other task ids this depends on>"],
      "produces":  "<what the task returns downstream>"
    }
  ]
}

Rules:
- Every distinct job the user asked for gets its own task. Do NOT collapse
  a hotel search + a car rental search into one task.
- Every booking-relevant task must have at least one downstream `check_policy`
  task that depends on it — policy is a hard gate.
- The final task is always `compose` and depends on every other task id.
- Never invent tasks the user did not ask for.
"""


def plan_tasks(project_client, planner_deployment: str, user_input: str,
               attachments: list[str] | None = None,
               employee_id: str = "EMP-001") -> dict[str, Any]:
    """Call the planner (default: gpt-5) and return the task graph."""
    from openai.types.chat import ChatCompletionMessageParam  # noqa: F401
    with span("agent.plan_tasks", planner_deployment=planner_deployment,
              employee_id=employee_id):
        user_ctx = f"Traveler: {employee_id}. User request: {user_input}"
        if attachments:
            user_ctx += f" Attachments: {', '.join(attachments)}."
        resp = project_client.chat.completions.create(
            model=planner_deployment,
            messages=[
                {"role": "system", "content": PLANNER_SYSTEM},
                {"role": "user",   "content": user_ctx},
            ],
            temperature=0.0,
            response_format={"type": "json_object"},
            max_tokens=800,
        )
        raw = resp.choices[0].message.content or "{}"
        try:
            graph = json.loads(raw)
        except Exception as e:
            log.warning("planner returned invalid JSON: %s", e)
            graph = {"tasks": []}
        tasks = graph.get("tasks", []) or []
        set_span_attr("agent.task_count", len(tasks))
        set_span_attr("agent.task_ids", ",".join(t.get("id", "?") for t in tasks))
        return graph


def format_task_graph_for_agent(graph: dict[str, Any]) -> str:
    """Render the task graph into a compact block for the agent's system message
    so the router-based worker knows which subtasks to execute and in what order.
    """
    lines = ["Task plan (execute each task in dependency order):"]
    for t in graph.get("tasks", []) or []:
        deps = t.get("needs") or []
        dep_str = f" (needs: {', '.join(deps)})" if deps else ""
        lines.append(f"- {t.get('id')}: {t.get('goal')}{dep_str}")
    return "\n".join(lines)
