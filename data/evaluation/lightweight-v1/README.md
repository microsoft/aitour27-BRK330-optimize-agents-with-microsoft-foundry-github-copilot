# Lightweight evaluation contract v1

This four-case dataset continues directly from the Demo 1 Agent Insights evidence. It is frozen for baseline v1, Model Router v2, trace-response student v3, and curated-response student v4 comparisons. Agent Optimizer can reuse it as bounded development input, but its internal rankings are not added to the v1-v4 comparison scorecard.

## Frozen inputs

- `dataset-v1.jsonl` is the original rubric-generation source retained for provenance.
- `dataset-v2.jsonl` is the runnable Dev Pack holdout from fine-tuning with required task `name`, `query`, and `expected_behavior` fields. It remains unseen for the measured v1-v4 comparison.
- `rubric-source.json` defines the approved quality dimensions, hard gates, pass threshold, and separate operational metrics.
- The judge deployment for rubric evaluation remains `gpt-5.4-mini` unless the pinned remote evaluator records a different reviewed choice.
- The reviewed evaluator v1 uses normalized pass threshold `0.5`, corresponding to midpoint score 3 on the rubric source's 1-5 scale.

## Insights continuity

The contract directly measures the two observed v1 findings:

1. Policy checks must occur before recommendations.
2. Itemized and reported totals must agree.

It also prevents a related baseline behavior: naming CT rules that are not attributable to structured tool output.

## Freeze rule

After the remote rubric evaluator is reviewed and versioned, record its name, version, judge deployment, dataset name/version, and hashes here or in the agent's `.foundry` metadata. Do not change the dataset, expected behavior, rubric dimensions, or threshold between v1-v4. A change creates a new evaluation contract and requires rerunning every compared version.

The lightweight path can give Agent Optimizer these same four rows to keep candidate generation bounded. Treat its ranking as a search signal only. Production use should optimize on a development split and promote only after a separate final holdout passes.

## Attendee setup

From the repository root, validate locally first:

```bash
python src/scripts/setup_lightweight_evaluation.py
```

Then register runnable dataset v2 and generate or reuse the retained rubric evaluator:

```bash
python src/scripts/setup_lightweight_evaluation.py --apply
```

Apply mode never deletes datasets, evaluators, jobs, or agents. It reuses the frozen names when present and saves the returned evaluator definition under `src/agent/.foundry/evaluators/` for human review before baseline scoring.

## Pinned remote contract

- Dataset: `brk330-lightweight-eval` v2
- Dataset SHA256: `5a6808f03ffce76dcf87366ff489793920324127c7d09e118c43f7249cff2699`
- Evaluator: `brk330-contoso-travel-quality` v1
- Rubric source SHA256: `f937a04d86ec75a1eb7f845266f5b23595dea22f3600a214078c6b13768b5995`
- Judge: `gpt-5.4-mini`
- Normalized threshold: `0.5`
- Generation job: `evaluatorgen-brk330-contoso-travel-quality-v1-091df611`

The exact remote references and service-returned definition are cached under `src/agent/.foundry/`. This pin applies unchanged to v1-v4 comparisons.

## Baseline v1 result

The complete retry run `evalrun_d518cfe6064d4d51ba6be97b4c211a60` scored all four rows with no evaluator errors:

| Case | Score | Result | Baseline finding |
| --- | ---: | --- | --- |
| INS-01 | 0.325 | Fail | The itinerary surfaced FL-004 without a clearly prior policy check and did not fully show arithmetic reconciliation. |
| INS-02 | 0.770 | Pass | Receipt facts, EUR-to-USD conversion, and policy evidence remained grounded and consistent. |
| INS-03 | 0.905 | Pass | Receipt classification, evidence, and reimbursable/non-reimbursable totals were exact. |
| INS-04 | 0.400 | Fail | The agent correctly refused the impossible complete trip but weakly framed hotel and car options as independently compliant. |

The baseline pass rate is 2/4 and its mean rubric score is 0.600. The earlier partial run remains operational evidence of judge throttling but is not combined with this result.

Evaluator v1 marked the receipt-only dimension applicable to INS-01 even though that case contains no receipt task. Preserve and disclose this behavior for every v1-v4 comparison; changing applicability now would create a new evaluation contract.

Quality, latency, evaluated-agent token usage, and the reproducible cost method are recorded in the [evaluation comparison scorecard](comparison-scorecard.md).