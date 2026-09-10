"""Run the Caldova rubric (RUB-001) as an LLM-as-judge evaluator over an
existing baseline result manifest.

Reads a per-row JSONL produced by `src.evaluation.run_baseline` and asks the
judge model (default: `gpt-4.1`) to score each response across the 6 Caldova
rubric dimensions from `data/evaluation/rubric.json`. Policy compliance is a
HARD GATE: a row cannot pass overall if policy < 5.

Writes results next to the input under
`data/evaluation/results/<variant>-<stamp>.rubric.jsonl` and a summary.

Usage:
    python -m src.evaluation.run_rubric \\
        --rows data/evaluation/results/baseline-20260910T073852Z.rows.jsonl \\
        --judge-endpoint https://<foundry-account>.services.ai.azure.com \\
        --judge-deployment gpt-4.1
"""
from __future__ import annotations
import argparse, concurrent.futures, json, os, sys, time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

import httpx
from azure.identity import DefaultAzureCredential

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
EVAL_DIR = DATA_DIR / "evaluation"
RESULTS_DIR = EVAL_DIR / "results"
RUBRIC_PATH = EVAL_DIR / "rubric.json"
EXPECTED_PATH = EVAL_DIR / "expected-behaviors-20.jsonl"

# Judge prompt built once from rubric.json so the demo can point at the same
# rubric file as its source of truth. The judge model returns strict JSON.
JUDGE_SYSTEM = """You are the Caldova rubric evaluator (RUB-001). You score
one Contoso Travel Concierge response at a time across six dimensions.

Score each dimension on the scale 1..5 defined by the rubric:
- 5 = fully satisfies the description of score_5
- 3 = matches score_3
- 1 = matches score_1
- 2 and 4 interpolate between these anchors

Policy compliance is a HARD GATE. If policy_compliance < 5, the row cannot
pass overall.

Return ONLY a JSON object with this exact schema (no prose, no code fences):
{
  "intent_task_completeness":  {"score": <1-5>, "reason": "<one sentence>"},
  "policy_compliance":         {"score": <1-5>, "reason": "<one sentence>"},
  "tool_use_accuracy":         {"score": <1-5>, "reason": "<one sentence>"},
  "travel_plan_correctness":   {"score": <1-5>, "reason": "<one sentence>"},
  "receipt_accuracy":          {"score": <1-5>|null, "reason": "<one sentence or null when N/A>"},
  "communication_clarity":     {"score": <1-5>, "reason": "<one sentence>"},
  "overall_pass": <true|false>,
  "primary_failure_dimension": "<dimension id or null>"
}

Never invent evidence. If a dimension cannot be assessed from the transcript,
score 3 and say why.
"""


def _fmt_rubric(rubric: dict) -> str:
    lines = [f"Rubric name: {rubric['name']}",
             f"Scale: {rubric['scale']['min']}..{rubric['scale']['max']}",
             ""]
    for d in rubric["dimensions"]:
        req = "REQUIRED" if d.get("required") else ("REQUIRED WHEN " + d.get("required_when","")) if d.get("required_when") else "OPTIONAL"
        gate = " (HARD GATE)" if d.get("hard_gate") else ""
        lines.append(f"- {d['id']}: {d['name']} · {req}{gate}")
        lines.append(f"    purpose: {d['purpose']}")
        lines.append(f"    score_5: {d['score_5']}")
        lines.append(f"    score_3: {d['score_3']}")
        lines.append(f"    score_1: {d['score_1']}")
        lines.append("")
    return "\n".join(lines)


def _build_judge_prompt(row: dict, expected: dict, rubric_txt: str) -> str:
    return f"""{rubric_txt}

--- Case ---
id: {row.get('id')}
persona: {row.get('persona')}
attachments: {row.get('attachments')}
user_prompt: >>>
{row.get('prompt')}
<<<

--- Expected behavior (fixture, for reference only) ---
expected_tools:      {expected.get('expected_tools', [])}
must_cite_rules:     {expected.get('must_cite_rules', [])}
policy_outcomes:     {expected.get('policy_outcomes', {})}

--- Agent response ---
model:               {row.get('model')}
variant:             {row.get('variant')}
tools_called:        {row.get('tools_called', [])}
cited_rule_ids:      {row.get('cited_rule_ids', [])}
hard_gate_blocked:   {row.get('hard_gate_blocked', False)}
tokens_input/output: {row.get('tokens_input',0)} / {row.get('tokens_output',0)}
assistant_text: >>>
{row.get('assistant_head','')[:4000]}
<<<
"""


