"""Turn a Responses payload into tool evidence and a plain-language outcome.

Shared by the Travel Concierge Portal and the command-line question runner so
both describe the same response the same way.
"""
from __future__ import annotations

import json
from typing import Any

OUTCOMES: dict[str, tuple[str, str]] = {
    "booked": ("passed", "Booked (dry run) — choices meet Caldova policy"),
    "checked": ("passed", "Checked — choices meet Caldova policy, not booked yet"),
    "reimbursable": ("passed", "Reimbursable — receipt meets Caldova policy"),
    "partly_reimbursable": ("warning", "Partly reimbursable — some receipt lines are excluded"),
    "blocked": ("blocked", "Not approved — blocked by Caldova policy"),
    "not_booked": ("warning", "Not booked — the booking step did not go through"),
    "partial": ("warning", "Partly done — nothing matched some of the requirements"),
    "error": ("warning", "Not confirmed — a check returned an error"),
    "unconfirmed": ("warning", "Not confirmed — no policy or receipt check ran"),
}


def _parse(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value or "{}")
        except json.JSONDecodeError:
            return {"raw": value}
    return value


def _outcome(
    *,
    errors: list[str],
    blocked: bool,
    booking: dict[str, Any] | None,
    empty_searches: list[str],
    policy_checked: bool,
    receipt_checked: bool,
    receipt_approved: bool,
    receipt_flagged: bool,
) -> str:
    if errors:
        return "error"
    if blocked:
        return "blocked"
    booking_status = (booking or {}).get("status")
    if booking_status == "dry_run_success":
        return "booked"
    if booking_status:
        return "not_booked"
    if empty_searches:
        return "partial"
    if receipt_checked and not policy_checked:
        if receipt_flagged:
            return "partly_reimbursable"
        return "reimbursable" if receipt_approved else "unconfirmed"
    if policy_checked:
        return "checked"
    return "unconfirmed"


def summarize_response(payload: dict[str, Any]) -> dict[str, Any]:
    """Extract assistant text, tool evidence, citations, usage, and the outcome."""
    text_parts: list[str] = []
    tool_timeline: list[dict[str, Any]] = []
    cited_rules: set[str] = set()
    blocked_decisions: list[dict[str, Any]] = []
    blocked = False
    policy_checked = False
    policy_errors: list[str] = []
    final_compliance: dict[str, Any] | None = None
    receipt_checked = False
    receipt_approved = True
    receipt_flagged_lines: list[dict[str, Any]] = []
    receipt_cited_rules: set[str] = set()
    empty_searches: list[str] = []
    booking: dict[str, Any] | None = None

    for item in payload.get("output", []) or []:
        item_type = item.get("type")
        if item_type == "message":
            for content in item.get("content", []) or []:
                if content.get("type") in {"output_text", "text"}:
                    text_parts.append(content.get("text", ""))
        elif item_type == "function_call":
            arguments = _parse(item.get("arguments", {}))
            if item.get("name") == "submit_booking" and isinstance(arguments, dict):
                compliance = arguments.get("compliance_summary")
                if isinstance(compliance, dict):
                    final_compliance = compliance
            tool_timeline.append(
                {"call_id": item.get("call_id"), "tool": item.get("name", "unknown"), "arguments": arguments, "result": None}
            )
        elif item_type == "function_call_output":
            output = _parse(item.get("output", {}))
            call_id = item.get("call_id")
            target = next(
                (step for step in reversed(tool_timeline) if step["call_id"] == call_id),
                tool_timeline[-1] if tool_timeline else None,
            )
            if target is not None:
                target["result"] = output
            tool = target["tool"] if target is not None else ""
            if tool.startswith("search_") and output == []:
                empty_searches.append(tool)
            if not isinstance(output, dict):
                continue
            if tool == "submit_booking":
                booking = output
            cited_rules.update(output.get("cited_rule_ids", []) or [])
            blocked = blocked or bool(output.get("hard_gate_blocked"))
            blocked_decisions.extend(output.get("blocked_decisions", []) or [])
            if tool == "check_travel_policy":
                policy_checked = True
                policy_errors.extend(output.get("errors", []) or [])
            if tool == "extract_receipt":
                receipt_checked = True
                if output.get("error"):
                    receipt_approved = False
                    policy_errors.append(str(output["error"]))
                policy_notes = output.get("policy_notes") or {}
                receipt_approved = receipt_approved and bool(policy_notes.get("reimbursable_category"))
                receipt_flagged_lines.extend(output.get("policy_flagged_lines", []) or [])
                for key in ("matched_rule", "conversion_rule"):
                    if policy_notes.get(key):
                        receipt_cited_rules.add(str(policy_notes[key]))

    if final_compliance is not None:
        blocked = bool(final_compliance.get("hard_gate_blocked"))
        blocked_decisions = list(final_compliance.get("blocked_decisions", []) or [])
        cited_rules = set(final_compliance.get("cited_rule_ids", []) or [])
        policy_errors = list(final_compliance.get("errors", []) or [])
        policy_checked = True

    cited_rules.update(receipt_cited_rules)
    cited_rules.update(str(line["rule_id"]) for line in receipt_flagged_lines if line.get("rule_id"))
    blocked_decisions = list(
        {
            (decision.get("rule_id"), decision.get("reason")): decision
            for decision in blocked_decisions
        }.values()
    )

    outcome = _outcome(
        errors=policy_errors,
        blocked=blocked,
        booking=booking,
        empty_searches=empty_searches,
        policy_checked=policy_checked,
        receipt_checked=receipt_checked,
        receipt_approved=receipt_approved,
        receipt_flagged=bool(receipt_flagged_lines),
    )
    tone, label = OUTCOMES[outcome]
    reimbursement = receipt_checked and not policy_checked
    if outcome == "blocked" and reimbursement:
        label = "Not reimbursable — blocked by Caldova policy"

    return {
        "assistant": "\n".join(text_parts),
        "tool_timeline": tool_timeline,
        "outcome": {"code": outcome, "tone": tone, "label": label},
        "policy": {
            "hard_gate_blocked": blocked,
            "cited_rule_ids": sorted(cited_rules),
            "blocked_decisions": blocked_decisions,
            "excluded_receipt_lines": receipt_flagged_lines,
            "empty_searches": empty_searches,
            "booking_status": (booking or {}).get("status"),
            "booking_reason": (booking or {}).get("reason"),
            "checked": policy_checked or receipt_checked,
            "approved": outcome in {"booked", "checked", "reimbursable"},
            "decision_type": "travel" if policy_checked else "reimbursement" if receipt_checked else "unconfirmed",
            "errors": policy_errors,
            "evidence_gap": not blocked and not cited_rules,
        },
        "usage": payload.get("usage") or {},
        "response_id": payload.get("id"),
        "model": payload.get("model"),
    }
