#!/usr/bin/env python3
"""Validate and optionally register the BRK330 lightweight evaluation contract."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import yaml
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    AgentEvaluatorGenerationJobSource,
    DatasetEvaluatorGenerationJobSource,
    EvaluatorGenerationInputs,
    EvaluatorGenerationJob,
    PromptEvaluatorGenerationJobSource,
)
from azure.core.exceptions import ResourceNotFoundError
from azure.identity import AzureCliCredential

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_ROOT = REPO_ROOT / "data" / "evaluation" / "lightweight-v1"
DATASET_PATH = CONTRACT_ROOT / "dataset-v2.jsonl"
RUBRIC_PATH = CONTRACT_ROOT / "rubric-source.json"
INSTRUCTIONS_PATH = REPO_ROOT / "src" / "agent" / ".agent_configs" / "baseline" / "instructions.md"
POLICY_PATH = REPO_ROOT / "data" / "fixtures" / "policy" / "caldova-travel-policy.md"
AGENT_NAME = "contoso-travel"
DATASET_NAME = "brk330-lightweight-eval"
DATASET_VERSION = "2"
PREVIEW_HEADERS = {"Foundry-Features": "Evaluations=V1Preview"}


def azd_value(name: str) -> str | None:
    result = subprocess.run(
        ["azd", "env", "get-value", name],
        check=False,
        capture_output=True,
        text=True,
    )
    value = result.stdout.strip()
    return value if result.returncode == 0 and value else None


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_number} must contain a JSON object")
        rows.append(value)
    return rows


def validate_contract() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = load_jsonl(DATASET_PATH)
    rubric = json.loads(RUBRIC_PATH.read_text(encoding="utf-8"))
    if [row.get("name") for row in rows] != ["INS-01", "INS-02", "INS-03", "INS-04"]:
        raise ValueError("Dataset must contain INS-01 through INS-04 in order")
    if any(not row.get("query") or not row.get("expected_behavior") for row in rows):
        raise ValueError("Every dataset row requires query and expected_behavior")

    required_dimensions = {
        "policy_compliance",
        "policy_check_sequencing",
        "policy_evidence_fidelity",
        "numeric_consistency",
    }
    dimensions = {dimension.get("name") for dimension in rubric.get("dimensions", [])}
    if not required_dimensions.issubset(dimensions):
        raise ValueError("Rubric is missing Insights-derived dimensions")
    if rubric.get("score_scale", {}).get("pass_threshold") != 3:
        raise ValueError("Pass threshold must remain 3 on the 1-5 scale")
    if len(rubric.get("hard_gates", [])) != 4:
        raise ValueError("Exactly four independent hard gates are required")
    if len(rubric.get("optimization_freedom", [])) < 4:
        raise ValueError("Rubric must preserve meaningful optimization freedom")
    return rows, rubric


def generation_prompt(rubric: dict[str, Any]) -> str:
    sections = [
        "Generate a rubric evaluator for this Caldova travel agent. Preserve the requested outcome-focused dimensions, relative weights, pass threshold, hard gates, and optimization freedom. Cost and latency are not quality dimensions.",
        "## Approved rubric source\n" + json.dumps(rubric, indent=2),
        "## Baseline agent instructions\n" + INSTRUCTIONS_PATH.read_text(encoding="utf-8"),
        "## Caldova policy\n" + POLICY_PATH.read_text(encoding="utf-8"),
    ]
    return "\n\n".join(sections)


def persist_pinned_metadata(
    dataset: Any,
    evaluator: Any,
    dataset_hash: str,
    rubric_hash: str,
    judge_deployment: str,
    definition_path: Path,
) -> None:
    agent_root = REPO_ROOT / "src" / "agent"
    metadata_path = agent_root / ".foundry" / "agent-metadata.yaml"
    environment_name = azd_value("AZURE_ENV_NAME") or "dev"
    dataset_ref = (
        agent_root
        / ".foundry"
        / "datasets"
        / f"contoso-travel-{DATASET_NAME}-v{DATASET_VERSION}.ref.json"
    )
    dataset_ref.parent.mkdir(parents=True, exist_ok=True)
    dataset_ref.write_text(
        json.dumps(
            {
                "name": DATASET_NAME,
                "version": DATASET_VERSION,
                "uri": dataset.id,
                "content_path": str(DATASET_PATH.relative_to(REPO_ROOT)),
                "sha256": dataset_hash,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    metadata = (
        yaml.safe_load(metadata_path.read_text(encoding="utf-8"))
        if metadata_path.exists()
        else {}
    ) or {}
    metadata["defaultEnvironment"] = environment_name
    environments = metadata.setdefault("environments", {})
    environment = environments.setdefault(environment_name, {})
    environment["azd"] = {
        "environmentName": environment_name,
        "service": "contoso-travel",
    }
    environment["evaluationSuites"] = [
        {
            "id": "lightweight-v1",
            "generationSource": "eval-yaml",
            "tags": {"tier": "smoke", "purpose": "baseline", "stage": "generated"},
            "dataset": DATASET_NAME,
            "datasetVersion": DATASET_VERSION,
            "datasetFile": str(dataset_ref.relative_to(agent_root)),
            "datasetContentPath": os.path.relpath(DATASET_PATH, agent_root),
            "datasetUri": dataset.id,
            "evaluators": [
                {
                    "name": evaluator.name,
                    "version": str(evaluator.version),
                    "threshold": 0.5,
                    "judgeDeployment": judge_deployment,
                    "generationJobId": getattr(evaluator, "generation_job_id", None),
                    "definitionFile": str(definition_path.relative_to(agent_root)),
                    "rubricSourceSha256": rubric_hash,
                }
            ],
        }
    ]
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        yaml.safe_dump(metadata, sort_keys=False),
        encoding="utf-8",
    )
    print(f"Pinned metadata: {metadata_path.relative_to(REPO_ROOT)}")
    print(f"Pinned dataset reference: {dataset_ref.relative_to(REPO_ROOT)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the frozen contract. Add --apply to upload dataset v2 and "
            "generate or reuse the retained rubric evaluator."
        )
    )
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--project-endpoint")
    parser.add_argument("--model-deployment", default="gpt-5.4-mini")
    parser.add_argument("--poll-interval", type=int, default=10)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.poll_interval < 1:
        raise SystemExit("--poll-interval must be at least 1")
    rows, rubric = validate_contract()
    dataset_hash = sha256(DATASET_PATH)
    rubric_hash = sha256(RUBRIC_PATH)
    print(f"Cases: {len(rows)}")
    print(f"Dataset: {DATASET_NAME} v{DATASET_VERSION}")
    print(f"Dataset SHA256: {dataset_hash}")
    print(f"Evaluator: {rubric['name']}")
    print(f"Rubric SHA256: {rubric_hash}")
    print(f"Judge deployment: {args.model_deployment}")
    print("Local contract validation: passed")
    if not args.apply:
        print("No Azure changes made. Re-run with --apply to register artifacts.")
        return 0

    endpoint = args.project_endpoint or os.getenv("FOUNDRY_PROJECT_ENDPOINT") or azd_value(
        "FOUNDRY_PROJECT_ENDPOINT"
    )
    if not endpoint:
        raise SystemExit("Select an azd environment that defines FOUNDRY_PROJECT_ENDPOINT")

    with (
        AzureCliCredential() as credential,
        AIProjectClient(endpoint=endpoint, credential=credential, allow_preview=True) as client,
    ):
        try:
            dataset = client.datasets.get(DATASET_NAME, DATASET_VERSION)
            print(f"Reusing dataset: {dataset.id}")
        except ResourceNotFoundError:
            dataset = client.datasets.upload_file(
                name=DATASET_NAME,
                version=DATASET_VERSION,
                file_path=str(DATASET_PATH),
            )
            print(f"Uploaded dataset: {dataset.id}")

        try:
            versions = list(client.beta.evaluators.list_versions(rubric["name"], limit=100))
        except ResourceNotFoundError:
            versions = []
        if versions:
            versions.sort(key=lambda item: int(item.version or "0"), reverse=True)
            evaluator = versions[0]
            print(f"Reusing evaluator: {evaluator.name} v{evaluator.version}")
        else:
            operation_id = f"brk330-rubric-{rubric_hash[:24]}"
            poller = client.beta.evaluators.begin_create_generation_job(
                job=EvaluatorGenerationJob(
                    inputs=EvaluatorGenerationInputs(
                        model=args.model_deployment,
                        evaluator_name=rubric["name"],
                        evaluator_display_name="Caldova Travel Quality",
                        evaluator_description=rubric["description"],
                        sources=[
                            PromptEvaluatorGenerationJobSource(
                                description="Approved rubric, baseline instructions, and policy.",
                                prompt=generation_prompt(rubric),
                            ),
                            AgentEvaluatorGenerationJobSource(
                                description="Deployed Hosted Agent metadata and tool surface.",
                                agent_name=AGENT_NAME,
                            ),
                            DatasetEvaluatorGenerationJobSource(
                                description="Frozen four-case expected-behavior dataset.",
                                name=DATASET_NAME,
                                version=DATASET_VERSION,
                            ),
                        ],
                    )
                ),
                operation_id=operation_id,
                polling=False,
                headers=PREVIEW_HEADERS,
            )
            job_id = poller.details["job_id"]
            print(f"Generation job: {job_id}")
            for _ in range(180):
                job = client.beta.evaluators.get_generation_job(
                    job_id,
                    headers=PREVIEW_HEADERS,
                )
                status = getattr(job.status, "value", str(job.status)).lower()
                print(f"Generation status: {status}")
                if status in {"succeeded", "failed", "canceled", "cancelled"}:
                    break
                time.sleep(args.poll_interval)
            else:
                raise TimeoutError(f"Generation job {job_id} did not finish within 30 minutes")
            if status != "succeeded":
                raise RuntimeError(
                    f"Generation job {job_id} ended as {status}: "
                    f"{json.dumps(job.as_dict(), default=str)}"
                )
            result = job.as_dict().get("result") or {}
            evaluator_name = result.get("name")
            evaluator_version = str(result.get("version") or "")
            if not evaluator_name or not evaluator_version:
                raise RuntimeError(f"Generation job {job_id} returned no evaluator version")
            evaluator = client.beta.evaluators.get_version(
                evaluator_name,
                evaluator_version,
                headers=PREVIEW_HEADERS,
            )
            print(f"Generated evaluator: {evaluator.name} v{evaluator.version}")

        output_dir = REPO_ROOT / "src" / "agent" / ".foundry" / "evaluators"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{evaluator.name}-v{evaluator.version}.json"
        output = {
            "dataset": {
                "name": DATASET_NAME,
                "version": DATASET_VERSION,
                "id": dataset.id,
                "sha256": dataset_hash,
            },
            "evaluator": evaluator.as_dict(),
            "rubric_source_sha256": rubric_hash,
            "judge_deployment": args.model_deployment,
        }
        output_path.write_text(json.dumps(output, indent=2, default=str) + "\n", encoding="utf-8")
        print(f"Saved review artifact: {output_path.relative_to(REPO_ROOT)}")
        persist_pinned_metadata(
            dataset,
            evaluator,
            dataset_hash,
            rubric_hash,
            args.model_deployment,
            output_path,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())