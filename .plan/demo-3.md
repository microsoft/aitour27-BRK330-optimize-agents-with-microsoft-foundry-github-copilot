# Demo 3: Automate with Agent Optimizer

## Act

Act 4 — Make it easier: Let's automate — Agent Optimizer

## Audience outcome

Agent Optimizer automates repetitive candidate generation and comparison using
trusted evidence, while the engineer retains control of promotion.

## Pre-recording state

- Python hosted agent is optimization-ready.
- Baseline configuration is immutable.
- Evaluation configuration references the fixed 20 prompts and Caldova rubric.
- Trace-derived dataset is available.
- A completed Agent Optimizer run exists in the portal.
- Candidate changes and comparison details have been reviewed for recording.

## Recording sequence

Foundry Agent Optimizer runs from `azd ai agent optimize` and visualizes
in the portal. The `/build/agents/contoso-travel/optimize` tab is the
viewer surface; the launcher is the CLI.

| Beat | Screen | Presenter action | Edit |
|---|---|---|---|
| 1 | Foundry portal | Open the **Optimize (Preview)** tab for `contoso-travel`. Show the landing card that describes the flow. | Keep context visible. |
| 2 | GitHub Copilot App | Ask Copilot to confirm readiness (Prompt 13) and compose the `azd ai agent optimize` command. Do not launch. | Show the composed command. |
| 3 | Terminal | Paste and run the composed command (Prompt 14). Confirm the portal accepts the run and shows a job id. | End after job id appears; resume at the completed candidate list. |
| 4 | Completed checkpoint | Resume at the completed candidate list in the Foundry portal Optimize tab. | Add completion title card. |
| 5 | Candidate comparison | Compare quality, compliance, cost, latency, and proposed changes across the up-to-five candidates. | Show more than one viable tradeoff if available. |
| 6 | Evidence | Open row-level results and candidate changes (instructions, tool descriptions, model selection). | Tie recommendation to Caldova goals. |
| 7 | Human review | Select the preferred candidate. Trigger promotion with `azd ai agent optimize deploy --candidate <id>` (or the portal Deploy button, whichever the presenter prefers). | Do not imply autonomous production change. |
| 8 | Final state | Show the promoted or approved version and version lineage in the portal + `azd ai agent show`. | Close the loop. |

## Narration

- “Act 3 taught us the discipline; now Foundry automates the repetition.”
- “Every candidate is tested against the same evidence and Caldova criteria.”
- “The optimizer recommends. Contoso reviews and decides.”
- “As models and workloads change, Lydia can rerun the loop without rebuilding
  the concierge.”

## Required visible evidence

- Agent, dataset, and evaluator selection.
- Candidate list.
- Candidate-specific changes.
- Separate business metrics.
- Human approval or explicit defer decision.
- Version lineage.

## Recording edit points

Remove optimizer execution, candidate-evaluation, refresh, and propagation
waiting periods. Always show the initiating action and the verified result.

## Reset

Retain the completed optimization run. Reset only the selected promotion state
or use an unpromoted duplicate run for retakes.

## Fallback media

- Optimizer setup.
- Running state.
- Completed candidate list.
- Candidate detail.
- Human review and promotion screen.
