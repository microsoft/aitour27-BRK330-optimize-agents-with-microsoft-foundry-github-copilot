#!/usr/bin/env python3
"""Convert .plan/test-prompts.md table into machine-readable JSONL."""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / ".plan" / "test-prompts.md"
OUT_DIR = ROOT / "data" / "evaluation"
OUT_DIR.mkdir(parents=True, exist_ok=True)

rows_all = []
rows_20 = []

for line in SRC.read_text().splitlines():
    if not line.startswith("| TP-"):
        continue
    parts = [p.strip() for p in line.strip("|").split("|")]
    if len(parts) < 7:
        continue
    tp_id, in20, persona, prompt, intents, assets, expected = parts[:7]
    row = {
        "id": tp_id,
        "in_recorded_subset": in20.lower() == "yes",
        "persona": persona,
        "prompt": prompt,
        "intents": [t.strip() for t in intents.split(",")],
        "assets": [a.strip() for a in assets.split(",") if a.strip() and a.strip().lower() != "none"],
        "expected_behavior": expected,
    }
    rows_all.append(row)
    if row["in_recorded_subset"]:
        rows_20.append(row)

(OUT_DIR / "prompts-50.jsonl").write_text("\n".join(json.dumps(r) for r in rows_all) + "\n")
(OUT_DIR / "prompts-20.jsonl").write_text("\n".join(json.dumps(r) for r in rows_20) + "\n")
print(f"Wrote {len(rows_all)} prompts and {len(rows_20)} in fixed subset")
print("Fixed subset IDs:", ", ".join(r["id"] for r in rows_20))
