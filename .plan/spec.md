# Contoso Travel Concierge demo specification

## Session contract

### Title

Optimize agents with Microsoft Foundry & GitHub Copilot

### Abstract

> You need agents to meet cost & quality targets, but model choices & costs keep
> shifting. Watch GitHub Copilot run a hill-climbing loop on a travel concierge
> built on Microsoft Foundry. Build a repeatable model optimization playbook for
> your AI agents.

The implementation and session must visibly satisfy every promise in this
abstract.

## Story

Caldova is a fictional Microsoft pharmaceutical operations company whose
employees travel frequently for research, sales, and engineering collaboration.
Caldova contracts Contoso Travel to build the **Contoso Travel Concierge**.

The concierge helps Caldova employees plan flights, hotels, and car rentals,
process travel receipts, and comply with Caldova travel policy. Contoso engineers
build and optimize the service; Caldova owns the policy, pays for the service,
and uses it.

### Personas

- **Krystal McKinney, R&D Lead:** needs travel planning and expenses to work with
  minimal effort.
- **Andre Lawson, CFO:** needs the concierge and the resulting travel to be
  cost-effective.
- **Cassandra Dunn, Compliance Manager:** needs policy and regulatory compliance.
- **Lydia Bauer, Enterprise IT Architect:** needs reliable integration and rapid
  adaptation as models and quality change.

Do not introduce other named personas. Replace any legacy reference to Carmen
with Krystal.

## Session outcomes

Attendees will be able to:

1. Define measurable quality, compliance, cost, and latency targets using
   representative workload data and a context-specific rubric.
2. Use GitHub Copilot and Microsoft Foundry to build, observe, and manually
   hill-climb an agent by changing one lever at a time.
3. Use Agent Optimizer to automate candidate evaluation while retaining human
   review and promotion.

## Five-act narrative

| Act | Duration | Outcome |
|---|---:|---|
| Set the stage | 5 minutes | Explain why continuous optimization is required. |
| Make it work: Let's build | 12 minutes | Build, deploy, observe, and baseline the Agent Loop. |
| Make it better: Let's climb | 12 minutes | Measure and manually hill-climb the Model Loop. |
| Make it easier: Let's automate | 12 minutes | Automate candidate search with Agent Optimizer. |
| Summary | 4 minutes | Present the reusable optimization playbook. |

## Demo system

### Real implementation requirement

Every demonstrated capability must be implemented and executed end to end
against live Azure resources. Recording edits may remove elapsed waiting time,
but they must never replace a real provisioning, deployment, evaluation,
training, tracing, Insights, or Agent Optimizer operation. Each resumed clip
must show the verified result of the operation started in the preceding clip.

### Required architecture

- Azure resource group named `rg-brk330-concierge`.
- A Python Microsoft Foundry hosted agent.
- Foundry Canvas used visibly from GitHub Copilot App for hosted-agent creation,
  configuration, deployment, and testing.
- A lightweight FastAPI application serving HTML, CSS, and JavaScript.
- Live Azure deployment only.
- Microsoft Foundry project connected to Application Insights.
- A deployed judge model supported by the active Foundry evaluation and Insights
  experiences.
- A Model Router deployment or supported routing configuration.
- A supported, catalog-verified student model for distillation or fine-tuning.
- Agent Optimizer configured for the Python hosted agent.

### Foundry Canvas role

- **Act 2:** Open Foundry Canvas in creation-progress mode when Copilot creates
  the new hosted agent. After creation, use **Deploy & test** to make deployment
  and smoke testing visible.
- **Act 3:** Open Foundry Canvas in manage mode. Use **Build current hosted
  agent** for model, tool, skill, and configuration work, and **Deploy & test**
  for candidate deployment and validation.
- **Act 4:** Keep Agent Optimizer portal-first. Foundry Canvas may remain open for
  agent context, but it does not replace the portal optimization-run experience.

Do not choose or name the student model until implementation verifies live
catalog availability and training eligibility.

### Lightweight travel tools

Use deterministic synthetic tools rather than production travel APIs:

- `search_flights`
- `search_hotels`
- `search_car_rentals`
- `check_travel_policy`
- `extract_receipt`
- `prepare_itinerary`
- `submit_booking` in dry-run mode only

Tool results come from synthetic fixtures. The UI must clearly show request
details, decomposed tasks, selected options, policy decisions, receipts,
model-routing evidence, and final itinerary status.

### Hero request

Krystal asks for a multi-stop business trip that combines:

