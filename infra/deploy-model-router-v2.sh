#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Provision Model Router and deploy immutable contoso-travel v2.

Usage: infra/deploy-model-router-v2.sh --environment brk330-NNNNNN

The script is resumable. It provisions or reuses a 200-capacity Global Standard
Model Router deployment, creates contoso-travel v2 exactly once, refreshes v2
monitoring RBAC, routes the endpoint to v2, and runs one smoke invocation.

It never deletes resources and refuses the protected prototype resource group.
Run the printed evaluation command separately after capturing deployment images.
EOF
}

environment_name=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --environment) environment_name="$2"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ ! "$environment_name" =~ ^brk330-[0-9]{6}$ ]]; then
  printf 'Environment must match brk330-NNNNNN.\n' >&2
  exit 3
fi

for command_name in az azd jq python3 sha256sum; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    printf 'Missing command %s. Rebuild the dev container.\n' "$command_name" >&2
    exit 4
  fi
done
if [[ ! -x .venv/bin/python ]]; then
  printf 'Python environment not found at .venv/bin/python. Rebuild the dev container.\n' >&2
  exit 5
fi

export AZURE_DEV_USER_AGENT=microsoft_foundry_skill
az account show >/dev/null
azd auth login --check-status >/dev/null
azd env select "$environment_name"

actual_environment="$(azd env get-value AZURE_ENV_NAME)"
resource_group="$(azd env get-value AZURE_RESOURCE_GROUP)"
subscription_id="$(azd env get-value AZURE_SUBSCRIPTION_ID)"
location="$(azd env get-value AZURE_LOCATION)"
foundry_account="$(azd env get-value AZURE_AI_ACCOUNT_NAME)"

if [[ "$actual_environment" != "$environment_name" ]]; then
  printf 'Selected environment %s, expected %s.\n' "$actual_environment" "$environment_name" >&2
  exit 6
fi
if [[ "$resource_group" == "rg-brk330-concierge" ]]; then
  printf 'Refusing to modify protected prototype resource group.\n' >&2
  exit 7
fi
if [[ ! "$resource_group" =~ ^rg-aitour-brk330-[0-9]{6}$ ]]; then
  printf 'Resource group %s is outside the generated BRK330 naming contract.\n' "$resource_group" >&2
  exit 8
fi

az account set --subscription "$subscription_id"

router_capacity=200
quota_reserve=40
arm_location="https://management.azure.com/subscriptions/$subscription_id/providers/Microsoft.CognitiveServices/locations/$location"
usage_json="$(az rest --method get --url "$arm_location/usages?api-version=2025-06-01" -o json)"
quota_record="$(jq -c '.value[] | select(.name.value == "OpenAI.GlobalStandard.ModelRouter")' <<<"$usage_json")"
if [[ -z "$quota_record" ]]; then
  printf 'Model Router quota record was not returned for %s.\n' "$location" >&2
  exit 9
fi
quota_limit="$(jq -r '.limit' <<<"$quota_record")"
quota_current="$(jq -r '.currentValue' <<<"$quota_record")"
quota_remaining=$((quota_limit - quota_current))

deployments_url="https://management.azure.com/subscriptions/$subscription_id/resourceGroups/$resource_group/providers/Microsoft.CognitiveServices/accounts/$foundry_account/deployments"
existing_capacity="$(az rest --method get --url "$deployments_url?api-version=2025-06-01" -o json | jq -r '[.value[] | select(.name == "model-router") | .sku.capacity][0] // 0')"
additional_capacity=$((router_capacity - existing_capacity))
if (( additional_capacity < 0 )); then
  additional_capacity=0
fi
required_remaining=$((additional_capacity + quota_reserve))
if (( quota_remaining < required_remaining )); then
  printf 'Insufficient Model Router quota: remaining=%d, required=%d (%d additional + %d reserve).\n' \
    "$quota_remaining" "$required_remaining" "$additional_capacity" "$quota_reserve" >&2
  exit 10
fi
printf 'Model Router quota: current=%d limit=%d remaining=%d; target=%d reserve=%d.\n' \
  "$quota_current" "$quota_limit" "$quota_remaining" "$router_capacity" "$quota_reserve"

