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
    from ..config import DATA_DIR
    from ..telemetry import span, set_span_attr
    from ..policy_engine import check_expense_line
except ImportError:
    from config import DATA_DIR
    from telemetry import span, set_span_attr
    from policy_engine import check_expense_line

RECEIPTS_DIR = DATA_DIR / "receipts"


def extract_receipt(*, receipt_id: str | None = None, image_path: str | None = None) -> dict[str, Any]:
    """Return the structured receipt JSON. Prefers fixture id; falls back to
    matching a supplied image path back to a fixture."""
    with span("tool.extract_receipt", receipt_id=receipt_id or "-", image_path=image_path or "-"):
        rid = receipt_id
        if not rid and image_path:
            rid = Path(image_path).stem
        if not rid:
            return {"error": "receipt_id or image_path required"}
        expected = RECEIPTS_DIR / f"{rid}.json"
        if not expected.exists():
            set_span_attr("tool.extraction_status", "unknown_fixture")
            return {"error": f"no fixture for {rid}"}
        data = json.loads(expected.read_text())
        # Layer policy_engine judgments per line
        flagged = []
        for line in data.get("line_items", []):
            for d in check_expense_line(line):
                if not d.allowed:
                    flagged.append({"line": line.get("description"), **d.to_dict()})
        data["policy_flagged_lines"] = flagged
        set_span_attr("tool.flagged_line_count", len(flagged))
        return data
