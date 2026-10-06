#!/usr/bin/env bash
set -euo pipefail

az login --use-device-code
azd auth login

usage() {
  cat <<'EOF'
Provision and deploy a reproducible BRK330 environment.

Usage: infra/setup.sh [--subscription NAME_OR_ID] [--location REGION] [--suffix NNNNNN] [--yes]

The command validates the repository, checks authentication, proposes the active
Azure subscription and swedencentral as defaults, runs preflight, and deploys the
complete environment. Flags and BRK330_SUBSCRIPTION/BRK330_LOCATION override the
defaults. Use --yes to accept resolved values without an interactive confirmation.
EOF
}

subscription="${BRK330_SUBSCRIPTION:-}"
location="${BRK330_LOCATION:-}"
suffix=""
assume_yes=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --subscription) subscription="$2"; shift 2 ;;
    --location) location="$2"; shift 2 ;;
    --suffix) suffix="$2"; shift 2 ;;
    --yes|-y) assume_yes=true; shift ;;
    --help|-h) usage; exit 0 ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
done

total_steps=11
current_step=0
temporary_log="$(mktemp)"
setup_log="$temporary_log"
preflight_file="$(mktemp)"
cleanup() {
  rm -f "$temporary_log" "$preflight_file"
}
trap cleanup EXIT

run_step() {
  local label="$1"
  shift
  current_step=$((current_step + 1))
  printf '[%d/%d] %s...\n' "$current_step" "$total_steps" "$label"
  if "$@" >>"$setup_log" 2>&1; then
    printf '  Ready.\n'
    return
  else
    local status=$?
  fi
  printf '  Failed. Last output:\n' >&2
  tail -n 40 "$setup_log" >&2
  if [[ "$setup_log" != "$temporary_log" ]]; then
    printf '  Full log: %s\n' "$setup_log" >&2
  fi
  if [[ -n "${environment_name:-}" ]]; then
    printf '  Resume: bash infra/setup.sh --suffix %s\n' "$suffix" >&2
  fi
  return "$status"
}

run_step 'Validating the local environment' bash infra/validate-local.sh

if [[ -z "$subscription" ]]; then
  subscription="$(az account show --query name -o tsv)"
fi
if [[ -z "$location" ]]; then
  location="swedencentral"
fi

if [[ "$assume_yes" != true ]]; then
  if [[ ! -t 0 ]]; then
    printf 'Interactive confirmation requires a terminal. Pass --yes to use the resolved target.\n' >&2
    exit 2
  fi
  printf '\nAzure target (press Enter to keep each default):\n'
  read -r -p "  Subscription [$subscription]: " response
  subscription="${response:-$subscription}"
  read -r -p "  Location [$location]: " response
  location="${response:-$location}"
  printf '  Subscription: %s\n  Location: %s\n' "$subscription" "$location"
  read -r -p 'Run preflight and create billable Azure resources? [y/N] ' response
  if [[ ! "$response" =~ ^[Yy]$ ]]; then
    printf 'Setup cancelled before resource creation.\n'
    exit 0
  fi
else
  printf 'Azure target: %s in %s\n' "$subscription" "$location"
fi

run_step 'Checking Azure capacity and prerequisites' \
  bash infra/preflight.sh --subscription "$subscription" --location "$location" --output "$preflight_file"

if [[ -z "$suffix" ]]; then
  suffix="$(python3 - <<'PY'
import secrets
print(f"{secrets.randbelow(1_000_000):06d}")
PY
)"
fi
if [[ ! "$suffix" =~ ^[0-9]{6}$ ]]; then
  printf 'Suffix must contain exactly six digits.\n' >&2
  exit 3
fi

environment_name="brk330-$suffix"
resource_group="rg-aitour-brk330-$suffix"
if [[ "$resource_group" == "rg-brk330-concierge" ]]; then
  printf 'Refusing protected prototype resource group.\n' >&2
  exit 4
fi

configure_environment() {
  local subscription_id
  subscription_id="$(az account show --query id -o tsv)"
  if azd env list -o json | python3 -c 'import json,sys; name=sys.argv[1]; raise SystemExit(0 if any(item.get("Name")==name or item.get("name")==name for item in json.load(sys.stdin)) else 1)' "$environment_name"; then
    azd env select "$environment_name"
  else
    azd env new "$environment_name" --no-prompt
  fi

  azd env set AZURE_SUBSCRIPTION_ID "$subscription_id"
  azd env set AZURE_LOCATION "$location"
  azd env set AZURE_RESOURCE_GROUP "$resource_group"
  azd env set AZURE_AI_MODEL_DEPLOYMENT_NAME gpt-5.4
  azd env set AZURE_AI_JUDGE_DEPLOYMENT_NAME gpt-5.4-mini
  azd env set AZURE_AI_STUDENT_BASE_MODEL gpt-4.1-mini
  azd env set CONTOSO_CONFIGURATION baseline
  azd env set CONTOSO_INSTRUCTION_SHA "$(sha256sum src/agent/.agent_configs/baseline/instructions.md | cut -d' ' -f1)"
}

