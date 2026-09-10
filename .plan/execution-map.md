# Implementation and recording ownership

## What implementation does

After plan approval, the presenter drives the full engineering work by pasting
the ordered prompts in `recording-prompts.md`. Copilot performs and verifies each
step:

1. Copy the staged planning package into the repository as `.plan/`.
2. Verify Azure identity, quota, model availability, regions, preview access, and
   current RBAC requirements.
3. Create every synthetic policy, catalog, receipt, itinerary, prompt, rubric,
   and training asset.
4. Build the Python Foundry hosted agent and FastAPI web application.
5. Create the Azure provisioning and deployment assets.
6. Provision and deploy the real solution to Azure.
7. Run the hero flow and policy-block flow.
8. Register the rubric and execute the fixed 20-prompt baseline evaluation.
9. Implement task decomposition and Model Router, then execute the comparison.
10. Discover a supported student model and execute the real training workflow.
11. Configure and execute a real Agent Optimizer run in the portal.
12. Persist measured result summaries, portal URLs, version IDs, and screenshots.
13. Prepare repeatable recording starting points and reset instructions.
14. Update the repository documentation and presenter materials.

All implementation files must follow the repository placement contract in
`spec.md`. Presenter runbooks remain in `.plan/`; the final
`delivery-resources/` directory remains a single `README.md`.

Implementation does **not** fabricate completed screens or substitute mocks for
Azure operations.

## What the presenter records

The presenter records while the solution is built. Each prompt creates or
verifies the real checkpoint used by the following prompt.

The presenter does not “prompt themselves.” They paste the numbered messages
from [`recording-prompts.md`](recording-prompts.md) into GitHub Copilot App, wait
for each step to finish or reach a documented cloud-operation boundary, inspect
the result, and then send the next prompt.

### Demo 1 recording

**Starting point:** the implementation branch containing `.plan/`, before the
application exists.

1. Create a new GitHub Copilot App session on that branch.
2. Paste the kickoff prompt from `demo-builder.md`.
3. Record Copilot reading the spec, planning, and creating representative files.
4. Record the command/action that starts provisioning and deployment.
5. Stop recording while Azure completes the real operation.
6. Resume after the deployment prompt verifies the completed operation.
7. Record the live web hero request, policy block, evaluation, traces, and
   Insights result.

### Demo 2 recording

**Starting point:** the deployed baseline checkpoint created and verified during
Demo 1.

1. Open a new Copilot App session for the baseline branch/configuration.
2. Record the request to create/register the Caldova rubric and run evaluation.
3. Resume at the verified baseline portal result.
4. Record the request to implement decomposition and Model Router.
5. Resume at the verified routed deployment and comparison.
6. Record the request that starts trace curation and supported training.
7. Resume at the verified training result and three-way comparison.

### Demo 3 recording

**Starting point:** the optimization-ready agent produced by Demo 2. The
presenter starts the real Agent Optimizer run, pauses recording, then resumes
after Copilot verifies that same run.

1. Record the portal setup and action that starts an optimizer run.
2. Stop while the real run completes.
3. Resume at the prepared completed run.
4. Record candidate comparison and evidence inspection.
5. Record the human review and promotion decision.

## Prepared recording artifacts

The ordered prompts progressively create:

- A named starting branch or commit for each Copilot recording.
- A named completed checkpoint for each cloud transition.
- The exact kickoff prompt for each new Copilot session.
- The complete ordered prompt script in `recording-prompts.md`.
- Public or authenticated URLs for the web app and relevant portal pages.
- Foundry Canvas creation-progress and manage-mode recording cues.
- Stable prompt IDs and uploaded media paths.
- Expected screen-by-screen results.
- Reset steps for retakes.
- Fallback screenshots and clips for preview UI changes.
- A result manifest containing only measured model, cost, latency, and quality
  values.

## What remains manual

- Starting a new Copilot App session for each recorded build narrative.
- Screen recording and video editing.
- Any interactive portal selection the presenter wants visible.
- Final PowerPoint edits using `slides.md` and `speaker-notes.md`.
- Final approval to promote an Agent Optimizer candidate.
