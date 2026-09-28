# Troubleshooting

Record reproducible failures and verified fixes here as the session evolves. Include the symptom, root cause, validation evidence, and automation that prevents recurrence. Do not record credentials, connection strings, access tokens, or sensitive trace content.

<br/>

## Agent Insights scan cannot start

### Symptom

Microsoft Foundry reports:

> Couldn't start insights run. A required Agent Insights dependency is unavailable.

The message is generic. A healthy agent, an Application Insights connection, and ingested traces are necessary but not sufficient for a Hosted Agent scan.

### Current official prerequisites

The deployment follows [Use Insights in Foundry (preview)](https://learn.microsoft.com/azure/foundry/observability/how-to/agent-insights#prerequisites) and the [Microsoft Foundry RBAC guidance](https://learn.microsoft.com/azure/foundry/concepts/rbac-foundry?tabs=owner%2Cfoundry#built-in-roles).

| Principal or dependency | Required configuration | Repository automation |
|---|---|---|
| Interactive presenter using a Hosted Agent | **Foundry Project Manager** on the parent Foundry account | `infra/supplemental.bicep` |
| Interactive presenter | **Monitoring Reader** on the connected Application Insights resource | `infra/supplemental.bicep` |
| Foundry project managed identity | **Foundry User** on the parent Foundry account | `infra/supplemental.bicep` |
| Foundry project managed identity | **Monitoring Reader** on the connected Application Insights resource | `infra/supplemental.bicep` |
| Judge model | GPT-5 or newer deployment that the Insights backend supports | Manually deploy `insights-judge` (`gpt-5.6-sol`, GlobalStandard capacity 100) and select it under Insights **Configuration** |
| Telemetry | Recent representative traces for the exact agent | Replay HERO, BLOCK, EVIDENCE, and ACCESS |
| Project connection | Shared `ApplicationInsights` connection targeting the session component | `infra/supplemental.bicep` |

The presenter might also inherit **Foundry User** from a broader scope. That does not replace the documented **Foundry Project Manager** requirement for Hosted Agent Insights.

If `AppGenAIContent` is configured as a protected table, every identity that reads protected content also needs **Privileged Monitoring Data Reader**. Do not assign that privileged role by default. First verify that table protection is enabled, then scope the role to Application Insights for resource-scoped queries or to the Log Analytics workspace for workspace-scoped queries. In the validated test environment, the `protectGenAISensitiveData` feature is not registered, so the privileged role is not required.

### Recovery procedure

1. Reapply the idempotent supplemental deployment:

   ```bash
   bash infra/deploy-supplemental.sh
   ```

2. Validate the deployment and telemetry:

   ```bash
   bash infra/validate-deployment.sh
   ```

3. Replay all four baseline cases to generate fresh successful, blocked, receipt, and accessibility traces.
4. In Foundry, open `contoso-travel` > **Insights**.
5. Under **Configuration**, select `insights-judge` (`gpt-5.6-sol`) as the judge model.
6. Refresh the page after RBAC propagation, then select **Run scan now**.

If the scan still fails after every check passes, capture the subscription and project IDs, agent name/version, UTC failure time, screenshot, and request ID when available. Agent Insights is a preview service, so the remaining failure can be service capacity, regional enablement, or another backend dependency. Do not repeatedly reset or recreate a monitor while a run is active.

### What we learned

- **Foundry User** for the project identity fixed documented data-plane access but did not satisfy all Hosted Agent Insights prerequisites.
- Azure **Reader** on Application Insights is not the documented trace role. Use **Monitoring Reader**.
- A Hosted Agent's interactive user needs **Foundry Project Manager**, whereas a Prompt Agent user needs only **Foundry User**.
- The scan requires a configured GPT-5-or-newer judge deployment. Mini and nano variants are supported, but a larger model is recommended for insight quality.
- A successful empty Insights retrieval means no findings were generated. It is different from a scan dependency failure.
- In the validated environment, runs using `gpt-5.4` failed immediately with `ServiceUnavailable`; switching the monitor to `insights-judge` backed by `gpt-5.6-sol` succeeded. A model can satisfy the broad GPT-5-or-newer documentation and still be unavailable to the preview Insights backend.
- Judge deployment remains a manual demo prerequisite so attendees explicitly see preview model compatibility and quota. It can be automated later after the supported model contract stabilizes.

<br/>

## Application Insights CLI extension cannot install

### Symptom

Dynamic installation of `application-insights` fails with:

> Pip failed with status code 1.

Azure CLI `2.45.0` in this container runs on `/usr/bin/python3`, which initially has no pip module.

### Fix and automation

`.devcontainer/post-create.sh` installs Debian `python3-pip` only when `/usr/bin/python3 -m pip` is unavailable, then installs `application-insights` version `0.1.19` idempotently.

The user-level extension is located at:

```text
~/.azure/cliextensions/application-insights
```

Verify it with:

```bash
az extension show --name application-insights \
  --query '{name:name,version:version,path:path}' -o json
```

This extension enables the read-only telemetry query in `infra/validate-deployment.sh`. Foundry Agent Insights does not depend on the local CLI extension.

<br/>

## Rubric generation poller reports Evaluations preview header missing

### Symptom

The evaluator generation job is created, but the Python SDK poller fails on a GET request:

> `This operation requires ... Foundry-Features: Evaluations=V1Preview`

### Cause and recovery

In `azure-ai-projects 2.6.1`, the evaluator-generation initial request receives the preview header through `allow_preview=True`, but the generic long-running-operation poller can omit it from status GET requests. The server-side job can still succeed and create the evaluator.

`src/scripts/setup_lightweight_evaluation.py` starts generation without SDK polling, then calls `get_generation_job` with the explicit preview header until a terminal state. Rerunning `--apply` first reuses an existing evaluator version and does not create a duplicate.

<br/>

## Generated rubric says the Hosted Agent has no instructions

### Symptom

The evaluator details show:

> `Generated with input-quality warnings: The agent has no instructions.`

### Meaning and mitigation

Foundry can retrieve full instructions from prompt agents, but a Hosted Agent's instructions are packaged inside its deployed code/configuration. The Agent generation source therefore contributes description and tool metadata but cannot expose the complete instruction text.

This repository supplies the full baseline instructions and Caldova policy in the explicit Prompt source, plus the frozen expected-behavior dataset. The generated v1 dimensions are domain-specific and cover the observed Insights findings, so the warning does not invalidate the evaluator. Review and pin the returned definition rather than generating repeatedly to remove a cosmetic warning.

Do not clone the evaluator solely to hide the warning. Create a new evaluator version only when a reviewer changes dimensions, descriptions, weights, applicability, or threshold.

<br/>

## RBAC scope notes

- Use **Foundry Agent Consumer** at project or agent scope for applications that only invoke an endpoint.
- The Travel Concierge Portal additionally receives **Foundry User** at account scope because it reads the active endpoint selector and immutable version metadata. An invocation-only application should omit that role.
- Do not use **Azure AI Developer** for current Foundry projects or Hosted Agents; Microsoft documents it for Azure Machine Learning workspaces and earlier Foundry hubs.
- Existing test resources can retain older redundant assignments from iterative development. Fresh deployments follow `infra/rbac-matrix.md`. Never remove roles or resources from the protected `rg-brk330-concierge` reference environment.
- The session ACR is explicitly configured for **RBAC Registry Permissions**, so its web identity uses **AcrPull**. Use **Container Registry Repository Reader** only when a registry is explicitly configured for **RBAC Registry + ABAC Repository Permissions**.

<br/>

## Fresh Hosted Agent deploy reports Project not found

### Symptom

Provisioning succeeds, but the first Hosted Agent deployment fails within seconds:

> `create_agent ... 404 NotFound: Project not found`

### Cause

The Foundry project ARM resource is complete before its data-plane endpoint has finished registering. An immediate `azd deploy contoso-travel` can therefore race the new project.

### Fix and recovery

`infra/setup.sh` now waits for `AIProjectClient.agents.list()` to succeed before deploying the initial agent. It retries only transient `404`, `409`, `429`, and `5xx` responses for up to 150 seconds.

Resume the same generated environment by passing its suffix; do not create another environment and do not run the individual deployment commands manually:

```bash
bash infra/setup.sh \
   --subscription ai-team \
   --location swedencentral \
   --suffix 340368
```

Provisioning and supplemental deployment are idempotent. The fixed script selects the existing `brk330-340368` environment, verifies data-plane readiness, and continues the supported deployment sequence.

<br/>

## First supplemental deployment reports InvalidPrincipalId

### Symptom

The first supplemental deployment fails before Hosted Agent v1 exists:

> `InvalidPrincipalId: The Principal ID 'ERROR: key not found in environment values ...' is not valid.`

### Cause

`azd env get-value` prints missing-key diagnostics to stdout. Command substitution captured that diagnostic as the Hosted Agent principal ID during the pre-agent infrastructure pass.

### Fix and recovery

`infra/deploy-supplemental.sh` now reads the complete azd environment map and returns an empty principal ID when the Hosted Agent identity has not been created. Bicep skips agent-specific monitoring roles on the first pass. After v1 deploys, the second idempotent supplemental pass receives the real GUID and creates those assignments.

Resume the same environment through `infra/setup.sh --suffix NNNNNN`; do not run the failed Bicep deployment manually.

<br/>

## Placeholder web revision reports Activation failed

### Symptom

The `contoso-travel-web` placeholder revision reports:

> `Deployment Progress Deadline Exceeded. 0/1 replicas ready.`

Its console log says:

> `Listening on :80...`

### Cause

The public `mcr.microsoft.com/k8se/quickstart:latest` placeholder listens on port 80, while the Container App ingress originally targeted the final FastAPI port 8080. Azure could run the container but could not mark its revision ready.

### Fix and recovery

Supplemental Bicep now selects port 80 for the public placeholder and port 8080 for the real portal image. After `azd deploy web`, setup runs one final idempotent supplemental pass to preserve the deployed image and enforce the final registry, identity, ingress, and RBAC configuration.

Let an already-running ARM deployment finish or fail; do not overlap another deployment. Then resume the same environment through `infra/setup.sh --suffix NNNNNN`.

### Preserve agent version on resume

The Hosted Agent can already be active before a later supplemental or portal step fails. Setup checks for an existing active `contoso-travel` agent and reuses it, preserving baseline v1. It deploys the agent only when the project returns `404` for that exact agent name. A non-active existing version stops setup for diagnosis rather than creating another version.