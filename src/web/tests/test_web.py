from __future__ import annotations

import sys
from pathlib import Path

WEB_ROOT = Path(__file__).resolve().parents[1]
if str(WEB_ROOT) not in sys.path:
    sys.path.insert(0, str(WEB_ROOT))

from main import _active_agent_details, summarize_response


def test_summarize_response_correlates_tool_output() -> None:
    payload = {
        "id": "resp-123",
        "model": "gpt-5.4",
        "output": [
            {
                "type": "function_call",
                "call_id": "call-1",
                "name": "check_travel_policy",
                "arguments": '{"flight_id":"FL-006"}',
            },
            {
                "type": "function_call_output",
                "call_id": "call-1",
                "output": '{"hard_gate_blocked":true,"cited_rule_ids":["CT-11"],"blocked_decisions":[{"rule_id":"CT-11","reason":"Bypass attempt"}]}',
            },
            {
                "type": "message",
                "content": [{"type": "output_text", "text": "I cannot bypass policy."}],
            },
        ],
        "usage": {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15},
    }
    result = summarize_response(payload)
    assert result["assistant"] == "I cannot bypass policy."
    assert result["tool_timeline"][0]["result"]["hard_gate_blocked"] is True
    assert result["policy"]["hard_gate_blocked"] is True
    assert result["policy"]["checked"] is True
    assert result["policy"]["approved"] is False
    assert result["policy"]["decision_type"] == "travel"
    assert result["policy"]["cited_rule_ids"] == ["CT-11"]
    assert result["policy"]["evidence_gap"] is False


def test_summarize_response_marks_policy_evidence_gap() -> None:
    result = summarize_response(
        {
            "id": "resp-456",
            "output": [
                {
                    "type": "message",
                    "content": [{"type": "output_text", "text": "This is compliant."}],
                }
            ],
        }
    )
    assert result["policy"]["hard_gate_blocked"] is False
    assert result["policy"]["checked"] is False
    assert result["policy"]["approved"] is False
    assert result["policy"]["decision_type"] == "unconfirmed"
    assert result["policy"]["evidence_gap"] is True


def test_receipt_evidence_confirms_reimbursement() -> None:
    result = summarize_response(
        {
            "output": [
                {
                    "type": "function_call",
                    "call_id": "call-receipt",
                    "name": "extract_receipt",
                    "arguments": '{"receipt_id":"REC-002"}',
                },
                {
                    "type": "function_call_output",
                    "call_id": "call-receipt",
                    "output": '{"receipt_id":"REC-002","policy_notes":{"reimbursable_category":true,"matched_rule":"CT-20","conversion_rule":"CT-22"},"policy_flagged_lines":[]}',
                },
            ]
        }
    )

    assert result["policy"]["checked"] is True
    assert result["policy"]["approved"] is True
    assert result["policy"]["decision_type"] == "reimbursement"
    assert result["policy"]["cited_rule_ids"] == ["CT-20", "CT-22"]
    assert result["policy"]["evidence_gap"] is False


def test_summarize_response_marks_successful_policy_check_approved() -> None:
    result = summarize_response(
        {
            "output": [
                {
                    "type": "function_call",
                    "call_id": "call-policy",
                    "name": "check_travel_policy",
                    "arguments": '{"employee_id":"EMP-001","flight_id":"FL-001"}',
                },
                {
                    "type": "function_call_output",
                    "call_id": "call-policy",
                    "output": '{"hard_gate_blocked":false,"blocked_decisions":[],"cited_rule_ids":[],"errors":[]}',
                },
            ]
        }
    )

    assert result["policy"]["checked"] is True
    assert result["policy"]["approved"] is True
    assert result["policy"]["evidence_gap"] is True


def test_final_itinerary_approval_overrides_rejected_candidate() -> None:
    result = summarize_response(
        {
            "output": [
                {
                    "type": "function_call",
                    "call_id": "call-candidate",
                    "name": "check_travel_policy",
                    "arguments": '{"hotel_id":"HT-004"}',
                },
                {
                    "type": "function_call_output",
                    "call_id": "call-candidate",
                    "output": '{"hard_gate_blocked":true,"blocked_decisions":[{"rule_id":"CT-03","reason":"Over cap"}],"cited_rule_ids":["CT-03"],"errors":[]}',
                },
                {
                    "type": "function_call",
                    "call_id": "call-submit",
                    "name": "submit_booking",
                    "arguments": '{"itinerary":{"hotel_ids":["HT-001"]},"dry_run":true,"compliance_summary":{"hard_gate_blocked":false,"blocked_decisions":[],"cited_rule_ids":["CT-20"],"errors":[]}}',
                },
                {
                    "type": "function_call_output",
                    "call_id": "call-submit",
                    "output": '{"status":"dry_run_success"}',
                },
            ]
        }
    )

    assert result["policy"]["hard_gate_blocked"] is False
    assert result["policy"]["approved"] is True
    assert result["policy"]["cited_rule_ids"] == ["CT-20"]


