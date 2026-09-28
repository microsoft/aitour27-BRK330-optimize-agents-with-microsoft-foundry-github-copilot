# Demo 1 Insights seed

Four fixed, policy-sensitive scenarios used to create production-like traces for the **Observe** and **Understand** stages of the session.

The baseline agent should remain useful: the hero and simple policy-block scenarios must work. These seed cases probe whether policy claims are consistently attributable to tool output and complete CT-rule citations.

## Files

| File | Purpose |
|---|---|
| `seed-prompts.jsonl` | Versioned prompts replayed against the active baseline agent. |
| `expected-behaviors.jsonl` | Required tools, rule citations, and observable outcomes. |

For the lightweight recorded path, these same four cases are the frozen comparison dataset for v1-v4. This deliberately continues the narrative from Insights into evaluation without introducing a larger test suite. Broader 20- and 50-prompt coverage is deferred.

The expected behavior contract includes three Insights-derived regression gates:

- policy checks occur before travel options are recommended as compliant;
- rule-level claims are attributable to structured tool evidence;
- reported totals reconcile with itemized fixture values.

Quality uses one frozen rubric evaluator. Policy gates, latency, and token usage are reported separately and never hidden inside a composite score.

## Reproducibility

A replay must record:

- Git commit and active agent/model/configuration/instruction hash.
- Prompt and expected-behavior file hashes.
- Run start/end timestamps.
- Response and trace IDs.
- Tools called and attributed CT-rule evidence.
- The generated Insights finding, likely cause, recommendation, and screenshot.

Insights wording and clustering can vary. The deterministic contract is the underlying prompt, expected evidence, and captured traces, not an exact generated card title.
