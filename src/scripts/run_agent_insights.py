#!/usr/bin/env python3
"""Inspect or run Agent Insights for the deployed Contoso Travel agent."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import AgentInsightMonitorCreate, AgentInsightRunCreate
from azure.core.exceptions import HttpResponseError
from azure.identity import AzureCliCredential

ACTIVE_STATUSES = {"queued", "not_started", "in_progress", "running"}


def azd_value(name: str) -> str | None:
    result = subprocess.run(
        ["azd", "env", "get-value", name],
        check=False,
        capture_output=True,
        text=True,
    )
    value = result.stdout.strip()
    return value if result.returncode == 0 and value else None


def configured_value(argument: str | None, environment_name: str, azd_name: str) -> str | None:
    return argument or os.getenv(environment_name) or azd_value(azd_name)


def as_dict(value: Any) -> dict[str, Any]:
    if hasattr(value, "as_dict"):
        return value.as_dict()
    raise TypeError(f"Unsupported SDK value: {type(value).__name__}")


def print_runs(operations: Any, monitor_id: str) -> None:
    runs = list(operations.list_runs(monitor_id, limit=10, order="desc"))
    print(f"Recent runs: {len(runs)}")
    for run in runs:
        data = as_dict(run)
        error = data.get("error") or {}
        print(
            f"- {data.get('id')}: status={data.get('status')} "
            f"model={data.get('model_deployment_name')} "
            f"error={error.get('code') or 'none'}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect the existing Agent Insights monitor. Add --run to start one "
            "on-demand analysis without deleting or resetting monitor state."
        )
    )
    parser.add_argument("--run", action="store_true", help="Start one on-demand Insights run.")
    parser.add_argument("--lookback-hours", type=int, default=3)
    parser.add_argument("--project-endpoint")
    parser.add_argument("--agent-name", default="contoso-travel")
    parser.add_argument("--model-deployment")
    parser.add_argument("--save", type=Path, help="Save findings (without IDs) to this JSON file.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.lookback_hours < 1:
        raise SystemExit("--lookback-hours must be at least 1")

    endpoint = configured_value(
        args.project_endpoint,
        "FOUNDRY_PROJECT_ENDPOINT",
        "FOUNDRY_PROJECT_ENDPOINT",
    )
    model_deployment = configured_value(
        args.model_deployment,
        "FOUNDRY_MODEL_NAME",
        "AZURE_AI_INSIGHTS_JUDGE_DEPLOYMENT_NAME",
    ) or "insights-judge"
    if not endpoint:
        raise SystemExit(
            "Set FOUNDRY_PROJECT_ENDPOINT or select an azd environment that defines it."
        )

    with (
        AzureCliCredential() as credential,
        AIProjectClient(
            endpoint=endpoint,
            credential=credential,
            allow_preview=True,
        ) as project_client,
    ):
        operations = project_client.beta.agent_insight_monitors
        monitors = list(operations.list(agent_name=args.agent_name, limit=100))
        if len(monitors) > 1:
            raise SystemExit(
                f"Found {len(monitors)} monitors for {args.agent_name}; refusing to choose one."
            )
        if monitors:
            monitor = operations.get(monitors[0].id)
            print(f"Using monitor: {monitor.id}")
            print(f"Agent: {monitor.agent_name}")
            print(f"Judge deployment: {monitor.model_deployment_name}")
            if monitor.model_deployment_name != model_deployment:
                raise SystemExit(
                    f"Monitor uses {monitor.model_deployment_name!r}, expected "
                    f"{model_deployment!r}. Update it explicitly in Foundry before running."
                )
        elif not args.run:
            raise SystemExit(
                "No monitor exists. Re-run with --run to create a disabled monitor and start analysis."
            )
        else:
            monitor = operations.create(
                AgentInsightMonitorCreate(
                    agent_name=args.agent_name,
                    model_deployment_name=model_deployment,
                    enabled=False,
                )
            )
            print(f"Created disabled monitor: {monitor.id}")

        print_runs(operations, monitor.id)
        if not args.run:
            if args.save:
                save_findings(list(operations.list_insights(monitor.id, include_details=True)), args.save)
            return 0

        operation_id = str(uuid.uuid4())
        active = next(
            (run for run in operations.list_runs(monitor.id, limit=10, order="desc")
             if str(as_dict(run).get("status")).lower() in ACTIVE_STATUSES),
            None,
        )
        if active is not None:
            return wait_for_active_run(operations, monitor.id, as_dict(active)["id"], args.save)
        poller = operations.begin_create_run(
            monitor.id,
            AgentInsightRunCreate(lookback_hours=args.lookback_hours),
            operation_id=operation_id,
        )
        run_id = poller.details["run_id"]
        print(f"Started run: {run_id}")
        print(f"Operation ID: {operation_id}")
        try:
            result = poller.result()
        except HttpResponseError as error:
            failed_run = operations.get_run(monitor.id, run_id)
            print("Run failed:")
            print(json.dumps(as_dict(failed_run), indent=2, default=str))
            print(f"Request ID: {getattr(error, 'request_id', None) or 'unavailable'}")
            return 1

        completed_run = operations.get_run(monitor.id, run_id)
        print(f"Run status: {completed_run.status}")
        print(f"Traces in window: {result.traces_in_window}")
        print(f"Traces analyzed: {result.traces_analyzed}")
        print(f"Insights created: {result.insights_created}")
        print(f"Insights updated: {result.insights_updated}")
        print(f"Insights reopened: {result.insights_reopened}")
        print(f"Total tokens: {result.token_usage.total_tokens}")
        insights = list(operations.list_insights(monitor.id, include_details=True))
        print(f"Insights available: {len(insights)}")
        for insight in insights:
            print(
                f"- {insight.id}: severity={insight.severity} "
                f"status={insight.status} traces={insight.trace_count} title={insight.title}"
            )
        if args.save:
            save_findings(insights, args.save)
        return 0


def wait_for_active_run(operations: Any, monitor_id: str, run_id: str, save: Path | None) -> int:
    """Only one run can be active per monitor, so wait for it rather than starting another."""
    print(f"A run is already in progress ({run_id}); waiting for it instead of starting another.")
    while True:
        data = as_dict(operations.get_run(monitor_id, run_id))
        status = str(data.get("status")).lower()
        if status not in ACTIVE_STATUSES:
            break
        time.sleep(20)
    print(f"Run status: {status}")
    if status != "succeeded":
        print(json.dumps(data, indent=2, default=str))
        return 1
    insights = list(operations.list_insights(monitor_id, include_details=True))
    print(f"Insights available: {len(insights)}")
    for insight in insights:
        print(
            f"- {insight.id}: severity={insight.severity} "
            f"status={insight.status} traces={insight.trace_count} title={insight.title}"
        )
    if save:
        save_findings(insights, save)
    return 0


def without_ids(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: without_ids(item)
            for key, item in value.items()
            if key != "id" and not key.endswith(("_id", "_ids")) and key not in {"linked_traces", "evidence", "created_at", "updated_at"}
        }
    if isinstance(value, list):
        return [without_ids(item) for item in value]
    return value


def save_findings(insights: list[Any], path: Path) -> None:
    """Keep the parts of each finding that describe the problem, without IDs."""
    findings = [without_ids(as_dict(insight)) for insight in insights]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(findings, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"Saved {len(findings)} finding(s) for the scorecard draft: {path}")


if __name__ == "__main__":
    sys.exit(main())