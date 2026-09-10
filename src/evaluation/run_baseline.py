"""Run the fixed 20-prompt subset against a deployed hosted-agent variant.

Loads `data/evaluation/prompts-20.jsonl` and calls the Foundry hosted-agent
Responses endpoint directly (bypasses the FastAPI web to keep the metrics
scoped to the agent itself). Captures per-row latency, tokens, tool timeline,
policy citations, and trace id. Scores each row deterministically against
`data/evaluation/expected-behaviors-20.jsonl`. Writes a versioned result
manifest under `data/evaluation/results/`.

Usage:
    python -m src.evaluation.run_baseline \\
        --variant baseline \\
        --project-endpoint https://.../api/projects/... \\
        --agent contoso-travel
luate
Concurrent execution defaults to 3 workers to respect rate limits.
"""
from __future__ import annotations
import argparse, concurrent.futures, json, os, sys, time, uuid
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any
from datetime import datetime, timezone

import httpx
from azure.identity import DefaultAzureCredential

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
EVAL_DIR = DATA_DIR / "evaluation"
RESULTS_DIR = EVAL_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True, parents=True)

# Approximate public list-price snapshot for gpt-5 (USD per 1M tokens).
# Kept here as an assumption; individual demo runs SHOULD swap in the price
# the CFO story assumes and refresh in the summary if it changes.
PRICES_USD_PER_1M = {
    "gpt-5":         {"input": 2.50,  "output": 10.00, "cached": 0.25},
    "gpt-4.1":       {"input": 2.00,  "output":  8.00, "cached": 0.20},
    "gpt-4.1-mini":  {"input": 0.40,  "output":  1.60, "cached": 0.04},
    "model-router":  {"input": 0.00,  "output":  0.00, "cached": 0.00},  # priced by routed target
    "gpt-5-mini":    {"input": 0.25,  "output":  1.00, "cached": 0.025},
}


@dataclass
class RunRow:
    id: str
    persona: str
    prompt: str
    attachments: list[str]
    variant: str
    model: str
    trace_id: str = ""
    response_id: str = ""
    latency_ms: int = 0
    tokens_input: int = 0
    tokens_output: int = 0
    tokens_total: int = 0
    tokens_cached: int = 0
    cost_per_request_usd: float = 0.0
    tools_called: list[str] = field(default_factory=list)
    cited_rule_ids: list[str] = field(default_factory=list)
    hard_gate_blocked: bool = False
    assistant_head: str = ""
    error: str | None = None
    # Rubric-derived scores (deterministic scoring against expected behavior)
    score_intent_completeness: int = 0
    score_policy_compliance: int = 0
    score_tool_use_accuracy: int = 0
    score_receipt_accuracy: int | None = None
    passed_hard_gate: bool = False


def _load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _extract_receipt_fixture(rid: str) -> dict | None:
    p = DATA_DIR / "receipts" / f"{rid}.json"
    if p.exists():
        return json.loads(p.read_text())
    return None


def _score_row(row: RunRow, expected: dict) -> RunRow:
    """Deterministic rubric scoring against expected-behaviors-20.jsonl."""
    exp_tools = set(expected.get("expected_tools") or [])
    exp_rules = set(expected.get("must_cite_rules") or [])
    exp_outcomes = expected.get("policy_outcomes") or {}
    called = set(row.tools_called)
    cited = set(row.cited_rule_ids)

    # Intent completeness — 5 if every expected tool was called; 3 if most; 1 if none
    if not exp_tools:
        row.score_intent_completeness = 5 if row.assistant_head else 3
    else:
        overlap = called & exp_tools
        pct = len(overlap) / len(exp_tools)
        row.score_intent_completeness = 5 if pct >= 0.8 else (3 if pct >= 0.5 else 1)

    # Policy compliance — hard gate. 5 if all required rules cited AND outcome matches
    if exp_outcomes.get("booking_blocked") is True:
        # Should have blocked
        row.passed_hard_gate = bool(row.hard_gate_blocked)
    elif exp_outcomes.get("booking_blocked") is False:
        row.passed_hard_gate = not row.hard_gate_blocked
    else:
        # No explicit block expectation: pass if either outcome is defensible
        row.passed_hard_gate = True

    if exp_rules:
        rule_pct = len(cited & exp_rules) / len(exp_rules)
        rule_score = 5 if rule_pct >= 0.8 else (3 if rule_pct >= 0.5 else 1)
    else:
        rule_score = 5
    row.score_policy_compliance = rule_score if row.passed_hard_gate else 1

    # Tool-use accuracy — same as intent for now (no tool argument audit yet)
    row.score_tool_use_accuracy = row.score_intent_completeness

    # Receipt accuracy — only when a receipt asset was in scope
    if "REC-001" in row.attachments or "REC-002" in row.attachments \
            or "REC-003" in row.attachments or "REC-004" in row.attachments:
        # If extract_receipt was called and no error, credit; deeper audit is future work
        row.score_receipt_accuracy = 5 if "extract_receipt" in called else 1
    return row


