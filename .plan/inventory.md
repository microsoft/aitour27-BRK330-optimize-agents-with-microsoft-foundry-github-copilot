# Implementation inventory

## Repository destinations

| Destination | Required assets |
|---|---|
| `.plan/` | Specifications, ordered recording prompts, demo runbooks, slide references, speaker notes, planning-only instructor guidance, and `session-log.md` capturing session decisions |
| `src/agent/` | Python hosted-agent entry point (Agent Framework, Responses protocol), task decomposition, tool definitions, telemetry, configuration loader, plus `eval.yaml` and `tests/queries.jsonl` for the azd golden-path evaluation |
| `src/web/` | FastAPI app, templates, CSS, JavaScript, `Dockerfile` (remote-build), and a thin HTTP client against the hosted-agent Responses endpoint |
| `src/evaluation/` | Dataset conversion (`build_eval_dataset.py`), batch evaluation (`run_baseline.py`), rubric scoring (`run_rubric.py`), result normalization, comparison reporting |
| `src/training/` | Trace curation, training-dataset preparation, supported fine-tuning/distillation workflow |
| `data/policy/` | Synthetic Caldova travel policy (`caldova-travel-policy.md`) and machine-readable rules (`rules.json`) |
| `data/catalogs/` | Flights, hotels, car rentals, airports, cities, exchange rates |
| `data/receipts/` | English and French synthetic receipt PNGs plus expected extraction JSON |
| `data/itineraries/` | Multi-stop examples and expected itinerary outputs |
| `data/evaluation/` | 50-prompt JSONL, fixed 20-prompt subset, expected behaviors, local rubric (`rubric.json`), Foundry-native rubric (`rubric-foundry.json`), rubric metadata, and result manifests under `results/` |
| `data/training/` | Curated trace-derived teacher/student examples and provenance manifest |
| `infra/` | `supplemental.bicep` for App Insights, Log Analytics, Container Apps, ACR, and RBAC that the Foundry provider does not handle |
| `docs/` | Architecture, data model, evaluation approach (`docs/evaluation/rubric-setup.md`), cost methodology, security/privacy |
| `delivery-resources/README.md` | Run of show, deck URL, recording links, presenter guidance |
| `instructions/` | Deferred until self-paced attendee guidance is approved |
| `azure.yaml` | Root azd service manifest with Foundry-provider hosted-agent config, model deployments, web container app, and `prepackage` / `postprovision` hooks |
| `scripts/` | Deterministic asset generation (`generate_receipts.py`, `build_eval_dataset.py`) |

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
| RUB-001 | Caldova rubric | Domain-specific quality measurement — see `data/evaluation/rubric.json` (local 1..5 scale), `data/evaluation/rubric-foundry.json` (Foundry portal / SDK weighted schema, `policy_compliance` = 9), and `data/evaluation/rubric-metadata.json` for the wrapper. |
| TRAIN-001 | Teacher/student examples | Catalog-verified training experiment |

## Azure resources

- Resource group named `rg-brk330-concierge` in Sweden Central.
- Foundry (AI Services) account, provisioned by the Foundry provider from
  `azure.yaml`. Concrete name: `cog-hqxztqzboq4bq`.
- Microsoft Foundry project `brk330-concierge-project` with an active
  ApplicationInsights connection (`isSharedToAll: true`).
- Foundry hosted-agent and azd service named `contoso-travel`.
- Application Insights + Log Analytics workspace, provisioned by
  `infra/supplemental.bicep`. Concrete names: `appi-brk330-nxzzad4sd6dl6`,
  `log-brk330-nxzzad4sd6dl6`.
- Model deployments — all three at `GlobalStandard` SKU, capacity `500`:
  - `gpt-5` @ 2025-08-07 (frontier baseline).
  - `gpt-4.1` @ 2025-04-14 (judge model for the Caldova rubric and
    Foundry Insights preview).
  - `model-router` @ 2025-11-18 (Session 2 routed variant).
- Azure Container Registry (`acrbrk330nxzzad4sd6dl6.azurecr.io`), Container
  Apps environment, and web Container App (`contoso-web`) for the FastAPI
  experience.
- User-assigned managed identity `id-web-nxzzad4sd6dl6` for the web app.
- Hosted-agent instance managed identity (managed by the Foundry provider;
  its principal id is captured in azd env as
  `HOSTED_AGENT_INSTANCE_PRINCIPAL_ID` and used by the supplemental
  Bicep to grant Monitoring Reader + Monitoring Metrics Publisher on
  App Insights).
- Role assignments — least-privilege — for deployment, invocation,
  tracing, evaluation, and Monitoring Reader access:
  - Web MI: `AcrPull` on ACR; `Monitoring Metrics Publisher` on App
    Insights; `Cognitive Services User` + `Cognitive Services OpenAI User`
    + `Foundry User` at both the Foundry account and project scope.
  - Hosted-agent instance MI: `Monitoring Reader` + `Monitoring Metrics
    Publisher` on App Insights.
  - Foundry project MI + Foundry account MI: `Monitoring Reader` on
    App Insights.

## Required captured evidence

- Deployment success and public URL.
- Hero request response and tool timeline.
- Blocked noncompliant request.
- Baseline evaluation summary and row-level failure.
- Model Router route selections and cost calculation.
- Student-model training status and comparison.
- Insights issue and related traces.
- Agent Optimizer candidate list, evidence, and human-review step.
