# Demo 1 Insights seed

> **What should we improve first when the agent appears to work?** We replay four representative requests, inspect their traces, and use Insights in Foundry to find repeated gaps that should become evaluation criteria.

```text
Seed prompt -> agent trace -> Insights finding -> evaluation case
```

[![Insights in Foundry turns repeated trace patterns into findings](../../../instructions/img/Agent-Insights.png)](../../../instructions/img/Agent-Insights.png)

The baseline agent should remain useful: the hero and simple policy-block scenarios must work. These seed cases check whether policy claims can be traced back to tool output and complete CT-rule citations.

## Files

| File | Purpose |
|---|---|
| [`seed-prompts.jsonl`](seed-prompts.jsonl) | Versioned prompts replayed against the active baseline agent. |
| [`expected-behaviors.jsonl`](expected-behaviors.jsonl) | Tools, rule citations, and visible evidence expected from each case. |

| Case | Behavior under review |
|---|---|
| INS-01 | Multi-city planning and policy checks. |
| INS-02 | Receipt translation and currency conversion. |
| INS-03 | Reimbursable versus personal hotel charges. |
| INS-04 | Accessibility and departure-time constraints. |

For the lightweight recorded path, these same four cases become the comparison dataset for v1-v4. This carries the evidence from Insights directly into evaluation without introducing a larger test suite. Broader 20- and 50-prompt coverage is deferred.

The expected evidence includes three checks we do not want future versions to break:

- policy checks occur before travel options are recommended as compliant;
- rule-level claims are attributable to structured tool evidence;
- reported totals reconcile with itemized fixture values.

Quality uses the same multi-dimensional rubric evaluator for every compared version. Policy checks, latency, and token usage are reported separately and never hidden inside one composite score.

## Reproducibility

A replay must record:

- Git commit and active agent/model/configuration/instruction hash.
- Prompt and expected-behavior file hashes.
- Run start/end timestamps.
- Response and trace IDs in an ignored private delivery log.
- Tools called and attributed CT-rule evidence.
- The generated Insights finding, likely cause, recommendation, and sanitized screenshot.

Insights wording and clustering can vary. The deterministic contract is the underlying prompt, expected evidence, and captured traces, not an exact generated card title.

Follow the replay and analysis steps in the main [`instructions/`](../../../instructions/README.md). Utility [S03](../../../src/scripts/README.md) inspects retained Insights history or starts one reviewed on-demand analysis. Publish only sanitized screenshots and aggregate findings; keep raw response and trace identifiers private.