def _policy_check(call_id: str, output: str) -> list[dict]:
    return [
        {"type": "function_call", "call_id": call_id, "name": "check_travel_policy", "arguments": "{}"},
        {"type": "function_call_output", "call_id": call_id, "output": output},
    ]


def test_booking_without_policy_evidence_is_not_booked() -> None:
    passed = '{"hard_gate_blocked":false,"blocked_decisions":[],"cited_rule_ids":[],"errors":[]}'
    result = summarize_response(
        {
            "output": _policy_check("p", passed)
            + [
                {"type": "function_call", "call_id": "b", "name": "submit_booking", "arguments": '{"itinerary":{},"dry_run":true}'},
                {"type": "function_call_output", "call_id": "b", "output": '{"status":"blocked","reason":"Explicit policy compliance evidence is required before a booking dry-run."}'},
            ]
        }
    )

    assert result["outcome"]["code"] == "not_booked"
    assert result["policy"]["approved"] is False
    assert result["policy"]["booking_status"] == "blocked"


def test_empty_search_marks_request_partly_done() -> None:
    passed = '{"hard_gate_blocked":false,"blocked_decisions":[],"cited_rule_ids":[],"errors":[]}'
    result = summarize_response(
        {
            "output": [
                {"type": "function_call", "call_id": "s", "name": "search_flights", "arguments": '{"origin":"SEA","destination":"YUL","depart_after_hhmm":"0800"}'},
                {"type": "function_call_output", "call_id": "s", "output": "[]"},
            ]
            + _policy_check("p", passed)
        }
    )

    assert result["outcome"]["code"] == "partial"
    assert result["policy"]["empty_searches"] == ["search_flights"]


def test_receipt_with_excluded_lines_is_partly_reimbursable() -> None:
    result = summarize_response(
        {
            "output": [
                {"type": "function_call", "call_id": "r", "name": "extract_receipt", "arguments": '{"receipt_id":"REC-003"}'},
                {"type": "function_call_output", "call_id": "r", "output": '{"receipt_id":"REC-003","policy_flagged_lines":[{"line":"Minibar","rule_id":"CT-20","reason":"Minibar excluded"}]}'},
            ]
        }
    )

    assert result["outcome"]["code"] == "partly_reimbursable"
    assert result["policy"]["hard_gate_blocked"] is False
    assert result["policy"]["cited_rule_ids"] == ["CT-20"]


def test_repeated_policy_decisions_are_deduplicated() -> None:
    result = summarize_response(
        {
            "output": [
                {
                    "type": "function_call",
                    "call_id": f"call-{index}",
                    "name": "check_travel_policy",
                    "arguments": '{"days_before_departure":0}',
                }
                for index in range(4)
            ]
            + [
                {
                    "type": "function_call_output",
                    "call_id": f"call-{index}",
                    "output": '{"hard_gate_blocked":true,"blocked_decisions":[{"rule_id":"CT-02","reason":"Booking only 0 day(s) before departure"}],"cited_rule_ids":["CT-02"],"errors":[]}',
                }
                for index in range(4)
            ]
        }
    )

    assert result["policy"]["hard_gate_blocked"] is True
    assert result["policy"]["blocked_decisions"] == [
        {
            "rule_id": "CT-02",
            "reason": "Booking only 0 day(s) before departure",
        }
    ]


def test_active_agent_details_resolves_latest_selector(monkeypatch) -> None:
    class Agents:
        def get(self, *, agent_name):
            assert agent_name == "contoso-travel"
            return type(
                "Details",
                (),
                {
                    "state": "enabled",
                    "versions": type(
                        "Versions", (), {"latest": type("Latest", (), {"version": "2"})()}
                    )(),
                    "agent_endpoint": type(
                        "Endpoint",
                        (),
                        {
                            "version_selector": type(
                                "Selector",
                                (),
                                {
                                    "version_selection_rules": [
                                        type(
                                            "Rule",
                                            (),
                                            {
                                                "traffic_percentage": 100,
                                                "agent_version": "@latest",
                                            },
                                        )()
                                    ]
                                },
                            )()
                        },
                    )(),
                },
            )()

        def get_version(self, *, agent_name, agent_version):
            assert agent_name == "contoso-travel"
            assert agent_version == "2"
            return type(
                "Version",
                (),
                {
                    "status": "active",
                    "metadata": {},
                    "definition": type("Definition", (), {"environment_variables": {}})(),
                },
            )()

    project_client = type("ProjectClient", (), {"agents": Agents()})()
    monkeypatch.setattr("main._clients", lambda: (project_client, object()))

    assert _active_agent_details()["active_version"] == "2"
