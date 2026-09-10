# BRK330 build session log

*Living record of decisions made and evidence produced during the
first end-to-end build session. Written for a future presenter or
maintainer to reconstruct what was built and why.*

## Naming and resource identifiers

| Slot | Value |
|---|---|
| Azure subscription | `ai-team` (`<subscription-id>`) |
| Region | Sweden Central |
| Resource group | `rg-brk330-concierge` |
| Foundry (AI Services) account | `cog-hqxztqzboq4bq` |
| Foundry project | `brk330-concierge-project` |
| Hosted-agent name / azd service | `contoso-travel` |
| Baseline model deployment | `gpt-5` @ `2025-08-07` |
| Judge model deployment | `gpt-4.1` @ `2025-04-14` |
| Router model deployment | `model-router` @ `2025-11-18` |
| Deployment SKU capacity (all three) | `GlobalStandard` at capacity `500` |
| Application Insights | `appi-brk330-nxzzad4sd6dl6` |
| Log Analytics workspace | `log-brk330-nxzzad4sd6dl6` |
| Azure Container Registry | `acrbrk330nxzzad4sd6dl6.azurecr.io` |
| Container Apps environment | `cae-brk330-nxzzad4sd6dl6` |
| Web app (FastAPI experience) | `contoso-web` |
| Web URL | https://contoso-web.orangemeadow-ec004249.swedencentral.azurecontainerapps.io |
| Web managed identity | `id-web-nxzzad4sd6dl6` |
| Hosted-agent instance MI | principalId `c1db71cb-7c6e-439a-a618-c4758b874d1d` |
| Foundry project MI | principalId `892bfbc2-4a6e-4e50-a77c-38bba8222aca` |
| Foundry account MI | principalId `c1928aad-d7d7-4abb-9bfc-52633c152b1c` |

## Repository layout (spec-compliant)

Everything sits under the folders the spec's placement contract allows.

- `src/agent/` — Python Foundry hosted agent (Agent Framework, Responses
  protocol). Fixtures mirrored into `src/agent/fixtures/` via the
  service-scoped `prepackage` hook so the container has them at
  `/app/fixtures/`.
- `src/agent/eval.yaml` + `src/agent/tests/queries.jsonl` — golden-path
  `azd ai agent eval` config and the 20-query dataset in the schema
  Foundry expects.
- `src/web/` — FastAPI thin-client that calls the deployed hosted agent's
  Responses endpoint using the web managed identity. Reads
  `AGENT_CONTOSO_TRAVEL_RESPONSES_ENDPOINT` and
  `APPLICATIONINSIGHTS_CONNECTION_STRING` from the container env.
- `src/evaluation/` — `run_baseline.py` runs the 20 prompts against the
  deployed agent and captures latency/tokens/cost. `run_rubric.py` runs
  the Caldova rubric as an LLM-as-judge scorer.
- `data/policy/`, `data/catalogs/`, `data/employees/`, `data/receipts/`,
  `data/itineraries/`, `data/evaluation/` — synthetic fixtures. The
  receipt PNGs are generated deterministically from
  `scripts/generate_receipts.py`.
- `data/evaluation/rubric.json` — internal 1..5 rubric used by the
  local scorer.
- `data/evaluation/rubric-foundry.json` — Foundry portal / SDK rubric
  schema (weight 1-10) for the Rubric Evaluator preview.
- `data/evaluation/rubric-metadata.json` — human-readable wrapper.
- `docs/evaluation/rubric-setup.md` — golden-path evaluation guide with
  paths A (azd), B (portal), C (SDK), D (local judge).
- `azure.yaml` — Foundry-provider driven manifest with three services
  (`contoso-travel` hosted agent, `ai-project` model deployments, `web`
  container app) and lifecycle hooks (`prepackage` for fixture sync,
  `postprovision` for supplemental infra).
- `infra/supplemental.bicep` — everything the Foundry provider does not
  handle: App Insights + Log Analytics, project → App Insights connection
  with `isSharedToAll: true`, Container Apps environment, ACR, web MI,
  and RBAC (Monitoring Reader, Monitoring Metrics Publisher, AcrPull,
  and Cognitive Services User / OpenAI User / Foundry User at both
  account and project scope for the web MI).

## What was proven live in this session

- **Provisioning** — Foundry account + project + three model deployments
  via the Foundry provider (`azd provision`).
- **Hosted-agent deploy** — `contoso-travel` v4 active on the Responses
  protocol.
