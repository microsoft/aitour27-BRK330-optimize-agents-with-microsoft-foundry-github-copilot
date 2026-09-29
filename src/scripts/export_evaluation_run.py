#!/usr/bin/env python3
"""Export Foundry evaluation run metadata and row-level output."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-endpoint", required=True)
    parser.add_argument("--eval-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--out-file", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.out_file.parent.mkdir(parents=True, exist_ok=True)
    items_file = args.out_file.with_name(f"{args.out_file.stem}.items.json")

    with DefaultAzureCredential() as credential, AIProjectClient(
        endpoint=args.project_endpoint,
        credential=credential,
    ) as project_client:
        client = project_client.get_openai_client()
        run = client.evals.runs.retrieve(
            eval_id=args.eval_id,
            run_id=args.run_id,
        )
        items = [
            item.model_dump()
            for item in client.evals.runs.output_items.list(
                eval_id=args.eval_id,
                run_id=args.run_id,
            )
        ]

    args.out_file.write_text(
        json.dumps(run.model_dump(), indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    items_file.write_text(
        json.dumps(items, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    print(f"Exported run metadata: {args.out_file}")
    print(f"Exported {len(items)} row items: {items_file}")


if __name__ == "__main__":
    main()