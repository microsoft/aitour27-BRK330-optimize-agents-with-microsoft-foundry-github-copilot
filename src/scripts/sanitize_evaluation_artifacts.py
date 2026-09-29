#!/usr/bin/env python3
"""Remove personal and environment-specific identifiers from evaluation JSON."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


DROP_KEYS = {
    "conversation_id",
    "created_by",
    "generation_job_id",
    "job_logs",
    "operation_id",
    "previous_response_id",
    "report_url",
    "response_id",
    "span_id",
    "trace_id",
}
AZURE_AI_URI = re.compile(r"azureai://accounts/[^/]+/projects/[^/]+/")


def sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: sanitize(item)
            for key, item in value.items()
            if key not in DROP_KEYS
        }
    if isinstance(value, list):
        return [sanitize(item) for item in value]
    if isinstance(value, str):
        return AZURE_AI_URI.sub(
            "azureai://accounts/<account>/projects/<project>/",
            value,
        )
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Rewrite files in place; default mode reports files that would change.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    for path in args.paths:
        original = json.loads(path.read_text(encoding="utf-8"))
        sanitized = sanitize(original)
        changed = sanitized != original
        print(f"{'sanitize' if changed else 'unchanged'}: {path}")
        if args.apply and changed:
            path.write_text(
                json.dumps(sanitized, indent=2, ensure_ascii=True) + "\n",
                encoding="utf-8",
            )


if __name__ == "__main__":
    main()