#!/usr/bin/env python3
"""Inspect or reroute the contoso-travel endpoint to a retained version.

Examples:
    python infra/switch-agent-version.py --version 3
    python infra/switch-agent-version.py --version 3 --apply

Without ``--apply`` the command is read-only. Switching is a control-plane
endpoint update; it does not rebuild an image or create a version. Start a new
conversation after switching. Use the reported previous version to restore.
"""
from __future__ import annotations

import argparse
import json
import os

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    AgentEndpointConfig,
    FixedRatioVersionSelectionRule,
    VersionSelector,
)
from azure.identity import DefaultAzureCredential


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--version",
        required=True,
        help="Retained active version to receive all endpoint traffic.",
    )
    parser.add_argument("--agent", default="contoso-travel", help="Hosted Agent name.")
    parser.add_argument(
        "--project-endpoint",
        default=os.getenv("FOUNDRY_PROJECT_ENDPOINT") or os.getenv("AZURE_AI_PROJECT_ENDPOINT"),
        help="Foundry project endpoint; defaults to the standard environment variables.",
    )
    parser.add_argument("--apply", action="store_true", help="Apply the endpoint update. Default is read-only.")
    return parser.parse_args()


def active_version(details) -> str:
    endpoint = details.agent_endpoint
    if endpoint and endpoint.version_selector:
        for rule in endpoint.version_selector.version_selection_rules:
            if getattr(rule, "traffic_percentage", 0) == 100:
                return rule.agent_version
    return details.versions.latest.version


def main() -> None:
    args = parse_args()
    if not args.project_endpoint:
        raise SystemExit("Set FOUNDRY_PROJECT_ENDPOINT or pass --project-endpoint.")
    with DefaultAzureCredential() as credential, AIProjectClient(
        endpoint=args.project_endpoint, credential=credential, allow_preview=True
    ) as project:
        details = project.agents.get(agent_name=args.agent)
        previous = active_version(details)
        target = project.agents.get_version(agent_name=args.agent, agent_version=args.version)
        if str(target.status).lower() != "active":
            raise SystemExit(f"Target version {args.version} is not active/ready: {target.status}")
        report = {
            "agent": args.agent,
            "previous_version": previous,
            "target_version": args.version,
            "target_status": str(target.status),
            "applied": args.apply,
        }
        if args.apply and previous != args.version:
            endpoint = AgentEndpointConfig(
                version_selector=VersionSelector(
                    version_selection_rules=[
                        FixedRatioVersionSelectionRule(
                            agent_version=args.version, traffic_percentage=100
                        )
                    ]
                ),
                protocol_configuration=details.agent_endpoint.protocol_configuration,
            )
            project.agents.update_details(agent_name=args.agent, agent_endpoint=endpoint)
            verified = project.agents.get(agent_name=args.agent)
            report["verified_version"] = active_version(verified)
            if report["verified_version"] != args.version:
                raise SystemExit("Endpoint update returned without routing the target version.")
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
