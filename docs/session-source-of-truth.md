# BRK330 session source of truth

This document is the working source of truth for rebuilding BRK330 for delivery. It is based on:

- `AITour27-BRK330.pdf`, especially the outline, demo transitions after slides 15, 29, and 35, and the closing principles.
- [Ship agents faster with expanded model choice, voice agents, and continuous optimization](https://azure.microsoft.com/en-us/blog/ship-agents-faster-with-expanded-model-choice-voice-agents-and-continuous-optimization/), especially "Turn production evidence into continuous improvement."
- The BRK240 repository under `REFERENCE ONLY/`, used as a quality reference for delivery-ready structure and guidance.

## Breakout narrative

Caldova has one travel concierge and three definitions of success:

- **Krystal, the traveler:** useful, policy-compliant travel support.
- **Andre, the CFO:** defensible quality, cost, and latency tradeoffs.
- **Lydia, the architect:** an improvement process that keeps pace with changing models, requirements, and capabilities.

Contoso addresses these needs in three acts:

1. **Make it work**
   Build, deploy, and observe a hosted concierge using a frontier model. Production traces reveal behavior, quality, latency, and cost.
2. **Make it better**
   Define what good means using Caldova's requirements and rubric. Establish a baseline on representative evidence, then hill-climb one optimization lever at a time.
3. **Make it scale**
   Use production evidence and trusted evaluators to automate candidate experimentation with Agent Optimizer. A human reviews and promotes the winner.

The operating model underneath all three acts is:

**Observe -> Understand -> Evaluate -> Optimize -> Validate -> Repeat**

Production is the beginning of the improvement loop, not its conclusion.

## Demo narrative

### Demo 1: Build with GitHub Copilot

**After slide 15: Make it work**

- GitHub Copilot builds, deploys, and tests the hosted travel concierge.
- Start with one frontier model serving all jobs.
- Inspect production traces and Insights in Foundry.
- Reveal a recurring policy-evidence gap: the agent can claim compliance without consistently grounding the decision in policy-tool evidence or citing the relevant CT rule.

**Loop stages:** Observe and Understand.

### Demo 2: Measure and optimize the model strategy

**After slide 29: Make it better**

- Define Caldova's approved rubric.
- Establish a repeatable baseline.
- Pull one hill-climb lever at a time.
- Lever 1: replace the frontier deployment with Model Router, enabling dynamic multi-model routing by task.
- Lever 2: distill behavior from quality-filtered frontier traces into a smaller fine-tuned student model.
- Measure each option against the same evidence and criteria.
- Keep or reject each change based on quality, policy compliance, cost, and latency evidence.

**Loop stages:** Evaluate, Optimize, and Validate.

The outcome is not predetermined. A regression is evidence: reject the change, preserve the last accepted configuration, and pull another lever.

### Demo 3: Automate with Agent Optimizer

**After slide 35: Make it scale**

- Start from production traces, agent configuration, and trusted evaluators.
- Use GitHub Copilot to run Agent Optimizer from code or CLI and generate approximately three candidates.
- Evaluate and rank every candidate with the frozen evaluation contract.
- Optimize across prompts, tools, skills, and model choice.
- Independently validate the recommendation for policy, quality, cost, and latency regressions.
- Record a human promote, reject, or hold decision.
- Return the improved agent to production observation.

**Loop stages:** Automate the full cycle and Repeat.

Promotion remains human-controlled. Rejection is an equally valid result when validation exposes a regression.

## Demo delivery contract

- All three demos use canonical prerecorded voice-over videos by default.
- Presenters can mute the same videos and narrate them live; duplicate no-audio exports are not required.
- Each runbook includes a transcript, timecoded beats, expected duration, and click or transition cues.
- Prefer toggleable platform captions rather than burned-in narration captions.
- Presenters receive complete rebuild instructions and may deliver live after rehearsal, but live execution is optional.
- Insights findings, routing decisions, rubric scores, training results, and optimizer candidates are nondeterministic. Presenters report their own measured results rather than attempting to force the canonical outcome.
- Raw capture can take as long as required. Record real operation starts and verified results, then edit idle cloud time and repetition without fabricating continuity or outcomes.
- Final edited duration targets are:
   - Demo 1: 4 minutes.
   - Demo 2: 6 minutes.
   - Demo 3: 5 minutes.
   - Total demo time: no more than 15 minutes.

## Demo 1 contract: Observe and understand

The hero products are Microsoft Foundry Hosted Agents and Insights in Foundry. Demo 1 stops before rubric generation and batch evaluation.

Agent v1 must be useful but imperfect:

- The hero request succeeds.
- A simple noncompliant request is blocked with a CT-rule citation.
- Repeatable edge cases expose missing policy-tool evidence or incomplete CT-rule citations.
- Existing TP-02, TP-03, TP-11, and TP-19 scenarios provide the starting evidence.

Create a dedicated, versioned Insights seed set from existing fixtures and scenarios. Do not modify the fixed 20-prompt comparison dataset. Persist:

- Seed prompts and expected tools, rules, and outcomes.
- Replay command and run window.
- Trace and response IDs.
- Finding title and identifier.
- Supporting evidence, likely cause, and recommended action.
- Reproduction status and fallback screenshot.

Exact Insights wording is not guaranteed. The underlying traces and expected evidence gaps must be reproducible, while the canonical screenshot and recording provide the delivery fallback.

### Copilot recording experience

Use GitHub Copilot Agent mode in VS Code from a clean recording checkpoint, with the Microsoft Learn MCP server enabled. Copilot should use the Foundry Dev Pack and the current `microsoft.foundry` and `azd ai agent` golden path. It must pause before provisioning, deploying, or deleting cloud resources so the developer visibly reviews each checkpoint.

The starting kickoff prompt is:

```text
Build the "Make it work" checkpoint for BRK330.

Read the repository's Demo 1 brief, architecture guidance, fixture
documentation, and acceptance criteria before changing files. Use the
Microsoft Learn MCP server to verify all Microsoft Foundry SDK, CLI,
hosting, tracing, and deployment choices against current official
documentation.

Follow the current Microsoft Foundry hosted-agent golden path:
- Python 3.13
- Responses protocol
- Agent Framework
- Azure Developer CLI with the microsoft.foundry extension
- Microsoft Foundry hosted agent named contoso-travel
- a FastAPI web experience that calls the hosted agent
- built-in trace instrumentation connected to Application Insights

Build only the baseline "Make it work" experience:
- one verified frontier model for all tasks
- deterministic Caldova travel fixtures and tools
- travel policy enforced as a hard gate
- the Krystal hero request and one noncompliant request
- one external, version-controlled agent instruction source
- reproducible setup and teardown using a new randomly named resource
   group: rg-aitour-brk330-<number>

Never access or modify rg-brk330-concierge.

First inspect the repository, verify the applicable Foundry quickstarts,
propose the implementation plan and expected files, and stop for review.
Do not provision, deploy, delete, or modify Azure resources until I
explicitly approve that checkpoint.
```

### Demo 1 acceptance

- The documented prompt rebuilds the baseline from the clean checkpoint.
- One setup flow deploys the hosted agent and FastAPI app to a random `rg-aitour-brk330-<number>` resource group.
- The FastAPI health endpoint passes.
- The hero request succeeds and the noncompliant request blocks with a CT citation.
- Agent and tool spans appear in Foundry traces.
- Insights seed replay produces the expected underlying policy-evidence gaps.
- The canonical Insights record contains trace IDs, evidence, reproduction steps, and a screenshot.
- One teardown flow purges the test resource group.
- The final recording and transcript accurately reflect the verified run.

## Demo 2 contract: Evaluate, optimize, and validate

Demo 2 asks whether the model can be right-sized for the task. It demonstrates two potential optimization levers, not two predetermined improvements.

- Baseline: one frontier model handles every job.
- Model Router: change only the model strategy; keep the instruction hash unchanged.
- Trace-based distillation: train a smaller model from quality-filtered frontier traces; keep the instruction hash unchanged.
- Run every variant against the same dataset, rubric evaluator version, judge configuration, and constraints.
- Report quality dimensions, policy gate, cost, and latency separately rather than manufacturing a composite winner.
- Reuse a lever in future iterations when new models, requirements, or evidence warrant it.

### Demo 2 acceptance

- Generate the rubric from Demo 1 context and traces, then review, refine, and pin it.
- Version the fixed 20 prompts and expected behaviors.
- Complete the baseline evaluation under the frozen evaluation contract.
- Verify Router changes only the model strategy and retains the baseline instruction SHA.
- Record the distillation source traces, train and validation data, provenance, training job, and deployed student identifiers.
- Verify the student retains the baseline instruction SHA.
- Evaluate baseline, Router, and student with identical evidence and settings.
- Rerun the Insights seed set as a regression gate.
- Preserve the actual outcome without forcing a winner.
- Link every result to its configuration, instruction SHA, agent version, and raw output.
- The final recording and transcript accurately reflect the verified runs.

The last accepted Demo 2 configuration becomes Demo 3's immutable optimizer baseline.

## Demo 3 contract: Automate and repeat

- GitHub Copilot runs Agent Optimizer from code or CLI; the portal can be used to inspect results.
- Generate approximately three candidates to keep the recording and cloud run manageable.
- Use the exact frozen dataset, evaluator version, judge, and constraints.
- Record the job ID and status, baseline score, candidate IDs and scores, configuration differences, recommendation, and supporting evidence.
- Preserve all generated candidate configurations unchanged.
- An improved aggregate score is necessary but not sufficient for promotion.

### Demo 3 acceptance

- Capture the last accepted Demo 2 configuration as the optimizer baseline.
- Complete the optimizer run and preserve all provenance.
- Independently test the recommended candidate with:
   - The hero request.
   - The policy-block request.
   - The Insights seed regression set.
   - The policy hard gate.
   - Quality, cost, and latency review.
- Record an explicit human promote, reject, or hold decision.
- Promote only after approval; rejection retains the prior version.
- Document and test rollback.
- The final recording and transcript accurately show the real outcome.

## Evaluation contract

The Rubric Evaluator is the primary quality measure. Cost and latency remain separate operational metrics.

### Rubric creation

After Demo 1:

1. Replay the Insights seed set and collect production-like traces.
2. Auto-generate a candidate rubric using the Foundry agent, explicit system prompt, Caldova policy and reference files, fixed dataset, and traces.
3. Review the generated dimensions in the recording.
4. Refine or manually author the approved dimensions.
5. Create an immutable evaluator version and export its exact returned definition and provenance.
6. Pin the evaluator name and version, judge deployment and configuration, dataset version, and pass threshold.

For hosted agents, the generation service obtains the agent description rather than the full instructions. Always provide the explicit system prompt and policy or reference files. Traces cannot be the only generation source; pair them with a base source.

### Canonical rubric dimensions

| Dimension | Weight | Purpose |
|---|---:|---|
| Policy compliance | 9 | Makes the correct policy decision; a policy violation is a hard failure. |
| Policy evidence fidelity | 6 | Uses required policy tools and cites complete, attributable CT rules. |
| Intent and task completeness | 6 | Identifies and completes every requested task. |
| Tool-use accuracy | 5 | Uses required tools with correct, grounded arguments. |
| Travel-plan correctness | 5 | Produces feasible, fixture-backed itinerary choices. |
| Receipt accuracy | 4 | Correctly extracts, reconciles, and converts receipt data. |
| General quality | 4 | Measures grounding, honesty, and uncertainty handling; always applicable. |
| Communication clarity | 2 | Produces an actionable, concise, correctly structured response. |

The dedicated policy regression gate prevents an improved weighted average from hiding a compliance failure.

### Freeze rule

Baseline, Router, student, and optimizer candidates must use the identical evaluator name and version, dimension definitions and weights, pass threshold, judge model configuration, and dataset version. Any change creates a new evaluation contract and requires rerunning every variant to be compared. Never combine results from different contracts in one comparison table.

After the demos, mention that evaluators can themselves evolve from new production traces. Evaluator optimization is conceptual only and is not part of the recorded workflow.

## Experiment and instruction reproducibility

- Never hard-code the active agent prompt in runtime code.
- Load the selected configuration and instruction artifact at runtime.
- Treat every instruction revision as immutable and named.
- Model-only Router and student experiments reuse the exact baseline instruction SHA.
- Treat an instruction change as its own hill-climb lever and experiment.
- Store Agent Optimizer candidate configurations unchanged.
- Promotion selects the accepted configuration without deleting baseline or rejected history.
- Every experiment manifest records:
   - Parent configuration and changed lever.
   - Configuration path, instruction path, and instruction SHA256.
   - Model deployment and agent version.
   - Git commit.
   - Dataset name and version.
   - Evaluator name and version, judge, threshold, and settings.
   - Raw result and evidence paths.
   - Quality dimensions, policy-gate result, cost, and latency.
   - Human decision and rationale.

## Session objectives

By the end of the breakout, attendees can:

- Build, deploy, and observe a Microsoft Foundry hosted agent using GitHub Copilot.
- Define business-specific success and evaluate representative and production evidence across quality, cost, and latency.
- Apply and automate a controlled continuous-improvement loop across models, prompts, skills, tools, and context, validating before promotion.

## Audience path

The self-paced experience requires access to Microsoft Foundry in an Azure subscription. Do not create a local mock or imply that canonical recordings are a hands-on substitute.

### Core path

Every attendee with the required cloud access can:

- Run a fail-fast prerequisite check.
- Deploy the hosted agent and FastAPI application into a uniquely named resource group.
- Run the hero and policy-block scenarios.
- Inspect Foundry traces.
- Run the baseline evaluation.
- Tear down and purge the environment.

### Optional advanced path

Attendees can continue with these stages when their subscription, region, quota, time, cost tolerance, and preview access support them:

- Model Router.
- Trace-based distillation and fine-tuning.
- Agent Optimizer.

The repository includes canonical recordings and evidence for delivery and comparison, but attendees must report their own measured results. They must not force their runs to match canonical Insights findings, routes, rubric scores, training outcomes, or optimizer candidates.

### Prerequisites

Document these before any deployment instructions:

- Azure subscription and active billing.
- Permission to create a resource group, provision required resources, and assign RBAC roles.
- A supported Microsoft Foundry region.
- Required model availability and quota for the core path.
- Foundry Dev Pack, including supported `az`, `azd`, and `microsoft.foundry` extension versions.
- Python and repository tooling required by the golden-path samples.
- GitHub Copilot access and Microsoft Learn MCP for rebuilding the recorded Copilot workflow.
- Estimated resource types, likely costs, and the obligation to run teardown.
- Additional model, quota, regional, training, and preview or allow-list requirements for each advanced stage.

### Automation contract

- One read-only preflight validates identity, subscription, permissions, tooling, region, model availability, quota, and advanced capability access before resource creation.
- Core prerequisite failures stop before provisioning.
- Advanced prerequisite failures disable only the affected optional stages.
- One setup flow generates a random `rg-aitour-brk330-<number>` name and deploys the complete core environment.
- One teardown flow deletes and purges that generated resource group so the workflow can be repeated.
- Neither flow accesses or modifies the prototype environment in `rg-brk330-concierge`.

## Repo-readiness objective

Create a repository that teaches and reproduces this exact story:

- Golden-path setup and complete teardown.
- One source of truth for code, instructions, data, and results.
- Deterministic evidence supporting every demo claim.
- Clear attendee instructions.
- Presenter runbooks with preflight, reset, and fallback guidance.
- Documentation centered on the continuous-optimization model and Microsoft article.
- No stale experiments, unexplained artifacts, duplicate files, or contradictory workflows.

## Repository structure principles

- Keep the first-level hierarchy simple and aligned with the AI Tour template.
- Organize `data/` as `fixtures/`, `evaluation/`, and `training/`.
- Mirror the build, evaluate, and customize stages in `src/agent/`, `src/evaluation/`, and `src/training/`.
- Generate `src/agent/fixtures/` from `data/fixtures/` during packaging; do not track the generated copy.
- Keep attendee guidance in `instructions/`, deeper reference material in `docs/`, and presenter materials in `delivery-resources/`.
- Remove `.plan/` after its durable content has been incorporated into published documentation.
- Follow the latest Microsoft Foundry quickstarts as the golden path for SDKs, tooling, configuration, deployment, evaluation, optimization, tracing, and cleanup.

## Continuous-optimization reference

Store the accepted continuous-optimization image at `docs/assets/continuous-optimization.png` and display it in `docs/optimization.md` with descriptive alt text and attribution to the Microsoft Azure article. Link to that guide from the root README and demo runbooks rather than duplicating the image.

## Proposed micro-sprints

| Sprint | Outcome |
|---|---|
| **03A: Lock the demo contracts** | Complete. Delivery modes, evidence, rubric, provenance, durations, and acceptance criteria are defined above. |
| **03B: Define the audience path** | Complete. Cloud requirements, core and advanced scope, prerequisites, nondeterminism, and automation defaults are defined above. |
| **04: Foundation and Make it work** | Rebuild structure, fixtures, hosted agent, FastAPI application, infrastructure, preflight, setup, and teardown. |
| **05: Make it better** | Build the Insights seed, rubric, baseline evaluation, Model Router, and trace-based distillation workflows. |
| **06: Make it scale and validate** | Build Agent Optimizer workflow, deploy cleanly, run regression gates, and capture canonical evidence. |
| **07: Delivery experience** | Complete attendee instructions, presenter runbooks, transcripts, recording guidance, and supporting documentation. |
| **08: Publication readiness** | Run final validation, remove staging and template artifacts, verify links, finalize screenshots, and prepare the commit and pull-request strategy. |

## Operating agreement

- Work interactively in labeled micro-sprints.
- Ask one decision question at a time.
- Discuss and confirm scope before making changes.
- Execute only after the explicit instruction `RUN SPRINT <number>`.
- End executed work with `Sprint <number> Complete` and a concise summary.
- Do not push, open a pull request, or modify upstream without explicit approval.
