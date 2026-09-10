# Implementation inventory

## Repository destinations

| Destination | Required assets |
|---|---|
| `.plan/` | Specifications, ordered recording prompts, demo runbooks, slide references, speaker notes, and planning-only instructor guidance |
| `src/agent/` | Python hosted-agent entry point, task decomposition, tool definitions, telemetry, configuration loader |
| `src/web/` | FastAPI app, templates, CSS, JavaScript, API client, static icons |
| `src/evaluation/` | Dataset conversion, batch evaluation, result normalization, comparison reporting |
| `src/training/` | Trace curation, training-dataset preparation, supported fine-tuning/distillation workflow |
| `data/policy/` | Synthetic Caldova travel policy and machine-readable rules |
| `data/catalogs/` | Flights, hotels, car rentals, airports, cities, and deterministic availability |
| `data/receipts/` | English and French synthetic receipt images plus expected extraction JSON |
| `data/itineraries/` | Multi-stop examples and expected itinerary outputs |
| `data/evaluation/` | 50-prompt JSONL, fixed 20-prompt subset, expected behaviors, rubric |
| `data/training/` | Curated trace-derived teacher/student examples and provenance manifest |
| `infra/` | Foundry project, hosted-agent prerequisites, App Insights, model deployments, web hosting, RBAC |
| `docs/` | Architecture, data model, evaluation approach, cost methodology, security/privacy |
| `delivery-resources/README.md` | Run of show, deck URL, recording links, presenter guidance |
| `instructions/` | Deferred until self-paced attendee guidance is approved |
| `azure.yaml` | Root azd service manifest only when required by the hosted-agent workflow |

Do not create other top-level implementation directories. In particular, do not
create `delivery-resources/demos/` or a separate presenter guide under
`delivery-resources/`.

## Synthetic fixture inventory

| ID | Asset | Purpose |
|---|---|---|
| POL-001 | Caldova global travel policy | Primary policy grounding source |
| POL-002 | Expense and receipt rules | Parking, meals, currency, receipt thresholds |
| CAT-001 | Flight catalog | Deterministic routes, cabins, prices, refundable flags |
| CAT-002 | Hotel catalog | Location, nightly rate, amenities, policy flags |
| CAT-003 | Car-rental catalog | Vehicle class, daily cost, insurance, fuel policy |
| EMP-001 | Krystal profile | Home airport, accessibility, loyalty, role limits |
| REC-001 | English parking receipt | Hero multimodal extraction case |
| REC-002 | French parking receipt | Multilingual extraction case |
| REC-003 | Hotel folio | Itemization and non-reimbursable charge case |
| REC-004 | Car-rental receipt | Fuel and insurance policy case |
| ITN-001 | Paris hero itinerary | Flight, hotel, car, receipt, policy |
| ITN-002 | Multi-stop EU itinerary | Routing, timing, and multilingual case |
| EVAL-050 | Full 50-prompt dataset | Reusable coverage |
| EVAL-020 | Fixed recorded subset | Comparable baseline and candidates |
| RUB-001 | Caldova rubric | Domain-specific quality measurement |
| TRAIN-001 | Teacher/student examples | Catalog-verified training experiment |

## Azure resources

- Resource group named `rg-brk330-concierge`.
- Microsoft Foundry resource and project.
- Application Insights and associated Log Analytics workspace if required.
- Hosted-agent deployment.
- Frontier model deployment for baseline.
- Eligible judge-model deployment for evaluation and Insights.
- Model Router deployment or current equivalent.
- Catalog-verified trainable student-model deployment.
- Azure hosting for FastAPI with managed identity.
- Role assignments for deployment, invocation, tracing, evaluation, and
  Monitoring Reader access.

## Required captured evidence

- Deployment success and public URL.
- Hero request response and tool timeline.
- Blocked noncompliant request.
- Baseline evaluation summary and row-level failure.
- Model Router route selections and cost calculation.
- Student-model training status and comparison.
- Insights issue and related traces.
- Agent Optimizer candidate list, evidence, and human-review step.
