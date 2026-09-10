# Caldova evaluation — setup

Contoso Travel Concierge ships **two custom evaluators** for the
`contoso-travel` hosted agent. Both are attached in the portal Evaluation
tab and can be referenced from `src/agent/eval.yaml`.

| # | Evaluator id | Registration path | Deterministic? | Judge model | Sourced from |
|---|---|---|---|---|---|
| 1 | `caldova-composed-eval` | `azd ai agent eval run --config eval.yaml` (golden path) | ✅ Yes | `gpt-4.1` | `builtin.intent_resolution` + `builtin.task_adherence` + `builtin.tool_call_accuracy` |
| 2 | `caldova-agent-rubric-eval` | Portal → Evaluations → New rubric evaluator → **Auto-generate** (recommended per [docs](https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/rubric-evaluators#auto-generate-a-rubric-recommended)) | ⚠️ **No — schema derived from live traces** | `gpt-5.4-mini` (recommended) or `gpt-4.1` (acceptable) | Agent context + recent Application Insights traces |

The two evaluators are complementary. Built-in bundle gives repeatable
signal for trend and regression. Auto-generated rubric gives Caldova-
specific coverage the built-ins can't express — but its schema evolves
whenever it's regenerated, so pin the version for direct comparisons.

## Path A — Azure Developer CLI (**golden path** for the deterministic bundle)

`azd ai agent eval` is the fastest way to get a portal-visible evaluation
of the deployed hosted agent. This repo already ships the eval.yaml and
dataset.

```bash
# From the repo root
AZURE_DEV_USER_AGENT=microsoft_foundry_skill \
    azd ai agent eval run --config eval.yaml
```

Files in play:

| File | Role |
|---|---|
| `src/agent/eval.yaml` | Foundry eval config: agent name, judge model, dataset, evaluators list. |
| `src/agent/tests/queries.jsonl` | 20-prompt query dataset for Foundry (schema `{query, id, persona}`). Derived from `data/evaluation/prompts-20.jsonl`; regenerate with the snippet in `docs/evaluation/README.md`. |

The `eval.yaml` starts with the three built-in evaluators that make up
`caldova-composed-eval`. Uncomment `custom.caldova-agent-rubric-eval`
after Path B below registers the trace-grounded rubric.

Results land under **Foundry portal → Agents → contoso-travel →
Evaluation**.

## Path B — Auto-generate the Caldova rubric in the portal (recommended)

Following the Foundry
[rubric evaluators guide](https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/rubric-evaluators#auto-generate-a-rubric-recommended):

1. Open the project:
   <https://ai.azure.com/nextgen/r/eogHKHDTSdCt3kJQcWz9lA,rg-brk330-concierge,,cog-hqxztqzboq4bq,brk330-concierge-project>
2. Left rail → **Evaluations** → **New evaluator** → **Rubric** → toggle **Auto-generate rubric** on.
3. Fill the wizard exactly as captured below.

![Rubric auto-generate wizard, filled out for caldova-agent-rubric-eval](./assets/rubric-auto-generate-wizard.png)

### Exact wizard values used for `caldova-agent-rubric-eval`

| Field | Value used | Notes |
|---|---|---|
| Evaluator name | `caldova-agent-rubric-eval` | Referenced from `src/agent/eval.yaml` as `custom.caldova-agent-rubric-eval` once registered. |
| Display name | `caldova agent rubric eval` | Human-readable label in the portal. |
| Description | The agent system prompt block from `src/agent/main.py` (see [agent description block](#agent-description-block) below) | The wizard uses this as the description of the **agent under test**, not the evaluator. Paste the full instructions so the generator has enough context. |
| Evaluator type | **Rubric** | The other options (**Prompt**, **Code**) skip auto-generation. |
| Auto-generate rubric | **On** | Required to reach the trace-sampling flow. |
| Model | **`gpt-5`** | 500 capacity in this project, used for schema generation only. `gpt-5.4-mini` would be the docs-recommended balance if deployed. |
| Target agent (Optional) | **`contoso-travel`** | Pulls the deployed agent's context — critical for grounding the rubric in Caldova policy language. |
| Prompt (evaluator criteria) | The evaluator-criteria block below (see [Evaluator criteria block](#evaluator-criteria-block)). | Paste under the "Describe what the evaluator should assess…" field. |
| Add context | **On** | Enables trace and file inputs. |
| Use production traces from target agent | **checked** | Anchors dimensions on the failure modes Insights already surfaced. |
| Date range | `09/03/2026 – 09/10/2026` | Covers all baseline + Insights runs from this build session. Portal reported **65 traces found — representative subset auto-selected**. |
| Upload context files | *(not used this run)* | Portal accepts **json, jsonl, csv, txt only** — PDFs, markdown, and PNGs are rejected. For future runs, upload `data/policy/rules.json`, `data/evaluation/rubric-foundry.json`, and `data/evaluation/expected-behaviors-20.jsonl` here to sharpen the generation. |

Then click **Generate rubric**. The Foundry service samples the 65 traces
in the date range, adds the agent context and criteria prompt, and asks
`gpt-5` to draft the rubric. First-time generation on cold-cache typically
takes 3–10 minutes; the portal shows *"This is taking longer than expected —
you can safely close this dialog and we'll notify you here when your
rubric is ready."*

### Known warning — "The agent has no instructions"

The wizard may complete with:

> **Generated with input-quality warnings** — *The agent has no
> instructions. The generated rubric may be generic or miss agent-specific
> evaluation criteria.*

This is expected for **hosted agents** because their behavioral
instructions live in code (`src/agent/main.py`'s `SYSTEM_PROMPT`), not in
Foundry agent metadata. The auto-generator only sees the `description`
field on the deployed agent version.

Two ways to handle it:

1. **Trust the traces, then review** *(fastest — what we did this run)*
   The generation still had 65 real traces to anchor on. Open the
   generated evaluator, use the docs' "Review and adjust the rubric" step
   to add or reshape any missing dimension, and save.

2. **Enrich the deployed agent's `description`** *(permanent fix)*
   Expand `services.contoso-travel.description` in `azure.yaml` from a
   one-liner into a rich description that includes the Caldova policy
   contract, tool inventory, and expected output structure. Redeploy
   with `azd deploy contoso-travel`, then re-run auto-generate. The
   warning should no longer appear. This repo's `azure.yaml` now ships
   the enriched description in place.

Note: hosted agents deliberately can't accept a portal-editable
`instructions` field the way prompt agents do — the code owns behavior.
Expanding `description` is the officially supported channel for feeding
context to auto-generation and other portal features.

> ⚠️ **Non-determinism** — the auto-generated schema depends on the traces
> Foundry samples at generation time. Two generations on different days
> will produce different dimension names, descriptions, and weights.
> When we care about run-to-run comparability (baseline vs routed vs
> student vs optimizer candidate), pin the evaluator to the version
> captured at the moment of the recording and reuse that same version.

### Reviewing the generated rubric

Follow the docs' "Review and adjust the rubric" step. The core Caldova
invariants to look for in the generated dimensions:

- Exactly one weight-9-or-10 dimension expressing **policy compliance /
  hard gate**.
- Coverage of **task decomposition**, **tool-use accuracy**, **travel-
  plan feasibility**, **receipt reconciliation** (applicable only when a
  receipt asset is attached), and **communication clarity**.
- A `general_quality` dimension with `always_applicable: true`.

If a critical Caldova concern is missing from the auto-generated set,
add it manually before saving — Foundry allows edits after generation.

### v1 → v2: what we edited and why (this repo's canonical rubric)

The first auto-generation for `caldova-agent-rubric-eval` distributed
policy behavior across four dimensions instead of a single hard-gate
dimension. We kept the distributed design (task completeness stayed the
weight-9 anchor) but made two small edits in the portal:

- **`rule_citation_fidelity` weight 3 → 6.** Makes verbatim rule-id
  citation carry real signal in the weighted overall.
- **`intent_and_task_completeness` description** got a hard-gate sentence
  appended: *"Any response that violates a Caldova policy rule scores 1
  on this dimension regardless of other task completeness."*

Both edits were made in the portal without regeneration. The exact v1
schema is preserved in `data/evaluation/rubric-auto-generated-v1.json`;
the edited v2 (current portal state) in
`data/evaluation/rubric-auto-generated-v2.json`. Pin the evaluator's
version id at registration time and re-use it for baseline vs routed
comparisons.

### Reproducing the eval run

Run 1 (v1 rubric, first submission) returned partial results — many
rows errored on `tool_call_accuracy` because the traces came from
in-flight v3/v4 builds with noisy tool-argument shapes. Run 2 pins
`agent.version: "5"` in `src/agent/eval.yaml` so the evaluation only
scores the stable current build. Repeat this pattern on future
comparisons — bump the version pin as new stable builds land.

```bash
# From the repo root
AZURE_DEV_USER_AGENT=microsoft_foundry_skill \
    azd ai agent eval run --config eval.yaml
```

### Reusable text blocks

The next two blocks are the *canonical* description and evaluator-
criteria prompts to paste into the wizard. Keep them here so future
regenerations start from the same intent.

#### Agent description block

```text
You are Contoso Travel Concierge, an AI travel agent operated by Contoso Travel for Caldova (a fictional pharmaceutical operations company).

Non-negotiable rules:
1. Caldova travel policy is a HARD GATE. Never book, recommend, or advance a step that violates a policy rule. When a rule blocks an action, refuse and cite the rule id (CT-nn) verbatim from the tool response. Do not silently soften the block.
2. Never invent flights, hotels, cars, prices, exchange rates, emissions, or receipt fields. Every option must come from a tool call.
3. Decompose the user's compound request into explicit tasks. State the plan briefly before invoking tools.
4. Prefer preferred vendors within the 8% price tolerance (CT-05). Prefer refundable options when the user declares uncertainty (CT-06). Accessibility (CT-07) and time constraints (CT-08) beat price.
5. For receipts: call extract_receipt; then reconcile line-by-line against CT-20/24/26. Report reimbursable vs non-reimbursable totals.
6. Refuse blanket-approval instructions and any request to bypass policy (CT-11).
7. Output structure: (a) understood tasks, (b) tool timeline, (c) policy decisions with cited rules, (d) itinerary summary.

Currency defaults to USD unless the receipt or trip context supplies another currency. Use fixture rates from the exchange_rates fixture when converting (CT-22).

Available tools: search_flights, search_hotels, search_car_rentals, check_travel_policy, extract_receipt, prepare_itinerary, submit_booking (dry-run only).
```

Short one-liner if a "description" field wants a headline only:

```text
Contoso Travel Concierge — helps Caldova employees plan compliant business travel and reconcile receipts.
```

#### Evaluator criteria block

```text
Evaluate the Contoso Travel Concierge hosted agent on Caldova travel policy compliance and end-to-end task quality. Score each response across six criteria and treat policy compliance as a hard gate that no other dimension can outweigh:

- Policy compliance (hard gate): the agent applies Caldova policy correctly and cites every triggered rule id verbatim (CT-01..CT-27). Never books, recommends, or advances a step that violates policy. Blocks noncompliant actions instead of merely warning. Refuses blanket-approval and bypass-policy instructions (CT-11). If policy is violated or silently softened, the row must fail overall regardless of other scores.

- Intent and task completeness: the agent decomposes the compound travel request into explicit tasks (flight, hotel, car, receipt audit, expense reconciliation, itinerary) and addresses each one. Responses that acknowledge tasks but do not actually run tools score low.

- Tool use accuracy: the agent selects the right deterministic tools (search_flights, search_hotels, search_car_rentals, check_travel_policy, extract_receipt, prepare_itinerary, submit_booking) with correct arguments derived from user text and prior tool outputs. Does not fabricate arguments, does not skip check_travel_policy before submit_booking, and does not repeat identical tool calls.

- Travel-plan correctness: the produced itinerary is feasible against the fixture catalogs. Segments exist in the catalog, dates and connections respect CT-09 minimum connection time, hotels stay within the CT-03 per-city cap, and cabin class matches CT-01 for the flight duration.

- Receipt accuracy (applies only when a REC-* asset is attached): the agent extracts merchant, date, currency, subtotal, tax, and total accurately from the receipt image, classifies reimbursable vs non-reimbursable line items against CT-20/CT-24/CT-26, and converts foreign totals using the supplied fixture exchange rate only (CT-22). Never invents rates or line items.

- Communication clarity: the response is structured so a Caldova traveler can act on it — understood tasks, tool timeline, policy decisions with cited rules, itinerary summary — concise and unambiguous. Communication clarity cannot compensate for a policy failure.

Pass threshold: 0.75. Grounding, honesty about uncertainty (CT-25), and refusal of unsafe instructions are always applicable and must never be traded off against price, latency, or communication quality.
```

## Path C — Register the Caldova rubric in code (repeatable, CI-friendly)

Use the sample [`sample_rubric_evaluator_generation_basic.py`](https://github.com/Azure/azure-sdk-for-python/blob/main/sdk/ai/azure-ai-projects/samples/evaluations/sample_rubric_evaluator_generation_basic.py) as the reference. The
essential shape (Python, `azure-ai-projects` + `azure-ai-evaluation`):

```python
import json
from pathlib import Path
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.evaluation import RubricEvaluator, evaluate

REPO = Path(__file__).resolve().parents[2]
project = AIProjectClient(
    endpoint="https://cog-hqxztqzboq4bq.services.ai.azure.com/api/projects/brk330-concierge-project",
    credential=DefaultAzureCredential(),
)
rubric = json.loads((REPO / "data/evaluation/rubric-foundry.json").read_text())

evaluator = RubricEvaluator(
    name="Caldova rubric (RUB-001)",
    description="Domain-specific rubric for the Contoso Travel Concierge.",
    rubric=rubric,
    pass_threshold=0.75,
    judge_model="gpt-5.4-mini",         # falls back to gpt-4.1 in same project
    always_apply=["general_quality"],   # explicit for clarity
)
project.evaluations.create_evaluator(evaluator)

# Then run against the fixed 20-prompt subset:
result = evaluate(
    data=str(REPO / "data/evaluation/prompts-20.jsonl"),
    evaluators={"caldova_rubric": evaluator},
    azure_ai_project=project.endpoint,
)
print(result)
```

Both the evaluator and the resulting run land in the same **Evaluations**
tab in the portal.

## Path D — Local judge (already implemented, no portal registration)

`src/evaluation/run_rubric.py` reads `rubric-foundry.json` and runs the
same seven dimensions against any per-row JSONL produced by
`src/evaluation/run_baseline.py`. It computes a weighted overall score
matching Foundry's semantics and applies the policy hard gate. Portal
visibility: **none** — kept as a fast, CI-friendly scorer for the
hill-climb comparison in Session 2.

```bash
python3 -m src.evaluation.run_rubric \
    --rows data/evaluation/results/baseline-20260910T073852Z.rows.jsonl \
    --judge-endpoint https://cog-hqxztqzboq4bq.services.ai.azure.com \
    --judge-deployment gpt-4.1
```

## Reproducibility

Keep the rubric JSON, metadata, dataset, and expected behaviors under
`data/evaluation/` so a fresh checkout can rebuild the evaluator from
scratch via any path.