def _run_one(prompt_row: dict, agent_url: str, variant: str, model: str,
             credential: DefaultAzureCredential) -> RunRow:
    row = RunRow(
        id=prompt_row["id"],
        persona=prompt_row.get("persona", ""),
        prompt=prompt_row.get("prompt", ""),
        attachments=[a for a in prompt_row.get("assets", []) if a.startswith("REC-")],
        variant=variant,
        model=model,
    )
    message = row.prompt
    if row.attachments:
        message += f"\n\nAttached receipts: {', '.join(row.attachments)}. Use extract_receipt for each."

    token = credential.get_token("https://ai.azure.com/.default").token
    started = time.time()
    try:
        with httpx.Client(timeout=300.0) as client:
            r = client.post(
                agent_url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "x-request-id": str(uuid.uuid4()),
                },
                json={"input": message, "store": False, "stream": False},
            )
        row.latency_ms = int((time.time() - started) * 1000)
        if r.status_code >= 400:
            row.error = f"HTTP {r.status_code}: {r.text[:400]}"
            return row
        data = r.json()
        row.response_id = data.get("id", "")
        row.trace_id = data.get("_request_id", "") or data.get("id", "")
        # tokens
        u = data.get("usage", {}) or {}
        row.tokens_input  = int(u.get("input_tokens") or 0)
        row.tokens_output = int(u.get("output_tokens") or 0)
        row.tokens_total  = int(u.get("total_tokens") or 0)
        row.tokens_cached = int((u.get("input_tokens_details") or {}).get("cached_tokens") or 0)
        # cost
        p = PRICES_USD_PER_1M.get(model, PRICES_USD_PER_1M["gpt-5"])
        uncached_in = max(0, row.tokens_input - row.tokens_cached)
        row.cost_per_request_usd = (
            uncached_in     * p["input"]  / 1_000_000
          + row.tokens_cached * p["cached"] / 1_000_000
          + row.tokens_output * p["output"] / 1_000_000
        )
        # tools + policy from output items
        cited: set[str] = set()
        blocked = False
        for item in data.get("output", []) or []:
            t = item.get("type")
            if t == "function_call":
                row.tools_called.append(item.get("name", "?"))
            elif t == "function_call_output":
                try:
                    out = json.loads(item.get("output", "{}") or "{}")
                except Exception:
                    continue
                if isinstance(out, dict):
                    for cr in out.get("cited_rule_ids", []) or []:
                        cited.add(cr)
                    if out.get("hard_gate_blocked"):
                        blocked = True
            elif t == "message":
                for content in item.get("content", []) or []:
                    if content.get("type") in ("output_text", "text"):
                        row.assistant_head += content.get("text", "")[:800]
                        row.assistant_head = row.assistant_head[:1200]
        row.cited_rule_ids = sorted(cited)
        row.hard_gate_blocked = blocked
    except Exception as e:
        row.error = f"{type(e).__name__}: {e}"
        row.latency_ms = int((time.time() - started) * 1000)
    return row


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant", default="baseline")
    parser.add_argument("--model", default="gpt-5")
    parser.add_argument("--project-endpoint", required=True,
                        help="Foundry project endpoint (…/api/projects/<name>)")
    parser.add_argument("--agent", default="contoso-travel")
    parser.add_argument("--parallel", type=int, default=3)
    parser.add_argument("--limit", type=int, default=0, help="cap prompts (dev only)")
    parser.add_argument("--dataset", default=str(EVAL_DIR / "prompts-20.jsonl"))
    parser.add_argument("--expected", default=str(EVAL_DIR / "expected-behaviors-20.jsonl"))
    args = parser.parse_args(argv)

    prompts = _load_jsonl(Path(args.dataset))
    expected_all = {r["id"]: r for r in _load_jsonl(Path(args.expected))}
    if args.limit:
        prompts = prompts[:args.limit]

    agent_url = (
        args.project_endpoint.rstrip("/") +
        f"/agents/{args.agent}/endpoint/protocols/openai/responses?api-version=v1"
    )
    print(f"Endpoint: {agent_url}")
    print(f"Variant:  {args.variant} ({args.model})")
    print(f"Prompts:  {len(prompts)}  (parallel={args.parallel})")

    credential = DefaultAzureCredential()
    started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    rows: list[RunRow] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.parallel) as pool:
        futures = {
            pool.submit(_run_one, p, agent_url, args.variant, args.model, credential): p
            for p in prompts
        }
        for i, fut in enumerate(concurrent.futures.as_completed(futures), 1):
            p = futures[fut]
            row = fut.result()
            row = _score_row(row, expected_all.get(row.id, {}))
            rows.append(row)
            marker = "BLOCK" if row.hard_gate_blocked else ("ERR" if row.error else "OK")
            print(f"  [{i:>2}/{len(prompts)}] {row.id:<6} {marker:<5} "
                  f"latency={row.latency_ms}ms  tokens={row.tokens_total}  "
                  f"cost=${row.cost_per_request_usd:.4f}  tools={len(row.tools_called)}"
                  f"  cited={','.join(row.cited_rule_ids) or '-'}")
            if row.error:
                print(f"          error: {row.error[:180]}")

    rows.sort(key=lambda r: r.id)
    ended_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    # Aggregate
    ok = [r for r in rows if not r.error]
    n = len(ok)
    def _avg(vals):
        return sum(vals) / n if n else 0
    aggregate = {
        "row_count": len(rows),
        "row_count_ok": n,
        "row_count_errors": len(rows) - n,
        "avg_latency_ms": int(_avg([r.latency_ms for r in ok])),
        "p95_latency_ms": (sorted(r.latency_ms for r in ok)[max(0, int(0.95*n)-1)] if n else 0),
        "sum_tokens_input":  sum(r.tokens_input  for r in ok),
        "sum_tokens_output": sum(r.tokens_output for r in ok),
        "sum_tokens_total":  sum(r.tokens_total  for r in ok),
        "sum_tokens_cached": sum(r.tokens_cached for r in ok),
        "sum_cost_usd":      round(sum(r.cost_per_request_usd for r in ok), 4),
        "cost_per_request_usd_avg": round(_avg([r.cost_per_request_usd for r in ok]), 4),
        "avg_score_intent":         round(_avg([r.score_intent_completeness for r in ok]), 2),
        "avg_score_policy":         round(_avg([r.score_policy_compliance   for r in ok]), 2),
        "avg_score_tool_use":       round(_avg([r.score_tool_use_accuracy   for r in ok]), 2),
        "policy_hard_gate_pass_rate": (sum(1 for r in ok if r.passed_hard_gate) / n if n else 0),
    }

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    per_row_path = RESULTS_DIR / f"{args.variant}-{stamp}.rows.jsonl"
    summary_path = RESULTS_DIR / f"{args.variant}-{stamp}.summary.json"
    per_row_path.write_text("\n".join(json.dumps(asdict(r), default=str) for r in rows) + "\n")
    summary_path.write_text(json.dumps({
        "variant": args.variant,
        "model": args.model,
        "project_endpoint": args.project_endpoint,
        "agent": args.agent,
        "dataset": args.dataset,
        "expected": args.expected,
        "started_at": started_at,
        "ended_at": ended_at,
        "prices_used_usd_per_1m": PRICES_USD_PER_1M.get(args.model, {}),
        "aggregate": aggregate,
    }, indent=2))

    print()
    print("=" * 60)
    print(f"SUMMARY  variant={args.variant}  model={args.model}")
    print("=" * 60)
    print(f"  ok={n}  errors={len(rows)-n}")
    print(f"  latency avg={aggregate['avg_latency_ms']}ms  p95={aggregate['p95_latency_ms']}ms")
    print(f"  tokens: in={aggregate['sum_tokens_input']:>8}  out={aggregate['sum_tokens_output']:>7}  cached={aggregate['sum_tokens_cached']:>8}")
    print(f"  cost:   total=${aggregate['sum_cost_usd']:.4f}  per-request avg=${aggregate['cost_per_request_usd_avg']:.4f}")
    print(f"  scores: intent={aggregate['avg_score_intent']}/5  policy={aggregate['avg_score_policy']}/5  tool_use={aggregate['avg_score_tool_use']}/5")
    print(f"  policy hard-gate pass rate: {aggregate['policy_hard_gate_pass_rate']*100:.1f}%")
    print()
    print(f"Per-row:  {per_row_path.relative_to(REPO_ROOT)}")
    print(f"Summary:  {summary_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
