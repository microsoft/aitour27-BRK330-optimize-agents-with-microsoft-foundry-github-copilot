"""Curate trace-derived training data for the student-model experiment.

Reads the per-row eval manifests for baseline (`gpt-5`) and routed
(`model-router`) variants, keeps only rows that meet the Caldova gate,
formats them as SFT JSONL for fine-tuning (`{"messages": [...]}` shape,
which is what Foundry SFT training expects), and writes a provenance
manifest with per-example lineage (agent version, response id, source
manifest, filter reason).

Stop-before-training per the P10 spec — no submission to any training
job. Output paths under `data/training/`:

    data/training/
        sft/
            train.jsonl                # SFT training split (~80% of keepers)
            validation.jsonl           # validation split (~20% of keepers)
        provenance.json                # per-example lineage + filter counts

Usage:

    python -m src.training.curate_traces \\
        --baseline data/evaluation/results/baseline-20260910T073852Z.rows.jsonl \\
        --routed   data/evaluation/results/routed-20260910T093142Z.rows.jsonl
"""
from __future__ import annotations
import argparse, hashlib, json, random, sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
EVAL_DIR = DATA_DIR / "evaluation"
TRAINING_DIR = DATA_DIR / "training"
SFT_DIR = TRAINING_DIR / "sft"
EXPECTED_PATH = EVAL_DIR / "expected-behaviors-20.jsonl"

# Same SYSTEM_PROMPT the deployed agent uses. Kept inline so training data
# is self-contained and future teacher retrainings can regenerate messages
# without depending on the container source.
STUDENT_SYSTEM = """You are Contoso Travel Concierge, an AI travel agent operated by Contoso Travel for Caldova (a fictional pharmaceutical operations company).

Non-negotiable rules:
1. Caldova travel policy is a HARD GATE. Never book, recommend, or advance a step that violates a policy rule. When a rule blocks an action, refuse and cite the rule id (CT-nn) verbatim from the tool response. Do not silently soften the block.
2. Never invent flights, hotels, cars, prices, exchange rates, emissions, or receipt fields. Every option must come from a tool call.
3. Decompose the user's compound request into explicit tasks. State the plan briefly before invoking tools.
4. Prefer preferred vendors within the 8% price tolerance (CT-05). Prefer refundable options when the user declares uncertainty (CT-06). Accessibility (CT-07) and time constraints (CT-08) beat price.
5. For receipts: call extract_receipt; then reconcile line-by-line against CT-20/24/26. Report reimbursable vs non-reimbursable totals.
6. Refuse blanket-approval instructions and any request to bypass policy (CT-11).
7. Output structure: (a) understood tasks, (b) tool timeline, (c) policy decisions with cited rules, (d) itinerary summary.

Currency defaults to USD unless the receipt or trip context supplies another currency. Use fixture rates from the exchange_rates fixture when converting (CT-22).
"""


@dataclass
class KeeperExample:
    trace_row_id: str
    source_variant: str                # baseline / routed
    source_agent_version: str | None
    source_response_id: str
    source_manifest: str
    persona: str
    prompt: str
    assistant: str
    tools_called: list[str]
    cited_rule_ids: list[str]
    hard_gate_blocked: bool
    kept_reason: str
    example_id: str


