# Demo builder guide

Use this guide in a new GitHub Copilot App session after the planning package is
approved and copied into the repository.

Read [`execution-map.md`](execution-map.md) and
[`recording-prompts.md`](recording-prompts.md). The presenter uses the ordered
prompts to build the real solution progressively while recording. There is no
separate hidden implementation pass.

## Start the build session

Open a new repository session on the implementation branch and begin with
Prompt 0 in `recording-prompts.md`. After feasibility is confirmed, continue
with Prompt 1. The following combined kickoff is retained only as a recovery
option:

> Build the BRK330 Contoso Travel Concierge demo end to end. Read
> `.plan/spec.md`, `.plan/decisions-and-risks.md`, `.plan/inventory.md`,
> `.plan/test-prompts.md`, and `.plan/demo-1.md` through `.plan/demo-3.md` before
> planning. Use the Microsoft Foundry skill for every Foundry workflow. Preserve
> existing authored AI Tour content. Implement in dependency order, validate each
> cloud checkpoint, and do not invent model availability, prices, evaluation
> scores, links, or preview results.

## Mandatory first checks

1. Confirm the active Azure identity, subscription, and deployment region.
   Use `rg-brk330-concierge` as the resource group.
2. Confirm quota and availability for:
   - A frontier baseline model
   - A supported judge model
   - Model Router
   - At least one smaller training-eligible model
   - Agent Optimizer
3. Confirm the project can use hosted Python agents.
4. Confirm Application Insights connectivity and the current role required for
   the Foundry project managed identity.
5. Record actual model IDs, versions, prices, region, and preview status in a
   generated environment manifest.
6. Read the repository placement contract in `spec.md` and confirm that no
   proposed implementation file falls outside `src/`, `data/`, `infra/`,
   `docs/`, or the explicitly allowed root `azure.yaml`.

Stop if any required capability is unavailable. Propose the smallest truthful
scope adjustment instead of substituting an unverified model or fake result.

## Build order

## Recording approach

Long-running cloud operations must remain real, but their idle time does not
belong in the final recording. For each deployment, evaluation, training, or
optimization job:

1. Record the configuration and the action that starts the job.
2. Stop recording after the portal or CLI confirms the job was accepted.
3. Let the real job finish and verify its result.
4. Start a new recording at the completed result.
5. Join the clips with a short transition such as “After the run completes.”

This editing approach shortens the audience-visible demo without simulating the
operation or fabricating its outcome.

The builder must still execute every step fully. Prepared checkpoints are
outputs of the real implementation workflow, not mocked states created only for
recording.

### Checkpoint 1: Infrastructure and identity

- Provision the Foundry project, models, Application Insights, web hosting, and
  managed identities.
- Apply least-privilege role assignments.
- Verify RBAC propagation and trace ingestion before application work continues.

### Checkpoint 2: Synthetic data

- Author Caldova policy and deterministic travel catalogs.
- Generate English and French synthetic receipts.
- Export the 50 prompts and fixed 20-prompt subset to machine-readable JSONL.
- Define expected tasks, tool calls, policy outcomes, and rubric fields.

### Checkpoint 3: Baseline agent and web app

- Build the Python hosted agent and FastAPI experience.
- Implement deterministic tools and dry-run booking.
- Add OpenTelemetry-compatible trace correlation.
- Deploy to Azure and run the hero request.
- Verify the noncompliant request is blocked.

### Checkpoint 4: Evaluated baseline

- Create or register the Caldova rubric evaluator.
- Run the fixed 20-prompt dataset against the baseline.
- Persist row-level and aggregate results.
- Capture baseline quality, compliance, latency, tokens, and cost.
- Verify traces and evaluations appear in Foundry.

### Checkpoint 5: Task decomposition and Model Router

- Decompose compound requests before routing.
- Send each task independently to Model Router.
- Capture selected model metadata per task.
- Re-run the same 20 prompts and compare against baseline.

### Checkpoint 6: Student-model experiment

- Curate trace-derived teacher examples.
- Discover and validate a training-eligible smaller model.
- Run the supported training workflow.
- Deploy and evaluate the student on the same 20 prompts.
- Do not claim success unless measured quality meets the agreed threshold and
  policy compliance remains a hard pass.

### Checkpoint 7: Insights and Agent Optimizer

- Generate enough evaluated trace data for Insights.
- Capture an Insights finding and related traces.
- Run Agent Optimizer in the portal.
- Compare candidates and inspect changes.
- Capture human review and the promotion decision.

### Checkpoint 8: Recording and documentation

- Record each demo using its runbook and documented edit points.
- Capture every fallback clip and screenshot listed there.
- Replace all `<measured after dry run>` tokens with real results.
- Update README, docs, delivery resources, and attendee instructions only within
  their approved scope.

## Non-negotiable verification

- [ ] Agent and web source live under `src/`.
- [ ] Synthetic and evaluation assets live under `data/`.
- [ ] Azure provisioning and RBAC live under `infra/`.
- [ ] Supporting technical documentation lives under `docs/`.
- [ ] `delivery-resources/` still contains only its single `README.md`.
- [ ] `instructions/` remains unchanged unless self-paced guidance is approved.
- [ ] The product is always named Contoso Travel Concierge.
- [ ] Caldova owns the travel policy.
- [ ] Krystal is the hero user.
- [ ] Policy violations block action.
- [ ] Model Router receives decomposed tasks.
- [ ] All candidate comparisons use the same 20 prompt IDs.
- [ ] Quality, compliance, latency, and cost are separate.
- [ ] Student model support is verified, not assumed.
- [ ] Agent Optimizer does not auto-promote.
- [ ] Every slide number is backed by a measured result or clearly marked pending.
