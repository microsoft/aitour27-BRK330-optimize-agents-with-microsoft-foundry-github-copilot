#!/usr/bin/env python3
"""Build the travel scorecard (rubric evaluator) from v1 traces.

Usage:
    python src/scripts/build_scorecard.py            # local check only
    python src/scripts/build_scorecard.py --apply    # upload sets, draft scorecard

--apply uploads the testing and exploring question sets as Foundry datasets and
drafts the scorecard from the v1 traces recorded by step 04, the Insights
findings saved by step 05, and data/scorecard-guidance.json. It reuses an
existing scorecard instead of creating a duplicate. Review the saved draft
before scoring any version.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from src.scripts.questions import path_for, validate  # noqa: E402

GUIDANCE_PATH = REPO_ROOT / "data" / "scorecard-guidance.json"
INSTRUCTIONS_PATH = REPO_ROOT / "src" / "agent" / ".agent_configs" / "baseline" / "instructions.md"
POLICY_PATH = REPO_ROOT / "data" / "fixtures" / "policy" / "caldova-travel-policy.md"
AGENT_NAME = "contoso-travel"
DATASETS = {"testing": "brk330-testing", "exploring": "brk330-exploring"}
DATASET_VERSION = "1"
PREVIEW_HEADERS = {"Foundry-Features": "Evaluations=V1Preview"}


def azd_value(name: str) -> str | None:
    result = subprocess.run(["azd", "env", "get-value", name], capture_output=True, text=True, check=False)
    value = result.stdout.strip()
    return value if result.returncode == 0 and value else None


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_guidance() -> dict[str, Any]:
    guidance = json.loads(GUIDANCE_PATH.read_text(encoding="utf-8"))
    for key in ("name", "description", "suggested_dimensions", "must_never", "allow"):
        if not guidance.get(key):
            raise ValueError(f"scorecard guidance is missing {key}")
    if guidance.get("pass_threshold") != 0.5:
        raise ValueError("scorecard pass_threshold must stay 0.5")
    return guidance


def brief(finding: dict[str, Any]) -> dict[str, Any]:
    details = finding.get("details") or {}
    return {
        "title": finding.get("title"),
        "severity": finding.get("severity"),
        "traces": finding.get("trace_count"),
        "description": finding.get("description"),
        "proposed_fix": (details.get("recommended_actions") or {}).get("proposed_fix"),
        "examples": [trace.get("summary") for trace in (details.get("highlighted_traces") or [])[:3]],
    }


def generation_prompt(guidance: dict[str, Any], findings: list[dict[str, Any]]) -> str:
    sections = [
        "Draft a rubric evaluator for the Caldova travel concierge. Base the dimensions on what the "
        "v1 traces actually show, use the guidance as a starting point, and keep cost and latency out "
        "of the quality score.",
        "## Guidance\n" + json.dumps(guidance, indent=2),
        "## Insights findings from v1\n"
        + (json.dumps([brief(finding) for finding in findings], indent=2) if findings else "None saved."),
        "## Agent instructions (v1)\n" + INSTRUCTIONS_PATH.read_text(encoding="utf-8"),
        "## Caldova travel policy\n" + POLICY_PATH.read_text(encoding="utf-8"),
    ]
    return "\n\n".join(sections)


def trace_window(environment: str) -> tuple[datetime, datetime]:
    window_file = REPO_ROOT / ".azure" / environment / "questions" / "exploring-v1-latest.json"
    if not window_file.exists():
        raise SystemExit("No v1 exploring run found. Run step 04 with --set exploring --version 1 first.")
    window = json.loads(window_file.read_text(encoding="utf-8"))
    start = datetime.fromisoformat(window["started_at"]) - timedelta(minutes=5)
    end = datetime.fromisoformat(window.get("finished_at") or window["started_at"]) + timedelta(minutes=15)
    return start, end


def load_findings(environment: str) -> list[dict[str, Any]]:
    findings_file = REPO_ROOT / ".azure" / environment / "insights" / "findings.json"
    if not findings_file.exists():
        print("No saved Insights findings; drafting from traces and guidance only.")
        return []
    return json.loads(findings_file.read_text(encoding="utf-8"))


def upload_datasets(client: Any) -> None:
    from azure.core.exceptions import ResourceNotFoundError

    for set_name, dataset_name in DATASETS.items():
        try:
            client.datasets.get(dataset_name, DATASET_VERSION)
            print(f"Reusing dataset {dataset_name} v{DATASET_VERSION}")
        except ResourceNotFoundError:
            client.datasets.upload_file(
                name=dataset_name, version=DATASET_VERSION, file_path=str(path_for(set_name))
            )
            print(f"Uploaded dataset {dataset_name} v{DATASET_VERSION}")


def draft_scorecard(client: Any, guidance: dict[str, Any], args: argparse.Namespace, environment: str) -> Any:
    from azure.ai.projects.models import (
        AgentEvaluatorGenerationJobSource,
        DatasetEvaluatorGenerationJobSource,
        EvaluatorGenerationInputs,
        EvaluatorGenerationJob,
        PromptEvaluatorGenerationJobSource,
        TracesEvaluatorGenerationJobSource,
    )
    from azure.core.exceptions import ResourceNotFoundError

    try:
        versions = list(client.beta.evaluators.list_versions(guidance["name"], limit=100))
    except ResourceNotFoundError:
        versions = []
    if versions:
        versions.sort(key=lambda item: int(item.version or "0"), reverse=True)
        print(f"Reusing scorecard {versions[0].name} v{versions[0].version}")
        return versions[0]

    start, end = trace_window(environment)
    findings = load_findings(environment)
    print(f"Drafting from v1 traces between {start.isoformat()} and {end.isoformat()}")
    poller = client.beta.evaluators.begin_create_generation_job(
        job=EvaluatorGenerationJob(
            inputs=EvaluatorGenerationInputs(
                model=args.model_deployment,
                evaluator_name=guidance["name"],
                evaluator_display_name=guidance["display_name"],
                evaluator_description=guidance["description"],
                sources=[
                    TracesEvaluatorGenerationJobSource(
                        description="v1 traces from the exploring questions.",
                        agent_name=AGENT_NAME, agent_version="1", start_time=start, end_time=end,
                    ),
                    AgentEvaluatorGenerationJobSource(
                        description="The v1 Hosted Agent and its tools.", agent_name=AGENT_NAME, agent_version="1",
                    ),
                    DatasetEvaluatorGenerationJobSource(
                        description="Exploring questions with expected outcomes.",
                        name=DATASETS["exploring"], version=DATASET_VERSION,
                    ),
                    PromptEvaluatorGenerationJobSource(
                        description="Guidance, Insights findings, v1 instructions, and Caldova policy.",
                        prompt=generation_prompt(guidance, findings),
                    ),
                ],
            )
        ),
        operation_id=f"brk330-scorecard-{sha256(GUIDANCE_PATH)[:24]}",
        polling=False,
        headers=PREVIEW_HEADERS,
    )
    job_id = poller.details["job_id"]
    print(f"Scorecard draft started: {job_id}")
    for _ in range(180):
        job = client.beta.evaluators.get_generation_job(job_id, headers=PREVIEW_HEADERS)
        status = getattr(job.status, "value", str(job.status)).lower()
        print(f"Draft status: {status}")
        if status in {"succeeded", "failed", "canceled", "cancelled"}:
            break
        time.sleep(args.poll_interval)
    else:
        raise TimeoutError(f"Scorecard draft {job_id} did not finish within the polling window")
    if status != "succeeded":
        raise RuntimeError(f"Scorecard draft {job_id} ended as {status}: {json.dumps(job.as_dict(), default=str)}")
    result = job.as_dict().get("result") or {}
    return client.beta.evaluators.get_version(
        result["name"], str(result["version"]), headers=PREVIEW_HEADERS
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="Upload question sets and draft the scorecard.")
    parser.add_argument("--project-endpoint")
    parser.add_argument("--model-deployment", default="gpt-5.4-mini")
    parser.add_argument("--poll-interval", type=int, default=10)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    sets = validate()
    guidance = load_guidance()
    for set_name, dataset_name in DATASETS.items():
        print(f"{dataset_name}: {len(sets[set_name])} questions, SHA256 {sha256(path_for(set_name))}")
    print(f"Scorecard: {guidance['name']} (guidance SHA256 {sha256(GUIDANCE_PATH)})")
    print(f"Judge deployment: {args.model_deployment}")
    if not args.apply:
        print("Local check passed. No Azure changes made; add --apply to build the scorecard.")
        return 0

    from azure.ai.projects import AIProjectClient
    from azure.identity import AzureCliCredential

    environment = azd_value("AZURE_ENV_NAME")
    endpoint = args.project_endpoint or os.getenv("FOUNDRY_PROJECT_ENDPOINT") or azd_value("FOUNDRY_PROJECT_ENDPOINT")
    if not environment or not endpoint:
        raise SystemExit("Select the session azd environment first.")
    with AzureCliCredential() as credential, AIProjectClient(
        endpoint=endpoint, credential=credential, allow_preview=True
    ) as client:
        upload_datasets(client)
        scorecard = draft_scorecard(client, guidance, args, environment)

    folder = REPO_ROOT / ".azure" / environment / "scorecard"
    folder.mkdir(parents=True, exist_ok=True)
    review_file = folder / f"{scorecard.name}-v{scorecard.version}.json"
    review_file.write_text(json.dumps(scorecard.as_dict(), indent=2, default=str) + "\n", encoding="utf-8")
    print(f"Scorecard ready: {scorecard.name} v{scorecard.version}")
    print(f"Review it in Foundry or in {review_file.relative_to(REPO_ROOT)} before scoring any version.")
    if str(scorecard.version) != "1":
        print("Note: src/agent/eval.yaml expects version 1. Update it if you deliberately created a new version.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