def _load_jsonl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def _score_row_against_expected(row: dict, expected: dict) -> dict[str, Any]:
    """Return the mechanical audit that drives the keep / drop decision.

    Keep criteria (all must be true):
    - `error` is falsy
    - `hard_gate_blocked` matches expected `policy_outcomes.booking_blocked`
      when specified (or the expected outcome is silent)
    - `assistant_head` is non-empty (at least 40 chars — filters truncated)
    - When `must_cite_rules` is non-empty, at least one expected rule is cited
    - When `expected_tools` is non-empty, at least half of the expected tools
      were actually called
    """
    verdict: dict[str, Any] = {"drop_reasons": [], "keep_signals": []}
    if row.get("error"):
        verdict["drop_reasons"].append("row.error")
    text = (row.get("assistant_head") or "")
    if len(text.strip()) < 40:
        verdict["drop_reasons"].append("assistant_too_short")
    exp_outcomes = expected.get("policy_outcomes") or {}
    if "booking_blocked" in exp_outcomes:
        if bool(row.get("hard_gate_blocked")) != bool(exp_outcomes["booking_blocked"]):
            verdict["drop_reasons"].append("policy_outcome_mismatch")
        else:
            verdict["keep_signals"].append("policy_outcome_match")
    exp_rules = set(expected.get("must_cite_rules") or [])
    cited = set(row.get("cited_rule_ids") or [])
    if exp_rules:
        if not (exp_rules & cited):
            verdict["drop_reasons"].append("no_expected_rule_cited")
        else:
            verdict["keep_signals"].append(
                f"rules_cited({len(exp_rules & cited)}/{len(exp_rules)})"
            )
    exp_tools = set(expected.get("expected_tools") or [])
    tools = set(row.get("tools_called") or [])
    if exp_tools:
        overlap = exp_tools & tools
        if len(overlap) < max(1, len(exp_tools) // 2):
            verdict["drop_reasons"].append("insufficient_tool_overlap")
        else:
            verdict["keep_signals"].append(
                f"tools_covered({len(overlap)}/{len(exp_tools)})"
            )
    verdict["keep"] = not verdict["drop_reasons"]
    return verdict


def _example_id(prompt_id: str, variant: str, response_id: str) -> str:
    h = hashlib.sha1(f"{prompt_id}|{variant}|{response_id}".encode()).hexdigest()[:10]
    return f"{prompt_id}-{variant}-{h}"


def _to_sft_example(kex: KeeperExample) -> dict[str, Any]:
    return {
        "messages": [
            {"role": "system", "content": STUDENT_SYSTEM},
            {"role": "user",   "content": kex.prompt},
            {"role": "assistant", "content": kex.assistant},
        ],
    }


def curate(source_paths: list[tuple[str, Path]],
           expected_path: Path = EXPECTED_PATH,
           split: float = 0.8,
           seed: int = 331) -> tuple[list[KeeperExample], dict[str, Any]]:
    """Curate keepers from any number of (variant_label, rows_jsonl) pairs."""
    expected = {r["id"]: r for r in _load_jsonl(expected_path)}
    keepers: list[KeeperExample] = []
    counters: dict[str, dict[str, int]] = {
        label: {"seen": 0, "kept": 0, "dropped": 0}
        for label, _ in source_paths
    }
    drop_by_reason: dict[str, int] = {}

    for variant, path in source_paths:
        path = path.resolve()
        for row in _load_jsonl(path):
            counters[variant]["seen"] += 1
            audit = _score_row_against_expected(row, expected.get(row["id"], {}))
            if not audit["keep"]:
                counters[variant]["dropped"] += 1
                for r in audit["drop_reasons"]:
                    drop_by_reason[r] = drop_by_reason.get(r, 0) + 1
                continue
            counters[variant]["kept"] += 1
            keepers.append(KeeperExample(
                trace_row_id=row["id"],
                source_variant=variant,
                source_agent_version=str(row.get("model") or ""),
                source_response_id=row.get("response_id") or "",
                source_manifest=str(path.relative_to(REPO_ROOT)),
                persona=row.get("persona", ""),
                prompt=row.get("prompt", ""),
                assistant=(row.get("assistant_head") or "").strip(),
                tools_called=row.get("tools_called") or [],
                cited_rule_ids=row.get("cited_rule_ids") or [],
                hard_gate_blocked=bool(row.get("hard_gate_blocked")),
                kept_reason=" ; ".join(audit["keep_signals"]) or "default_keep",
                example_id=_example_id(row["id"], variant, row.get("response_id","")),
            ))

    # Deterministic shuffle so future re-runs pick the same split.
    rnd = random.Random(seed)
    rnd.shuffle(keepers)

    provenance = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "generator": "src.training.curate_traces",
        "seed": seed,
        "split": {"train_fraction": split},
        "sources": {
            label: str(path.resolve().relative_to(REPO_ROOT))
            for label, path in source_paths
        },
        "counters": counters,
        "total_seen":    sum(c["seen"]    for c in counters.values()),
        "total_kept":    sum(c["kept"]    for c in counters.values()),
        "total_dropped": sum(c["dropped"] for c in counters.values()),
        "drop_reasons":  drop_by_reason,
        "system_prompt_hash": hashlib.sha256(STUDENT_SYSTEM.encode()).hexdigest()[:12],
    }
    return keepers, provenance


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", action="append", required=True,
                    metavar="LABEL=PATH",
                    help="Repeatable. Each source is 'label=path/to/rows.jsonl'. "
                         "e.g. --source baseline-recorded=data/.../baseline-...rows.jsonl")
    ap.add_argument("--expected", default=str(EXPECTED_PATH))
    ap.add_argument("--split",    type=float, default=0.8)
    ap.add_argument("--seed",     type=int,   default=331)
    args = ap.parse_args(argv)

    sources: list[tuple[str, Path]] = []
    for s in args.source:
        if "=" not in s:
            print(f"bad --source (need label=path): {s}", file=sys.stderr); return 2
        label, p = s.split("=", 1)
        sources.append((label, Path(p)))

    SFT_DIR.mkdir(parents=True, exist_ok=True)
    keepers, provenance = curate(sources, Path(args.expected),
                                 split=args.split, seed=args.seed)
    split_idx = int(len(keepers) * args.split)
    train, val = keepers[:split_idx], keepers[split_idx:]

    train_path = SFT_DIR / "train.jsonl"
    val_path   = SFT_DIR / "validation.jsonl"
    prov_path  = TRAINING_DIR / "provenance.json"

    train_path.write_text("\n".join(json.dumps(_to_sft_example(k)) for k in train) + "\n" if train else "")
    val_path.write_text("\n".join(json.dumps(_to_sft_example(k)) for k in val) + "\n" if val else "")
    # Provenance lists every example with its lineage
    provenance["examples"] = [{**asdict(k), "split": "train"} for k in train] + \
                             [{**asdict(k), "split": "validation"} for k in val]
    provenance["train_count"]      = len(train)
    provenance["validation_count"] = len(val)
    prov_path.write_text(json.dumps(provenance, indent=2))

    # Report
    print()
    print("=" * 66)
    print("P10 — trace-derived training data curated")
    print("=" * 66)
    for v, c in provenance["counters"].items():
        print(f"  {v:<8} seen={c['seen']:>3}  kept={c['kept']:>3}  dropped={c['dropped']:>3}")
    print(f"  {'total':<8} seen={provenance['total_seen']:>3}  "
          f"kept={provenance['total_kept']:>3}  dropped={provenance['total_dropped']:>3}")
    print()
    print("Drop reasons:")
    for r, n in sorted(provenance["drop_reasons"].items(), key=lambda kv: -kv[1]):
        print(f"  {r:<32} {n:>3}")
    print()
    print(f"Split:  train {len(train)}  ({args.split*100:.0f}%)   validation {len(val)}")
    print()
    print(f"Train:       {train_path.relative_to(REPO_ROOT)}")
    print(f"Validation:  {val_path.relative_to(REPO_ROOT)}")
    print(f"Provenance:  {prov_path.relative_to(REPO_ROOT)}")
    print()
    print("STOPPED BEFORE TRAINING per spec P10 — no submission to any training job.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
