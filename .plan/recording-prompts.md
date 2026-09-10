# Ordered Copilot prompts for recording

These prompts are both the implementation workflow and the recording script.
Paste them manually into GitHub Copilot App in the exact order below. Send one
prompt at a time, record the useful interaction, and let Copilot finish and
verify the requested checkpoint before sending the next prompt.

The solution does not need to exist before Prompt 1. It is built progressively
by these prompts. Completed checkpoints remain in the repository and Azure, so
later prompts continue the real implementation instead of replaying mocked work.

## Before Prompt 1

The planning session must have copied `.plan/` into the repository and pushed
the implementation branch. Open a new GitHub Copilot App session on that branch.

### Prompt 0 — Verify cloud feasibility

> Read every Markdown file in `.plan/`, starting with `.plan/spec.md`,
> `.plan/decisions-and-risks.md`, `.plan/execution-map.md`, and
> `.plan/recording-prompts.md`. Use the Microsoft Foundry skill to inspect the
> active Azure identity, subscription, region, quota, hosted-agent support,
> current judge-model options, Model Router availability, training-eligible
> smaller models, Agent Optimizer access, Application Insights requirements, and
> current RBAC role names. Do not create resources or edit files. Write a
> concise feasibility report with verified model IDs, versions, prices, preview
> status, and blockers. Use `rg-brk330-concierge` as the required resource-group
> name for every later provisioning step. Stop for my review.

**Record:** optional preparation clip. **Do not continue** until every
must-have capability for Act 2 is available and Act 3/4 limitations are explicit.

## Session 1: Build and baseline

### Prompt 1 — Load the specification

> Read `.plan/spec.md`, `.plan/decisions-and-risks.md`,
> `.plan/inventory.md`, `.plan/test-prompts.md`, and `.plan/demo-1.md`.
> Inspect the repository and Azure environment without editing anything. Confirm
> the exact implementation checkpoints you will complete for Demo 1, identify
> the fixed hero prompt and 20-prompt evaluation subset, and stop for my review.

**Record:** the request, file reading, and concise plan.

### Prompt 2 — Build the application

> Implement the baseline Contoso Travel Concierge described in the approved
> plan. Create the Python Microsoft Foundry hosted agent, deterministic synthetic
> travel tools and data integration, and lightweight FastAPI HTML/CSS/JavaScript
> experience. Use one verified frontier-model deployment for every task. Enforce
> Caldova policy as a hard booking gate. Run the repository's targeted local
> validation, summarize the changed files, and stop before Azure deployment.

**Record:** representative file creation and final change summary. Remove
repetitive generation from the edited video.

### Prompt 3 — Provision and deploy

> Use the Microsoft Foundry skill and the repository infrastructure to provision
> or update the live Azure demo environment and deploy the baseline hosted agent
> and FastAPI site. Ensure Application Insights is connected and required role
> assignments are applied. Create or reuse only the resource group
> `rg-brk330-concierge`. Execute the full operation, verify the deployment,
> report the operation IDs and URLs, and do not claim success until the live
> health and agent smoke tests pass.

**Record:** the provisioning/deployment command or action and the accepted job.
Stop recording during elapsed cloud wait. Resume only after Copilot reports the
verified result.

### Prompt 4 — Run the hero and policy-block cases

> Invoke the live deployment with TP-01 and its receipt asset, then invoke the
> designated noncompliant booking case. Verify the first response completes every
> requested task and cites Caldova policy. Verify the second case blocks the
> prohibited action. Show the web URL and concise evidence for both outcomes.

**Record:** both live interactions.

### Prompt 5 — Generate evaluated baseline traffic

> Run the fixed 20-prompt subset against the deployed baseline using the
> evaluation setup approved for Act 2. Preserve prompt IDs, capture traces, and
> persist the result manifest with quality, compliance, latency, token use, and
> cost units. Verify the completed evaluation and give me the Foundry portal URLs
> for the run and related traces.

**Record:** job start, then pause. Resume at the verified completed evaluation.

### Prompt 6 — Prepare the Insights reveal

> Verify the prerequisites for Foundry Insights, including evaluated trace data,
> the judge model, Application Insights connection, and the project managed
> identity's monitoring role. Run or inspect the prepared Insights scan. Select
> one evidence-backed issue relevant to quality, tool use, latency, or token cost,
> and give me the exact portal navigation and related trace to show. Do not
> modify the agent.

**Record:** portal navigation, finding, and linked trace.

## Session 2: Hill climb

