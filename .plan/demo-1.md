# Demo 1: Build and baseline with GitHub Copilot

## Act

Act 2 — Make it work: Let's build — Agent Loop

## Audience outcome

The concierge can complete a compound request, but a successful example does not
prove quality, compliance, or cost-effectiveness. Evaluated traces establish the
baseline and reveal where to improve.

## Pre-recording state

- Foundry project and supported models provisioned.
- Application Insights connected.
- Foundry project managed identity has the required monitoring role.
- Hosted agent and FastAPI site do not yet exist on the starting branch.
- Final deployed checkpoint exists on a separate prepared branch.
- Fixed hero prompt, policy, catalogs, and receipt are ready.
- The 20-prompt batch and completed evaluation checkpoint are ready.

## Recording sequence

| Beat | Screen | Presenter action | Edit |
|---|---|---|---|
| 1 | GitHub Copilot App | Open a new session and provide the build prompt referencing `.plan/spec.md`. | Keep prompt and plan summary. |
| 2 | Foundry Canvas + Copilot changes | Show Foundry Canvas in creation-progress mode and the proposed hosted-agent, FastAPI, data, and infra files. | Show representative files, then edit directly to the completed change set. |
| 3 | Foundry Canvas | Use **Deploy & test** while Copilot provisions and deploys with the Foundry skill. | End this clip after Azure accepts the deployment; resume in a new clip after successful verification. |
| 4 | Deployed checkpoint | Resume on the prepared branch with successful deployment output and URL. | Add “deployment completed” title card. |
| 5 | Web app | Submit Krystal's hero request with `REC-001`. | Keep full user interaction. |
| 6 | Result | Show decomposed tasks, policy citations, selected travel options, receipt decision, and itinerary. | Highlight compliance. |
| 7 | Policy gate | Run one known noncompliant request. | Show booking blocked. |
| 8 | Batch action | Ask Copilot to run the fixed evaluation subset. | End after the job starts; resume at the verified completed result. |
| 9 | Foundry portal | Show completed evaluation and traces. | Use stable prepared result. |
| 10 | Insights | Open prepared finding and related trace. | End on evidence, not solution. |

## Narration

- “Contoso starts with the fastest path to value: make the concierge work.”
- “One request contains several jobs—planning, vision, policy, and action.”
- “A good-looking answer is not evidence that the system is reliable.”
- “Now we know what the system did, what it cost, and where behavior changed.”

## Required visible evidence

- Correct task decomposition.
- English receipt extraction.
- Caldova policy citation.
- Hard block for a noncompliant option.
- Trace tree with model and tool spans.
- Evaluation result correlated to traces.
- Insights finding labeled as preview if still applicable.

## Recording edit points

Remove idle or repetitive portions of scaffolding, Azure provisioning, RBAC
propagation, batch evaluation, trace ingestion, and Insights analysis. Always
show the initiating action and the verified result in adjacent clips.

## Reset

1. Restore the starting Git branch.
2. Clear only demo conversations, not shared project resources.
3. Confirm the hero fixtures are unchanged.
4. Confirm the prepared deployment and evaluation checkpoints still exist.

## Fallback media

- Successful Copilot plan.
- Deployment completion.
- Hero result.
- Blocked policy case.
- Evaluation summary.
- Trace detail.
- Insights finding and linked trace.
