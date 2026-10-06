# Infrastructure

> **Which script should I run next, and what will it change?**
>
> Think of this folder as the workshop floor: first check your tools, then inspect the Azure site, build the environment, verify it, change one lever, and clean up when finished.

```text
03 Build v1 (includes local validation and Azure preflight)
	-> 04 Validate
	-> 05 Model Router v2
	-> 08 Agent Optimizer
	-> 10 Teardown

Optional references: 06 trace-trained student, 07 curated-label student,
										 09 reviewed candidate promotion
```

## Ownership

- The `microsoft.foundry` azd provider creates the Foundry account/project, model deployments, Hosted Agent build resources, Container Registry, Application Insights, and provider-managed identities/RBAC.
- [`supplemental.bicep`](supplemental.bicep) reuses those resources and adds only the FastAPI Container Apps environment, web user-assigned identity, and missing least-privilege assignments.
- See [`rbac-matrix.md`](rbac-matrix.md) for the capability-to-role contract.

## Commands

Use the step number when referring to a script in slides, recordings, or issue discussions. Filenames remain unchanged because scripts call each other by name.

| Step | Act | Script | Cloud side effects | Purpose |
|---:|---|---|---|---|
| — | Internal check | [`validate-local.sh`](validate-local.sh) | None | Run fixture, syntax, manifest, Bicep, and test checks. Setup calls this automatically. |
| — | Internal check | [`preflight.sh`](preflight.sh) | None | Check clients, authentication, selected subscription/region, model availability, and quota. Setup calls this automatically. |
| 03 | Foundation | [`setup.sh`](setup.sh) | Creates billable resources | Validate, authenticate, confirm the Azure target, run preflight, and build the isolated Foundry, monitoring, registry, web, and v1 agent environment. Deploys `gpt-5.4` capacity 200, `gpt-5.4-mini` capacity 150, and `gpt-4.1-mini` capacity 100. |
| 04 | Foundation | [`validate-deployment.sh`](validate-deployment.sh) | Read-only Azure queries | Verify the active Hosted Agent, web health, roles, and telemetry. |
| 05 | Make it better | [`deploy-model-router-v2.sh`](deploy-model-router-v2.sh) | Creates/updates a billable model deployment and Hosted Agent v2 | Provision Model Router with quota headroom, deploy and activate immutable v2, refresh RBAC, and smoke-test. |
| 06 | Fine-tuning reference | [`trace-finetune-v3.sh`](trace-finetune-v3.sh) | Read-only in harvest/status; billable in generate/submit/deploy/agent-v3 | Build a reviewed trace-derived SFT dataset, fine-tune/deploy `contoso-student`, and activate immutable v3. |
| 07 | Fine-tuning reference | [`curated-finetune-v4.sh`](curated-finetune-v4.sh) | Local-only in prepare; billable in submit/deploy/agent-v4 | Validate gold responses, fine-tune/deploy `contoso-curated-student`, and activate immutable v4. |
| 08 | Make it scale | [`optimize-v5.sh`](optimize-v5.sh) | Billable optimizer submission; status is read-only | Submit/reuse three optimizer candidates from v2 and stop for human review before apply/deploy. |
| 09 | Optional promotion | [`deploy-optimizer-v5.sh`](deploy-optimizer-v5.sh) | Creates immutable Hosted Agent v5 and changes endpoint routing | Post-session reference for deploying an authorized, reviewed local candidate through normal azd. |
| 10 | Cleanup | [`teardown.sh`](teardown.sh) | Deletes generated environment | Guard, delete, purge, and verify cleanup. |

Reusable utility: [`switch-agent-version.py`](switch-agent-version.py) (`U01`) inspects a retained immutable version and changes endpoint routing only when `--apply` is supplied. Internal helper [`deploy-supplemental.sh`](deploy-supplemental.sh) is called by the numbered deployment scripts and is not a learner step.

Generated environments use `rg-aitour-brk330-NNNNNN`. Every destructive command refuses the protected prototype resource group `rg-brk330-concierge`.

Run setup without arguments to review and edit its proposed subscription and location before resource creation. Flags are available for automation. After setup prints the generated environment name, set `BRK330_ENVIRONMENT` for later stages:

```bash
bash infra/setup.sh \
	--subscription "<subscription-name-or-id>" \
	--location "<azure-region>" \
	--yes
export BRK330_ENVIRONMENT="brk330-NNNNNN"
```

## Deployment order

1. Dev-container post-create installs declared dependencies and Foundry tooling.
2. Step 03 runs local validation, checks authentication, proposes the active subscription and `swedencentral`, and confirms the target before resource creation.
3. It checks live capability without creating resources, then provisions the Foundry project and models.
4. It deploys monitoring and early RBAC assignments without portal resources.
5. It starts the Container Apps environment asynchronously and deploys or reuses baseline Hosted Agent v1 while that Azure operation runs.
6. It waits for the portal infrastructure, reapplies identity-dependent RBAC, deploys FastAPI, and verifies the environment.
7. Step 04 validates the deployment and curated scenarios.
8. After accepting the v1 four-case rubric result, step 05 changes only the model strategy.
9. Step 08 generates optimizer candidates from the retained v2 baseline.
10. Step 10 removes the generated environment when the session is finished.

## Model Router stage

Model Router is intentionally not part of the baseline `setup.sh` path. The stage script deploys `model-router` version `2025-11-18` as Global Standard capacity 200 through [`model-router.bicep`](model-router.bicep). Before deployment it requires enough unallocated quota for any additional capacity plus a 40-unit reserve.

The script is resumable: environment metadata records v2 after a successful agent deploy, so a rerun reuses v2 instead of creating v3. It never deletes resources and refuses any resource group outside `rg-aitour-brk330-NNNNNN`.

## Trace-driven fine-tuning stage

[`trace-finetune-v3.sh`](trace-finetune-v3.sh) separates trace generation, harvest, human curation, training, model deployment, and agent deployment. Volatile trace content and training files remain under ignored `.azure/<environment>/training-v3/`; committed files contain only the training-only seed prompts, curation code, schemas, and instructions needed to reproduce the workflow.

Every phase is resumable and refuses `rg-brk330-concierge`. The script never deletes jobs, deployments, agents, traces, or datasets.

The curated-response stage keeps the v3 base model, method, seed, epochs, instruction hash, 20/4 split, deployment tier, and four-case rubric evaluation unchanged. Only the response labels change, so we can see whether better examples improve the student.

## Optional v5 promotion

Step 09 requires the retained v1-v4 deployment history and the reviewed candidate files produced by Agent Optimizer. It is not part of the live breakout and cannot be run directly after only a fresh v1/v2 rebuild.