@dataclass
class RubricRow:
    id: str
    persona: str
    variant: str
    model: str
    judge_model: str
    intent_task_completeness: dict | None = None
    policy_compliance: dict | None = None
    tool_use_accuracy: dict | None = None
    travel_plan_correctness: dict | None = None
    receipt_accuracy: dict | None = None
    communication_clarity: dict | None = None
    overall_pass: bool = False
    primary_failure_dimension: str | None = None
    quality_average: float = 0.0
    raw_judge_output: str = ""
    error: str | None = None


def _score_one(row: dict, expected: dict, rubric_txt: str, judge_endpoint: str,
               judge_deployment: str, credential: DefaultAzureCredential) -> RubricRow:
    rr = RubricRow(
        id=row["id"], persona=row.get("persona", ""),
        variant=row.get("variant", "baseline"), model=row.get("model", ""),
        judge_model=judge_deployment,
    )
    try:
        token = credential.get_token("https://cognitiveservices.azure.com/.default").token
        url = (
            judge_endpoint.rstrip("/") +
            f"/openai/deployments/{judge_deployment}/chat/completions?api-version=2025-04-01-preview"
        )
        prompt = _build_judge_prompt(row, expected, rubric_txt)
        with httpx.Client(timeout=180.0) as client:
            r = client.post(url,
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "messages": [
                        {"role": "system", "content": JUDGE_SYSTEM},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.0,
                    "response_format": {"type": "json_object"},
                    "max_tokens": 1200,
                })
        if r.status_code >= 400:
            rr.error = f"HTTP {r.status_code}: {r.text[:200]}"
            return rr
        raw = r.json()["choices"][0]["message"]["content"]
        rr.raw_judge_output = raw
        parsed = json.loads(raw)
        for k in ("intent_task_completeness", "policy_compliance",
                 "tool_use_accuracy", "travel_plan_correctness",
                 "receipt_accuracy", "communication_clarity"):
            setattr(rr, k, parsed.get(k))
        rr.overall_pass = bool(parsed.get("overall_pass", False))
        rr.primary_failure_dimension = parsed.get("primary_failure_dimension")
        # Compute quality average (excludes receipt when N/A)
        scores = []
        for k in ("intent_task_completeness", "policy_compliance",
                 "tool_use_accuracy", "travel_plan_correctness",
                 "receipt_accuracy", "communication_clarity"):
            v = getattr(rr, k)
            if v and isinstance(v.get("score"), (int, float)):
                scores.append(v["score"])
        rr.quality_average = round(sum(scores) / len(scores), 2) if scores else 0.0
    except Exception as e:
        rr.error = f"{type(e).__name__}: {e}"
    return rr


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rows", required=True, help="Per-row JSONL from run_baseline")
    ap.add_argument("--rubric", default=str(RUBRIC_PATH))
    ap.add_argument("--expected", default=str(EXPECTED_PATH))
    ap.add_argument("--judge-endpoint", required=True,
                    help="Foundry AI account base endpoint (…services.ai.azure.com)")
    ap.add_argument("--judge-deployment", default="gpt-4.1")
    ap.add_argument("--parallel", type=int, default=5)
    ap.add_argument("--variant", default="baseline")
    args = ap.parse_args(argv)

    rubric = json.loads(Path(args.rubric).read_text())
    rubric_txt = _fmt_rubric(rubric)
    expected_all = {r["id"]: r
                    for r in (json.loads(l) for l in Path(args.expected).read_text().splitlines() if l.strip())}
    rows = [json.loads(l) for l in Path(args.rows).read_text().splitlines() if l.strip()]

    print(f"Rows to score:   {len(rows)}")
    print(f"Judge model:     {args.judge_deployment}")
    print(f"Judge endpoint:  {args.judge_endpoint}")
    print(f"Rubric:          {rubric['id']} / {rubric['name']}")

    credential = DefaultAzureCredential()
    started = time.time()
    scored: list[RubricRow] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.parallel) as pool:
        futs = {
            pool.submit(_score_one, r, expected_all.get(r["id"], {}), rubric_txt,
                        args.judge_endpoint, args.judge_deployment, credential): r
            for r in rows
        }
        for i, fut in enumerate(concurrent.futures.as_completed(futs), 1):
            rr = fut.result()
            scored.append(rr)
            m = "PASS" if rr.overall_pass else ("ERR" if rr.error else "FAIL")
            print(f"  [{i:>2}/{len(rows)}] {rr.id:<6} {m:<4} "
                  f"policy={rr.policy_compliance and rr.policy_compliance.get('score')} "
                  f"intent={rr.intent_task_completeness and rr.intent_task_completeness.get('score')} "
                  f"quality_avg={rr.quality_average} "
                  f"fail_dim={rr.primary_failure_dimension or '-'}")
            if rr.error:
                print(f"          err: {rr.error[:200]}")

    scored.sort(key=lambda r: r.id)
    elapsed = int(time.time() - started)

    # Aggregate
    ok = [r for r in scored if not r.error]
    n = len(ok)
    def _avg(k): return round(sum((getattr(r, k) or {}).get("score", 0) or 0 for r in ok) / n, 2) if n else 0
    aggregate = {
        "row_count": len(scored),
        "row_count_ok": n,
        "row_count_errors": len(scored) - n,
        "pass_rate": round(sum(1 for r in ok if r.overall_pass) / n, 3) if n else 0,
        "avg_intent":         _avg("intent_task_completeness"),
        "avg_policy":         _avg("policy_compliance"),
        "avg_tool_use":       _avg("tool_use_accuracy"),
        "avg_travel_plan":    _avg("travel_plan_correctness"),
        "avg_receipt":        (
            round(sum((r.receipt_accuracy or {}).get("score", 0) or 0 for r in ok
                       if r.receipt_accuracy and isinstance(r.receipt_accuracy.get("score"), (int,float))) /
                  max(1, sum(1 for r in ok if r.receipt_accuracy and isinstance(r.receipt_accuracy.get("score"), (int,float)))),
                  2)
        ),
        "avg_communication":  _avg("communication_clarity"),
        "avg_quality_overall": round(sum(r.quality_average for r in ok) / n, 2) if n else 0,
        "elapsed_sec": elapsed,
    }

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    per_row_path = RESULTS_DIR / f"{args.variant}-{stamp}.rubric.jsonl"
    summary_path = RESULTS_DIR / f"{args.variant}-{stamp}.rubric.summary.json"
    per_row_path.write_text("\n".join(json.dumps(asdict(r)) for r in scored) + "\n")
    summary_path.write_text(json.dumps({
        "variant": args.variant,
        "rubric": rubric["id"],
        "judge_endpoint": args.judge_endpoint,
        "judge_deployment": args.judge_deployment,
        "input_rows": args.rows,
        "aggregate": aggregate,
        "ended_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }, indent=2))

    # Highlight one representative failure
    failing = [r for r in scored if not r.error and not r.overall_pass]
    print()
    print("=" * 68)
    print(f"RUBRIC SUMMARY  variant={args.variant}  judge={args.judge_deployment}")
    print("=" * 68)
    print(f"  pass rate:            {aggregate['pass_rate']*100:.1f}%  ({sum(1 for r in ok if r.overall_pass)}/{n})")
    print(f"  policy (hard gate):   {aggregate['avg_policy']}/5")
    print(f"  intent:               {aggregate['avg_intent']}/5")
    print(f"  tool_use:             {aggregate['avg_tool_use']}/5")
    print(f"  travel_plan:          {aggregate['avg_travel_plan']}/5")
    print(f"  receipt:              {aggregate['avg_receipt']}/5")
    print(f"  communication:        {aggregate['avg_communication']}/5")
    print(f"  overall quality avg:  {aggregate['avg_quality_overall']}/5")
    print()
    if failing:
        rep = sorted(failing, key=lambda r: r.quality_average)[0]
        print(f"REPRESENTATIVE FAILURE — {rep.id}")
        for d in ("intent_task_completeness","policy_compliance","tool_use_accuracy",
                 "travel_plan_correctness","receipt_accuracy","communication_clarity"):
            v = getattr(rep, d)
            if v is not None:
                print(f"  {d:<25} {v.get('score')} — {v.get('reason','')[:180]}")
        print(f"  overall pass:           {rep.overall_pass}")
        print(f"  primary failure dim:    {rep.primary_failure_dimension}")
    print()
    print(f"Per-row:  {per_row_path.relative_to(REPO_ROOT)}")
    print(f"Summary:  {summary_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
