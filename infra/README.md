# Infrastructure

Reproducible deployment and cleanup for an isolated BRK330 environment.

## Ownership

- The `microsoft.foundry` azd provider creates the Foundry account/project, model deployments, Hosted Agent build resources, Container Registry, Application Insights, and provider-managed identities/RBAC.
- [`supplemental.bicep`](supplemental.bicep) reuses those resources and adds only the FastAPI Container Apps environment, web user-assigned identity, and missing least-privilege assignments.
- See [`rbac-matrix.md`](rbac-matrix.md) for the capability-to-role contract.

## Commands

| Command | Cloud side effects | Purpose |
|---|---|---|
| `bash infra/preflight.sh --help` | None | Check clients, authentication, subscription, region, and model availability. |
| `bash infra/setup.sh --help` | Creates billable resources | Generate an isolated environment, provision, and deploy. |
| `bash infra/deploy-model-router-v2.sh --help` | Creates/updates a billable model deployment and Hosted Agent v2 | Provision Model Router with quota headroom, deploy and activate immutable v2, refresh RBAC, and smoke-test. |
| `bash infra/validate-local.sh` | None | Run fixture, syntax, manifest, Bicep, and test checks. |
| `bash infra/validate-deployment.sh` | Read-only Azure queries | Verify the active Hosted Agent, web health, roles, and telemetry. |
| `python infra/switch-agent-version.py --help` | Read-only unless `--apply` | Inspect or reroute the endpoint to a retained immutable version. |
| `bash infra/teardown.sh --help` | Deletes generated environment | Guard, delete, purge, and verify cleanup. |

Generated environments use `rg-aitour-brk330-NNNNNN`. Every destructive command refuses the protected prototype resource group `rg-brk330-concierge`.

## Deployment order

1. Dev-container post-create installs declared dependencies, the Foundry azd extension, and the user-level Application Insights Azure CLI extension used by deployment validation.
2. Authenticate yourself with `az login --use-device-code` and `azd auth login`.
3. Preflight checks live capability without creating resources.
4. `setup.sh` provisions the Foundry project and models.
5. It deploys the Hosted Agent so the provider creates its registry, monitoring, identity, and immutable version.
6. It deploys monitoring/web resources and injects the App Insights connection.
7. It creates the telemetry-enabled Hosted Agent version, then reapplies RBAC for that immutable version identity.
8. It deploys the FastAPI image and runs the resource-group guard check.
9. Run deployment validation and the curated scenarios.
10. After accepting the frozen v1 evaluation, run `deploy-model-router-v2.sh` to add the first optimization lever without changing v1.
11. Run teardown when finished to stop ongoing charges.

## Model Router stage

Model Router is intentionally not part of the baseline `setup.sh` path. The stage script deploys `model-router` version `2025-11-18` as Global Standard capacity 200 through [`model-router.bicep`](model-router.bicep). Before deployment it requires enough unallocated quota for any additional capacity plus a 40-unit reserve.

The script is resumable: environment metadata records v2 after a successful agent deploy, so a rerun reuses v2 instead of creating v3. It never deletes resources and refuses any resource group outside `rg-aitour-brk330-NNNNNN`.
