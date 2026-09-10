# Built-in evaluator progression — baseline → routed → student → optimizer

*The hill-climb dashboard for the recording. One row per agent variant,
one column per metric. All variants scored on the **same** fixed 20-prompt
subset (`src/agent/tests/queries.jsonl`) using the same three built-in
Foundry evaluators (`caldova-composed-eval`) and, when available, the
custom rubric (`caldova-agent-rubric-eval`).*

Update this file after each Foundry `azd ai agent eval run` completes.
Round to one decimal place for portal-visible scores; keep the raw report
URL alongside for provenance.

## Score-card

| Variant | Version | Intent resolution | Task adherence | Tool-call accuracy | Rubric weighted | Latency avg | Cost / request |
|---|---|---:|---:|---:|---:|---:|---:|
| **Baseline (frontier `gpt-5`)** | v6 | **12 / 20 pass** (8 err) | 12 / 20 pass (8 err) | 0 / 20 pass (14 err — reasoning SDK bug) | pending | ~44.5 s | $0.0313 |
| **Routed (`model-router`)** | ~~v7~~ | ~~discarded (empty responses, monkey-patch bug)~~ | | | | | |
| **Routed (`model-router`)** | v8 | pending (azd eval running) | pending | pending | pending | **24.1 s** (−46%) | **$0.0025** (−92%, blended Router estimate) |
| **Trained student** | — | pending — Session 2 P10–P12 | | | | | |
| **Optimizer-promoted candidate** | — | pending — Session 3 P13–P15 | | | | | |

Notes on rendering: `intent_resolution`, `task_adherence`,
`tool_call_accuracy` are the three built-ins from
`caldova-composed-eval`; the **Rubric weighted** column is the overall
score from `caldova-agent-rubric-eval` (weighted-average across seven
dimensions, pass threshold `0.75`).

## Report URLs (provenance)

| Variant | Version | azd eval run | Foundry portal report |
|---|---|---|---|
| Baseline | v6 | `evalrun_56c66cfbf5274d6e8993a9d8554bba50` | <https://ai.azure.com/nextgen/r/eogHKHDTSdCt3kJQcWz9lA,rg-brk330-concierge,,cog-hqxztqzboq4bq,brk330-concierge-project/build/evaluations/eval_e252fb33291b4267b1a55b7a3a8a94d9/run/evalrun_56c66cfbf5274d6e8993a9d8554bba50> |
| Routed | v8 | `evalrun_eaf07331100e4dbc885ae673860abdf3` | <https://ai.azure.com/nextgen/r/eogHKHDTSdCt3kJQcWz9lA,rg-brk330-concierge,,cog-hqxztqzboq4bq,brk330-concierge-project/build/evaluations/eval_e252fb33291b4267b1a55b7a3a8a94d9/run/evalrun_eaf07331100e4dbc885ae673860abdf3> |
| Trained student | — | pending | pending |
| Optimizer-promoted candidate | — | pending | pending |

## Local metric manifests (latency / tokens / cost)

| Variant | Version | rows.jsonl | summary.json |
|---|---|---|---|
| Baseline | v6 | `data/evaluation/results/baseline-20260910T073852Z.rows.jsonl` | `data/evaluation/results/baseline-20260910T073852Z.summary.json` |
| Routed | ~~v7~~ | ~~`routed-20260910T092427Z.rows.jsonl` — discarded, `0 tokens` per row from monkey-patch bug~~ | ~~`routed-20260910T092427Z.summary.json`~~ |
| Routed | v8 | `data/evaluation/results/routed-20260910T093142Z.rows.jsonl` | `data/evaluation/results/routed-20260910T093142Z.summary.json` |

### v8 routed vs v6 baseline — head-to-head (local metrics)

Router pricing is a passthrough — the deployment itself is $0/token; the
underlying model billed depends on which one Router selects per call.
For the presenter deck we use a **blended estimate** that assumes
Router picks `gpt-5` 20 % of calls (final compose + hard reasoning),
`gpt-5-mini` 50 %, `gpt-5-nano` 30 %. Blended prices per 1M tokens:
`input=$0.640`, `output=$2.560`, `cached=$0.064`. Fine-tune the blend
with real per-call route telemetry from Application Insights before
recording final slide numbers.

**Legend:** 🟢 moved in the good direction · 🔴 moved in the bad
direction · ⚪ flat. Arrow follows the raw value; colour follows whether
that direction is favourable for this metric.

| Metric | Baseline v6 | Routed v8 | Delta | |
|---|---:|---:|---:|:--:|
| Rows OK | 20 | 20 | — | ⚪ |
| Avg latency | 44.5 s | 24.1 s | **−46 %** | 🟢 ⬇ |
| p95 latency | 69.5 s | 45.2 s | −35 % | 🟢 ⬇ |
| Total tokens | 134 286 | 70 782 | −47 % | 🟢 ⬇ |
| Output tokens | 55 434 | 17 132 | −69 % | 🟢 ⬇ |
| **Cost / trip** *(blended)* | $0.0313 | $0.0025 | **−92 %** | 🟢 ⬇ |
| Intent /5 (mechanical) | 3.10 | 3.00 | −3 % | 🔴 ⬇ |
| Policy /5 (mechanical) | 2.20 | 2.20 | 0 % | ⚪ |
| Tool-use /5 (mechanical) | 3.10 | 3.00 | −3 % | 🔴 ⬇ |
| **Hard-gate pass rate** | 95 % | 95 % | 0 % | ⚪ |

Reading the delta: quality holds within noise (~3 % dip on intent and
tool-use, policy pass-rate unchanged), while latency and cost drop
dramatically. That's the classic hill-climb win — the Ferrari really
was doing bike jobs. Wait for Foundry rubric scores before locking a
winner, per spec.

## Known failure modes to guard against on future variants

- **`Invalid content type 'reasoning'`** on `tool_call_accuracy` and
  sometimes `intent_resolution` / `task_adherence`. Root cause: gpt-5
  reasoning content emitted in assistant messages. Fix applied in v6:
  `default_options={"reasoning": {"summary": None}, "include": []}` in
  `src/agent/main.py`. Still leaked on `tool_call_accuracy` for v6 (14
  errors); worth re-testing on v8 to see whether the routed variant
  (`model-router` selecting non-reasoning models per call) reduces
  leakage.
- **Version pinning matters.** Set `agent.version: "<n>"` in
  `src/agent/eval.yaml` before every eval so runs are comparable.
- **Empty responses** — v7 taught us: any monkey-patch or middleware on
  `Agent.run` must exactly match Foundry's calling convention. If a
  variant returns 0 tokens across the board, look at container logs
  before running any evaluator.

## What each stage of the hill climb changes

- **Baseline → Routed** (this cycle): worker model swap from `gpt-5` to
  `model-router`; enriched instructions in `main.py` force explicit
  decomposition on the first turn. No fine-tune, no promotion.
- **Routed → Trained student**: trace-derived training dataset built
  from routed traces + baseline gold traces, fine-tune of a
  catalog-verified smaller student model, re-evaluate on the same 20
  prompts.
- **Trained student → Optimizer-promoted candidate**: Agent Optimizer
  portal run using the same rubric and dataset; human review before
  promotion.