az deployment group create \
  --subscription "$subscription_id" \
  --resource-group "$resource_group" \
  --name "brk330-model-router-$environment_name" \
  --template-file infra/model-router.bicep \
  --parameters foundryAccountName="$foundry_account" capacity="$router_capacity" \
  --query 'properties.outputs' -o table

router="$(az rest --method get --url "$deployments_url/model-router?api-version=2025-06-01" -o json)"
if [[ "$(jq -r '.properties.provisioningState' <<<"$router")" != "Succeeded" ]]; then
  printf 'Model Router deployment is not ready.\n' >&2
  exit 11
fi
if [[ "$(jq -r '.sku.capacity' <<<"$router")" != "$router_capacity" ]]; then
  printf 'Model Router capacity does not match %d.\n' "$router_capacity" >&2
  exit 12
fi
printf 'Screenshot checkpoint: Foundry model deployments -> model-router (save as Model-Router-Deployment.png).\n'

instruction_sha="$(sha256sum src/agent/.agent_configs/baseline/instructions.md | cut -d' ' -f1)"
azd env set AZURE_AI_MODEL_DEPLOYMENT_NAME model-router
azd env set CONTOSO_CONFIGURATION model-router
azd env set CONTOSO_INSTRUCTION_SHA "$instruction_sha"

recorded_version="$(azd env get-value AGENT_CONTOSO_TRAVEL_VERSION 2>/dev/null || true)"
case "$recorded_version" in
  1)
    azd deploy contoso-travel --no-prompt
    ;;
  2)
    printf 'Reusing recorded contoso-travel v2.\n'
    ;;
  *)
    printf 'Expected recorded contoso-travel version 1 or 2; found %s. Refusing to create another version.\n' \
      "${recorded_version:-unset}" >&2
    exit 13
    ;;
esac

deployed_version="$(azd env get-value AGENT_CONTOSO_TRAVEL_VERSION)"
if [[ "$deployed_version" != "2" ]]; then
  printf 'Expected immutable agent v2 after deploy; found v%s.\n' "$deployed_version" >&2
  exit 14
fi

bash infra/deploy-supplemental.sh
project_endpoint="$(azd env get-value FOUNDRY_PROJECT_ENDPOINT 2>/dev/null || azd env get-value AZURE_AI_PROJECT_ENDPOINT)"
.venv/bin/python infra/switch-agent-version.py \
  --version 2 \
  --project-endpoint "$project_endpoint" \
  --apply

agent_json="$(azd ai agent show --output json)"
if [[ "$(jq -r '.version' <<<"$agent_json")" != "2" ]]; then
  printf 'Foundry did not report contoso-travel v2 as active.\n' >&2
  exit 15
fi
if [[ "$(jq -r '.definition.environment_variables.AZURE_AI_MODEL_DEPLOYMENT_NAME' <<<"$agent_json")" != "model-router" ]]; then
  printf 'Active v2 does not reference model-router.\n' >&2
  exit 16
fi
if [[ "$(jq -r '.definition.environment_variables.CONTOSO_CONFIGURATION' <<<"$agent_json")" != "model-router" ]]; then
  printf 'Active v2 does not reference the model-router configuration.\n' >&2
  exit 17
fi
printf 'Screenshot checkpoint: Foundry agent contoso-travel v2 details (save as Model-Router-Agent-v2.png).\n'

azd ai agent invoke \
  'For employee EMP-001, state the applicable booking lead-time policy and cite the rule ID. Do not prepare or submit an itinerary.' \
  --no-prompt

printf 'Screenshot checkpoint: Travel Concierge Portal header and smoke response (save as Model-Router-Portal-v2.png).\n'
printf 'Model Router v2 is active. Capture deployment images before evaluation.\n'
printf 'Evaluation command:\n'
printf '  cd src/agent && AZURE_DEV_USER_AGENT=microsoft_foundry_skill azd ai agent eval run --agent contoso-travel --config eval-model-router-v2.yaml --name brk330-v2-model-router\n'