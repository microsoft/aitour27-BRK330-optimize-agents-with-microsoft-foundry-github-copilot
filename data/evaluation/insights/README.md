# Demo 1 Insights seed

Four fixed, policy-sensitive scenarios used to create production-like traces for the **Observe** and **Understand** stages of the session.

The baseline agent should remain useful: the hero and simple policy-block scenarios must work. These seed cases probe whether policy claims are consistently attributable to tool output and complete CT-rule citations.

## Files

| File | Purpose |
|---|---|
| `seed-prompts.jsonl` | Versioned prompts replayed against the active baseline agent. |
| `expected-behaviors.jsonl` | Required tools, rule citations, and observable outcomes. |

The fixed 20-prompt comparison dataset used in later demos is separate and must not be modified to tune these findings.

## Reproducibility

A replay must record:

- Git commit and active agent/model/configuration/instruction hash.
- Prompt and expected-behavior file hashes.
- Run start/end timestamps.
- Response and trace IDs.
- Tools called and attributed CT-rule evidence.
- The generated Insights finding, likely cause, recommendation, and screenshot.

Insights wording and clustering can vary. The deterministic contract is the underlying prompt, expected evidence, and captured traces, not an exact generated card title.
