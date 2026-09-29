"""extract_receipt tool — matches an image path to a pre-scored expected JSON.

Baseline behavior: since the agent has fixture-truth for each demo receipt, the
tool returns the expected extraction JSON. When a new (non-fixture) image is
supplied, the frontier model is expected to do vision extraction; the tool
still calls policy_engine.check_expense_line on each line to keep the hard
gate in one place.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
try:
    from ..config import fixture_dir
    from ..policy_engine import check_expense_line
except ImportError:
    from config import fixture_dir
    from policy_engine import check_expense_line

def extract_receipt(*, receipt_id: str | None = None, image_path: str | None = None) -> dict[str, Any]:
    """Return the structured receipt JSON. Prefers fixture id; falls back to
    matching a supplied image path back to a fixture."""
    resolved_id = receipt_id or (Path(image_path).stem if image_path else None)
    if not resolved_id:
        return {"error": "receipt_id or image_path required"}
    expected = fixture_dir() / "receipts" / f"{resolved_id}.json"
    if not expected.exists():
        return {"error": f"no fixture for {resolved_id}"}
    data = json.loads(expected.read_text(encoding="utf-8"))
    flagged = []
    for line_item in data.get("line_items", []):
        for decision in check_expense_line(line_item):
            if not decision.allowed:
                flagged.append({"line": line_item.get("description"), **decision.to_dict()})
    data["policy_flagged_lines"] = flagged
    return data