- **Live smoke tests** — hero (TP-01-shape) passed with cited policy;
  hard-gate case (TP-04-shape) blocked with CT-11 + CT-02.
- **Web app** — FastAPI thin client renders task decomposition, tool
  timeline, cited rules, and token / cost metadata.
- **Baseline evaluation** — 20 prompts, 100% completion, 0 errors, avg
  latency 44.5 s, avg cost per request $0.0313, hard-gate pass rate 95%.
  Manifest: `data/evaluation/results/baseline-20260910T073852Z.*`.
- **Foundry Insights scan** — returned 4 evidence-backed findings.
  Highlighted the *"Hallucinates rule-level compliance from
  non-attributed tool outputs"* finding as Demo 1's reveal.
- **Caldova rubric scoring** — three complementary artefacts now cover it:
  1. `caldova-composed-eval` — deterministic bundle of three built-in
     Foundry evaluators (`intent_resolution`, `task_adherence`,
     `tool_call_accuracy`), attached via `src/agent/eval.yaml` and the
     `azd ai agent eval run` golden path.
  2. `caldova-agent-rubric-eval` — auto-generated Foundry Rubric
     Evaluator grounded on the deployed contoso-travel agent context
     and recent App Insights traces. **Non-deterministic** in schema:
     dimensions and weights depend on which traces the generator sees.
     Pin the specific evaluator version when comparing baseline against
     routed / student / optimizer candidates.
  3. `src/evaluation/run_rubric.py` — local seven-dimension judge that
     mirrors the Foundry Rubric Evaluator semantics (weight-9 policy
     hard gate) for fast CI/CD scoring outside the portal.
  Local scorer baseline result on the P5 rows: overall quality 3.38/5,
  policy 2.55/5, pass rate 10 %. Representative failure:
  **TP-19** (Montréal accessibility case, 0 tools called, 0 rules cited).

## Decisions worth remembering

- **Azure Container Apps** for the FastAPI experience (recommended over
  App Service Linux for managed-identity + Insights fit).
- **Foundry provider owns Foundry resources**; supplemental Bicep covers
  App Insights + Container Apps + non-Foundry RBAC. Avoids reinventing
  what the provider already automates.
- **Token audience for the hosted-agent Responses endpoint is
  `https://ai.azure.com/.default`**, not `cognitiveservices.azure.com`.
  The web `chat` handler tries the Foundry scope first and falls back to
  the Cognitive Services scope for backwards compatibility.
- **Project-scope RBAC is required** for callers invoking the hosted
  agent's Responses endpoint. Account-scope grants are inherited but
  the endpoint's own check runs at project scope; the web MI needs
  `Cognitive Services User` + `Cognitive Services OpenAI User` + `Foundry
  User` at the project resource, not just the account.
- **App Insights connection on the project must have `isSharedToAll:
  true`** for the Insights preview scan to consume it.
- **Hosted-agent instance MI needs `Monitoring Metrics Publisher`** on
  App Insights for tracing to actually land; Bicep grants this when
  `hostedAgentInstancePrincipalId` is present in azd env.
- **Fixtures are mirrored into `src/agent/fixtures/`** at package time.
  The container's Dockerfile does `COPY .` from the service project
  folder only, so fixtures must live inside `src/agent/` at deploy.
- **Caldova rubric weights** follow the Foundry rule "exactly one 8–10":
  `policy_compliance` at 9 (hard gate), others 2–6, plus a `general_quality`
  criterion at weight 5 with `always_applicable: true`.
- **Model deployment capacities were bumped to 500 (from 30 / 10)** so
  the Insights scan and the rubric judge have plenty of TPM headroom
  without contending with baseline invocations.

## Still open (P8 onwards)

- Task decomposition + Model Router routing in the agent (P8).
- Routed deployment + comparison (P9).
- Trace-derived training dataset + student model (P10–P12).
- Agent Optimizer readiness + run + promotion (P13–P15).
- Cleanup of remaining `*.custom-backup` / `*.scaffold` artefacts
  (`azure.yaml.custom-backup`, `src/agent/Dockerfile.scaffold`,
  `src/agent/main.py.scaffold`, `src/agent/requirements.scaffold.txt`,
  `src/agent/agent.yaml.custom-backup`, `src/agent/main.py.custom-backup`,
  `src/web/main.py.custom-backup`) — tracked as todo `cleanup-backups`.