run_step "Configuring environment $environment_name" configure_environment

mkdir -p ".azure/$environment_name"
cp "$preflight_file" ".azure/$environment_name/preflight.json"
cp "$temporary_log" ".azure/$environment_name/setup.log"
setup_log=".azure/$environment_name/setup.log"

run_step 'Provisioning core Azure resources' azd provision --no-prompt

project_endpoint="$(azd env get-value FOUNDRY_PROJECT_ENDPOINT 2>/dev/null || true)"
if [[ -z "$project_endpoint" ]]; then
  project_endpoint="$(azd env get-value AZURE_AI_PROJECT_ENDPOINT)"
fi

wait_for_foundry() {
  FOUNDRY_PROJECT_ENDPOINT="$project_endpoint" .venv/bin/python - <<'PY'
import os
import time

from azure.ai.projects import AIProjectClient
from azure.core.exceptions import HttpResponseError
from azure.identity import AzureCliCredential

client = AIProjectClient(
  endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
  credential=AzureCliCredential(),
  allow_preview=True,
)
for attempt in range(1, 31):
  try:
    list(client.agents.list())
    print(f"Foundry project data plane ready after attempt {attempt}.")
    break
  except HttpResponseError as error:
    if error.status_code not in {404, 409, 429, 500, 502, 503} or attempt == 30:
      raise
    print(
      f"Foundry project data plane not ready (HTTP {error.status_code}); "
      f"retrying attempt {attempt}/30."
    )
    time.sleep(5)
PY
}

run_step 'Waiting for the Foundry project data plane' wait_for_foundry
run_step 'Preparing monitoring and agent access' bash infra/deploy-supplemental.sh --agent-only
run_step 'Starting portal infrastructure in parallel' bash infra/deploy-supplemental.sh --start-web

deploy_agent() {
  if FOUNDRY_PROJECT_ENDPOINT="$project_endpoint" .venv/bin/python - <<'PY'
import os
import sys

from azure.ai.projects import AIProjectClient
from azure.core.exceptions import HttpResponseError
from azure.identity import AzureCliCredential

client = AIProjectClient(
  endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
  credential=AzureCliCredential(),
  allow_preview=True,
)
try:
  details = client.agents.get(agent_name="contoso-travel")
except HttpResponseError as error:
  if error.status_code == 404:
    raise SystemExit(1) from None
  raise

latest = details.versions.latest
latest_status = getattr(latest.status, "value", str(latest.status)).lower()
if latest_status != "active":
  raise SystemExit(
    f"Existing contoso-travel version {latest.version} is {latest_status}; "
    "refusing to create another version during setup."
  )
print(f"Reusing active contoso-travel v{latest.version}.")
PY
  then
    return
  else
    agent_status=$?
    if (( agent_status != 1 )); then
      return "$agent_status"
    fi
    azd deploy contoso-travel --no-prompt
  fi
}

finish_portal_infrastructure() {
  bash infra/deploy-supplemental.sh --finish-web
  bash infra/deploy-supplemental.sh
}

deploy_portal() {
  azd deploy web --no-prompt
  bash infra/deploy-supplemental.sh
}

verify_environment() {
  local actual_group provisioning_state
  actual_group="$(azd env get-value AZURE_RESOURCE_GROUP)"
  if [[ "$actual_group" != "$resource_group" ]]; then
    printf 'Expected resource group %s, azd reports %s.\n' "$resource_group" "$actual_group" >&2
    return 5
  fi
  provisioning_state="$(az group show --name "$resource_group" --query properties.provisioningState -o tsv)"
  if [[ "$provisioning_state" != "Succeeded" ]]; then
    printf 'Resource group provisioning state is %s.\n' "$provisioning_state" >&2
    return 6
  fi
}

run_step 'Deploying Hosted Agent v1' deploy_agent
run_step 'Finishing portal infrastructure and RBAC' finish_portal_infrastructure
run_step 'Building and deploying the portal' deploy_portal
run_step 'Verifying the deployed environment' verify_environment

printf '\nBRK330 environment ready.\n'
printf 'Environment: %s\n' "$environment_name"
printf 'Web URL: %s\n' "$(azd env get-value WEB_URL)"
printf 'Setup log: %s\n' "$setup_log"
printf 'Teardown command: bash infra/teardown.sh --environment %s\n' "$environment_name"
