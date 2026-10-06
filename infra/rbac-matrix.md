# RBAC capability matrix

Roles are resolved by name during deployment so current Azure role-definition IDs are used. The setup principal must be able to create resources and role assignments.

The assignments follow the current [Microsoft Foundry RBAC guidance](https://learn.microsoft.com/azure/foundry/concepts/rbac-foundry?tabs=owner%2Cfoundry#built-in-roles) and [Agent Insights prerequisites](https://learn.microsoft.com/azure/foundry/observability/how-to/agent-insights#prerequisites). See [`docs/troubleshooting.md`](../docs/troubleshooting.md) for rationale and recovery steps.

| Principal | Scope | Role | Capability validated |
|---|---|---|---|
| Signed-in presenter | Subscription or generated resource group | Owner, or equivalent resource-create plus role-assignment permissions | Provision the isolated environment and assign least-privilege runtime roles. |
| Signed-in presenter | Foundry account | Foundry Project Manager | Required for Hosted Agent Insights and project development workflows. |
| Signed-in presenter | Application Insights | Monitoring Reader | Read traces and monitoring evidence in the portal/query APIs. |
| Foundry project managed identity | Foundry account | Foundry User | Let Agent Insights resolve Hosted Agent data-plane metadata and run analysis. This matches the known-good reference deployment. |
| Foundry project managed identity | Provider-managed resources | Provider-assigned roles | Build and pull Hosted Agent images, invoke models, and connect platform telemetry. The Foundry provider owns these assignments. |
| Hosted Agent version identity | Foundry project/model access | Provider-assigned roles | Invoke configured models/tools. Each immutable version receives its platform identity and provider access. |
| Hosted Agent version identity | Application Insights | Monitoring Reader | Let Insights correlate/read the agent's monitoring evidence. |
| Hosted Agent version identity | Application Insights | Monitoring Metrics Publisher | Emit telemetry when Entra-based monitoring authorization is used. |
| FastAPI user-assigned identity | Foundry project | Foundry Agent Consumer | Invoke `contoso-travel` without broader development access. |
| FastAPI user-assigned identity | Foundry account | Foundry User | Read the endpoint version selector and immutable version metadata displayed by the demo surface. The Hosted Agent data plane evaluates `AIServices/agents/read` at the parent account scope. |
| FastAPI user-assigned identity | Session ACR | AcrPull | Pull the deployed web image from the explicitly configured RBAC-mode registry. |
| FastAPI user-assigned identity | Application Insights | Monitoring Metrics Publisher | Export FastAPI traces and metrics. |

## Validation

- `infra/preflight.sh` checks presenter authentication, subscription, model catalog, and core prerequisites before resource creation.
- `infra/deploy-supplemental.sh` resolves role IDs and deploys runtime assignments idempotently.
- `infra/03-check.sh` checks the five model deployments, the agent, web health, web identity assignments, and trace ingestion.
- Fine-tuning and evaluation commands use the signed-in presenter identity and the scoped Foundry roles established by setup; preflight stops when required access is unavailable.

Do not copy role GUIDs from the prototype. If a documented role cannot be resolved by name, setup stops rather than substituting a broader role silently.
