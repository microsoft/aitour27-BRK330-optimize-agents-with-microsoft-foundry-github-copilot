# Dry-run readiness

## Feasibility assessment for the 15-hour constraint

A demo-focused dry run is plausible within the fixed window if Azure access,
quota, and preview capabilities are already available. A complete polished
package is not a safe commitment because training and optimizer completion are
external cloud dependencies.

A credible dry run is achievable if the work is intentionally staged:

1. Front-load Azure identity, quota, model, RBAC, and preview checks. Stop early
   if a required capability is unavailable.
2. Make Acts 1 and 2 fully functional first.
3. Make the baseline and Model Router comparison in Act 3 functional next.
4. Treat fine-tuning and Agent Optimizer as checkpoint-dependent cloud jobs:
   start them early, capture results as soon as available, and never fabricate
   outcomes.
5. Record portal clips immediately after each usable checkpoint.
6. Use measured placeholders in slides until the first successful comparison.

## Minimum viable dry-run path

### Must work

- Foundry project and Application Insights connection.
- Hosted agent and FastAPI site deployed to Azure.
- Caldova policy and deterministic travel fixtures.
- Krystal hero request, including one receipt.
- Policy hard-block example.
- Small evaluated batch from the fixed 20-prompt subset.
- Trace and evaluation views in the portal.

### Strongly preferred

- Model Router applied after task decomposition.
- Baseline-versus-router quality, latency, and cost comparison.
- One usable Insights finding.

### Checkpoint dependent

- Completed fine-tuning/distillation run.
- Completed Agent Optimizer candidate comparison.

If checkpoint-dependent items are unavailable, the dry run should state that the
workflow and inputs are ready but the measured cloud result is pending. The
published session must not make that substitution.

## First actions after approval

1. Copy `.plan/` into the repository and commit the planning package.
2. Verify Azure identity, subscription, quota, region, and preview access.
3. Discover available baseline, judge, router, trainable, and optimizer models.
4. Provision observability and RBAC before building the app.
5. Build the deterministic data fixtures and hero flow.
6. Deploy and capture the first known-good Act 2 checkpoint.
