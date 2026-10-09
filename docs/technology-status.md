# Technology status

Status last verified against current Microsoft documentation and a live learner-selected subscription in **East US 2 (`eastus2`)** on **October 6, 2026**. Preview and rollout status can change; presenters must rerun preflight and verify the target tenant before recording or delivery.

| Capability | Status at verification | BRK330 use |
|---|---|---|
| GitHub Copilot Agent mode | Generally available; Copilot license required | Demo 1 build workflow, Demo 2 engineering changes, Demo 3 optimizer orchestration. |
| Foundry Dev Pack | Supported installer bundle; components have their own lifecycle | Dev-container toolchain for Azure CLI, azd, Foundry extensions, and Toolkit. |
| Microsoft Foundry Skill | Supported coding-agent workflow content; no separate service lifecycle label | Deployment, evaluation, tracing, RBAC, and optimizer guidance. |
| Foundry Toolkit for VS Code | Active extension; current optimizer workflow requires a recent/pre-release version | Agent/project inspection and optional visual review in Demos 1 and 3. |
| [Microsoft Learn MCP Server](https://learn.microsoft.com/en-us/training/support/mcp) | Current hosted MCP documentation service; current page has no preview banner | Authoritative documentation grounding during build and presenter rebuild. |
| [Foundry MCP Server](https://learn.microsoft.com/en-us/azure/foundry/mcp/get-started) | **Preview** | Live Foundry model/project/resource discovery and preflight. Agent Optimizer execution uses the Foundry Skill and azd instead. |
| [Foundry Hosted Agents](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/hosted-agents) | Current production capability; individual protocols can have separate preview status | Core `contoso-travel` runtime, immutable versions, endpoint rerouting, and rollback. |
| Responses API and Agent Framework | Current recommended hosted-agent implementation path | Agent orchestration and deterministic tool calls in all demos. |
| Application Insights and OpenTelemetry | Generally available platform components | Traces, tool evidence, version correlation, and Insights input. |
| Insights in Foundry | **Public preview** | Act 2: groups v1's traces into findings that feed the scorecard. |
| [Rubric Evaluator](https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/rubric-evaluators) | **Preview** | Act 3: scorecard drafted from v1's traces, reviewed, then used unchanged for every version. |
| [Model Router](https://learn.microsoft.com/en-us/azure/foundry/openai/concepts/model-router) | Generally available; underlying model availability remains regional | Act 3 lever v2: the router picks a model per request. |
| [`gpt-4.1-mini` fine-tuning](https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/fine-tuning) | Live East US 2 catalog: Legacy, Responses/Agents v2 support, `globalFineTune` and `devTierFineTune`, retirement April 14, 2027 | Act 3 lever v2-alt: supervised student base through the December 2026 delivery. Revalidate immediately before training. |
| Foundry Fine Tuning azd extension | `azure.ai.finetune` `0.0.17-preview`; output and config contracts remain preview | Submit, inspect, and deploy the v2-alt student. |
| Synthetic and traces-to-dataset generation | Rollout and regional availability vary; verify the target tenant | Optional acceleration for Demo 2 data curation; versioned manual provenance remains the fallback. |
| [Agent Optimizer](https://learn.microsoft.com/en-us/azure/foundry/agents/quickstarts/quickstart-optimize-hosted-agent) | **Preview**; current quickstart requires subscription allow-list | Act 4: proposes instruction changes from practice questions; a person reviews, retests, and promotes v3. |
| Azure Container Apps | Generally available | Persistent FastAPI behavior surface across sequential agent versions. |

## Delivery rule

Never change labels merely to match a slide. Update this table, recordings, screenshots, and presenter notes from authoritative documentation and observed tenant capability together.

## Recording model plan

Live quota check against the learner-selected subscription in East US 2 on October 6, 2026. Setup deploys every model below; the capacity column is what `azure.yaml` requests.

| Role | Deployment | Model/version | Lifecycle | Capacity deployed | Remaining quota at check | Earliest model-level retirement |
|---|---|---|---|---:|---:|---|
| v1 and optimizer reasoning | `gpt-5.4` | `gpt-5.4` `2026-03-05` | Generally available | 300 | 12,697 | September 2, 2027 |
| Scorecard judge | `gpt-5.4-mini` | `gpt-5.4-mini` `2026-03-17` | Generally available | 300 | 38,199 | September 21, 2027 |
| Insights judge | `insights-judge` | `gpt-5.6-sol` `2026-07-09` | Generally available | 500 | 750 | January 11, 2028 |
| v2 | `model-router` | `model-router` `2025-11-18` | Generally available | 300 | 11,439 | May 20, 2027 |
| v2-alt base | `gpt-4.1-mini` | `gpt-4.1-mini` `2025-04-14` | Legacy; `globalFineTune` and `devTierFineTune` | 100 | 449,610 (500 fine-tuning units) | April 14, 2027 |

Quota is subscription-specific and can change after this check. `infra/preflight.sh` is the source of truth before every rebuild or recording. `gpt-4.1-mini` is intentionally accepted for the December 2026 delivery because it remains supported until April 14, 2027. `gpt-oss` models are intentionally excluded from this session.
