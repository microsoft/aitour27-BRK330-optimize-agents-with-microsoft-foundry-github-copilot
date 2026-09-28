#!/usr/bin/env python3
"""Inspect or run Agent Insights for the deployed Contoso Travel agent."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import uuid
from typing import Any

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import AgentInsightMonitorCreate, AgentInsightRunCreate
from azure.core.exceptions import HttpResponseError
from azure.identity import AzureCliCredential


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
            return 0

        operation_id = str(uuid.uuid4())
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
        return 0


if __name__ == "__main__":
    sys.exit(main())