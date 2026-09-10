# Demo 2: Hill climb with GitHub Copilot

## Act

Act 3 — Make it better: Let's climb — Model Loop

## Audience outcome

Contoso defines “good,” changes one lever at a time, and uses the same evidence to
decide whether each step improves the overall cost-quality outcome.

## Pre-recording state

- Baseline hosted agent and fixed 20-prompt results exist.
- Caldova rubric draft and expected behaviors exist.
- Model Router availability is verified.
- A completed routed checkpoint exists.
- A supported training-eligible student model is verified.
- Training dataset and completed training checkpoint exist if the training path
  succeeded.

## Recording sequence

| Beat | Screen | Presenter action | Edit |
|---|---|---|---|
| 1 | GitHub Copilot App | Ask Copilot with Foundry skills to create/register the Caldova rubric and run baseline evaluation. | End after the job starts; resume at the verified completed result. |
| 2 | Foundry portal | Show baseline dimensions and a failing policy/task-completeness row. | Establish the hill. |
| 3 | GitHub Copilot App | Ask Copilot to identify tasks in the compound workload and implement decomposition before Model Router. | Show focused diff. |
| 4 | Deployment action | Deploy the routed candidate. | End after Azure accepts the deployment; resume after verification. |
| 5 | Foundry portal | Show per-task route evidence and the same 20-prompt comparison. | Highlight cost drop and any quality loss. |
| 6 | GitHub Copilot App | Ask Copilot to curate teacher outputs and start the supported training workflow for the verified student model. | End after the training job starts; resume at its verified result. |
| 7 | Completed training checkpoint | Show the trained model deployment and evaluation run. | Do not show fabricated success. |
| 8 | Comparison | Compare baseline, routed, and student configurations across separate metrics. | End on the accepted or rejected climb. |

## Narration

- “Do not use a Ferrari when the job needs a bike.”
- “Routing works only after we separate the jobs.”
- “Cheaper is not better if policy adherence drops.”
- “The evaluator tells us where quality changed; it does not improve the agent.”
- “The student wins only if it recovers the target quality at the lower cost.”

## Caldova rubric emphasis

- Policy compliance is a hard gate.
- Intent and task completeness carries strong weight.
- Tool-use accuracy must inspect the trace.
- Receipt accuracy applies only to receipt cases.
- Communication quality cannot compensate for a policy failure.

## Required comparison

| Variant | Quality | Compliance | Latency | Cost |
|---|---|---|---|---|
| Frontier baseline | `<measured after dry run>` | `<measured after dry run>` | `<measured after dry run>` | `<measured after dry run>` |
| Decomposed + Model Router | `<measured after dry run>` | `<measured after dry run>` | `<measured after dry run>` | `<measured after dry run>` |
| Trained student | `<measured after dry run>` | `<measured after dry run>` | `<measured after dry run>` | `<measured after dry run>` |

## Recording edit points

Remove waiting periods for evaluator registration, evaluation jobs, routed
deployment, training-data upload, training, and model deployment. Always show
the initiating action and the verified result.

## Reset

Use separate immutable version labels for baseline, routed, and student
configurations. Never overwrite the baseline.

## Fallback media

- Rubric dimensions and threshold.
- One passing and one failing result.
- Decomposition diff.
- Per-task route metadata.
- Three-way comparison.
- Training status and model details.