- Flights
- Hotel near the meeting location
- Car rental
- Caldova travel-policy constraints
- An attached parking receipt
- A request to determine whether the receipt is reimbursable

The exact prompt and assets are defined in `test-prompts.md` and `inventory.md`.

## Functional requirements

1. Parse a single compound request into explicit tasks.
2. Extract structured data from English and French receipt images.
3. Search deterministic flight, hotel, and car-rental fixtures.
4. apply Caldova policy to each proposed choice and expense.
5. Block noncompliant booking actions rather than merely warning.
6. Explain policy decisions and cite the relevant synthetic policy rule.
7. Return a clear itinerary with estimated travel cost and next actions.
8. Preserve trace correlation across task decomposition, model calls, and tools.
9. Record model, token, latency, and estimated cost metadata per task.
10. Support a frontier-model baseline and a decomposed Model Router variant.
11. Run the same evaluation dataset against all compared variants.
12. Support a catalog-verified distillation or fine-tuning experiment.
13. Keep Agent Optimizer promotion human-approved.

## Evaluation contract

### Evaluation dataset

- Retain exactly 50 representative prompts.
- Use 20 balanced prompts for recorded evaluation runs.
- Include multi-intent, ambiguous, multilingual, disruption, accessibility,
  policy-conflict, receipt, and multi-stop cases.
- Use the same 20 prompt IDs for baseline, routed, student, and optimizer
  comparisons.

### Caldova rubric

Score each response across:

| Dimension | Purpose | Gate |
|---|---|---|
| Intent and task completeness | Identifies and addresses every requested job | Required |
| Policy compliance | Applies Caldova policy correctly and cites the rule | Hard gate |
| Tool-use accuracy | Selects tools and passes correct arguments | Required |
| Travel-plan correctness | Produces a feasible itinerary from fixtures | Required |
| Receipt accuracy | Extracts and classifies receipt details correctly | Required when applicable |
| Communication clarity | Produces concise, actionable output | Required |

Quality, cost, and latency remain separate metrics. Do not collapse them into a
single synthetic score.

### Cost glossary

- **Per model call:** cost for one routed or direct inference.
- **Per request:** aggregate cost for one user turn, including decomposed tasks.
- **Per trip:** aggregate cost to complete the full itinerary workflow.

Every slide and result must name its unit. Replace all provisional figures with
measured dry-run results.

## Optimization experiments

### Baseline

One capable frontier model handles the entire compound request. This should
provide strong behavior at a comparatively high cost.

### Task decomposition and routing

Decompose the request before routing. Send each independent task to Model Router
with sufficient context. Measure selected models, quality, latency, and cost.
Never send the raw compound request directly to Model Router and claim
task-level right-sizing.

### Distillation or fine-tuning

Use high-quality frontier outputs and trace-derived examples to train a supported
smaller student model. The goal is to recover the required quality threshold at
lower cost. If the live catalog does not support the intended training path,
stop and record the exact limitation rather than fabricating a result.

### Agent Optimizer

Use the portal to generate and evaluate candidates against the same dataset and
rubric. The optimizer recommends; a human reviews the evidence and decides
whether to promote.

## Observability requirements

- Server-side hosted-agent tracing.
- Application Insights connection.
- Evaluation results correlated with traces.
- Foundry Insights configured with an eligible judge model.
- Foundry project managed identity assigned the least-privilege role required to
  read Application Insights; validate the current portal requirement during
  implementation.
- Portal screenshots or clips captured for preview UI contingencies.

Evaluation improves measurement, not behavior. Insights identifies changes and
supporting traces; it does not itself complete the optimization.

## Synthetic data requirements

All assets must be original and fictional:

- Caldova travel policy
- Employee profile and preferences for Krystal
- Flight, hotel, and car-rental fixture catalogs
- English and French receipt images
- Multi-stop itinerary documents
- Expected tool calls and policy outcomes
- Evaluation dataset and expected behaviors
- Trace-derived training examples

Do not use real personal, pharmaceutical, payment, or travel-account data.

## Definition of done

- Live Azure URL for the FastAPI experience.
- Deployed Foundry hosted agent.
- Hero request completes with visible policy enforcement.
- Baseline, routed, and trained-student results use the same 20 prompts.
- Measured quality, compliance, latency, tokens, and cost are available.
- Insights displays prepared evaluated-trace evidence.
- Agent Optimizer run displays candidate comparison and human review.
- Three recordable demo runbooks have verified checkpoints.
- Session timing totals 45 minutes.
- Slide and speaker-note recommendations align with actual measured results.