Continue from the completed baseline checkpoint. Start a new Copilot App session
on the same branch if a clean conversation is desirable; the committed files,
Azure resources, operation IDs, and result manifest remain the handoff.

### Prompt 7 — Create the Caldova rubric

> Read `.plan/spec.md`, `.plan/test-prompts.md`, and `.plan/demo-2.md`.
> Use the Microsoft Foundry skill to create or register the Caldova rubric
> evaluator, review its dimensions and weights against the specification, and
> run it on the fixed 20-prompt baseline. Verify the completed run, persist the
> results, and stop with the portal URL and one representative failure.

**Record:** rubric creation/review, job start, and completed portal result.

### Prompt 8 — Add task decomposition and Model Router

> Implement task decomposition for the compound travel workflow and route each
> independent task through the verified Model Router deployment. Never send the
> full compound request as a single routed task. Add telemetry that records the
> selected model for every task. Run targeted local validation, show the focused
> diff, and stop before deployment.

**Record:** request, focused diff, and task graph.

### Prompt 9 — Deploy and compare the routed candidate

> Deploy the routed candidate to the live Azure environment. Run the same fixed
> 20 prompt IDs with the same rubric and settings. Verify the completed run and
> produce a baseline-versus-router comparison with separate quality, compliance,
> latency, token, cost-per-call, cost-per-request, and cost-per-trip values.
> Highlight any quality regression and do not select a winner.

**Record:** deployment start, then completed portal comparison and route evidence.

### Prompt 10 — Prepare trace-derived training data

> Analyze the baseline and routed traces, select high-quality frontier responses
> and representative routed failures, and create a versioned training dataset
> with provenance. Verify that no sensitive or real customer data is present.
> Report dataset counts and validation findings, then stop before starting
> training.

**Record:** dataset summary and validation.

### Prompt 11 — Start supported student-model training

> Use the Microsoft Foundry skill to discover a currently available smaller model
> that supports the intended distillation or fine-tuning workflow in this region.
> Show the evidence for eligibility. If none is available, stop without choosing
> a substitute. Otherwise start the real training job with the approved dataset,
> report the operation ID, and stop without waiting or claiming completion.

**Record:** catalog/eligibility evidence and training-job start.

### Prompt 12 — Verify and compare the student

> Check the existing training operation from Prompt 11; do not start a new one.
> If it completed successfully, deploy the resulting model, run the same fixed
> 20 prompts, and compare baseline, routed, and student configurations using the
> same rubric and separate metrics. Accept the student only if it meets the
> quality threshold and passes every policy gate. Persist the measured results.

**Record:** completed job, deployment, and three-way comparison.

## Session 3: Automate

Continue from the completed optimization-ready checkpoint. Start a new Copilot
App session on the same branch if a clean conversation is desirable.

### Prompt 13 — Verify Agent Optimizer readiness

> Read `.plan/spec.md`, `.plan/demo-3.md`, and the measured result manifest.
> Verify that the Python hosted agent is optimization-ready, the baseline is
> immutable, the fixed 20-prompt dataset and Caldova rubric are available, and
> the trace-derived evidence is current. Do not launch optimization. Give me the
> exact Foundry portal navigation and configuration values to use while recording.

**Record:** readiness summary, then switch to the portal.

### Portal step 1 — Start optimization

In Foundry, select the verified agent, evidence set, evaluator, and goals. Start
the run and record the confirmation. Stop recording during processing.

### Prompt 14 — Verify the existing optimizer run

> Check the Agent Optimizer operation I just started; do not create another run.
> Verify completion and provide the portal URL, candidate IDs, metric summary,
> and any warnings. Do not apply or deploy a candidate.

**Record:** Copilot's verification, then return to the completed portal run.

### Portal step 2 — Review and promote

Record:

1. Candidate comparison.
2. Proposed changes and row-level evidence.
3. Quality, compliance, latency, and cost tradeoffs.
4. The explicit human selection.
5. Promotion only after the presenter approves it.

### Prompt 15 — Verify the promoted result

> Verify the selected Agent Optimizer candidate and version lineage after my
> portal action. Run the fixed smoke cases against the promoted version and
> confirm that policy blocking, quality threshold, and deployment health still
> pass. Persist the final result manifest.

**Record:** final verification and close on the measured outcome.

## Recovery prompt

Use this after any interrupted cloud operation:

> Inspect the existing operation IDs and deployed resources from the latest
> checkpoint. Do not start replacement jobs. Report which operations succeeded,
> failed, or remain in progress, preserve successful state, and continue only
> from the first incomplete checkpoint.
