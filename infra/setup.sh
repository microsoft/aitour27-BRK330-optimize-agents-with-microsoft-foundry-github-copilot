#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Provision and deploy a reproducible BRK330 environment.

Usage: infra/setup.sh [--subscription NAME_OR_ID] [--location REGION] [--suffix NNNNNN]

Defaults: subscription ai-team, location swedencentral, random six-digit suffix.
Creates azd environment brk330-<suffix> and resource group
rg-aitour-brk330-<suffix>. The protected prototype group is never used.
EOF
}

subscription="ai-team"
location="swedencentral"
suffix=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --subscription) subscription="$2"; shift 2 ;;
    --location) location="$2"; shift 2 ;;
    --suffix) suffix="$2"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
done

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

preflight_file="$(mktemp)"
bash infra/preflight.sh --subscription "$subscription" --location "$location" --output "$preflight_file"
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
azd env set AZURE_AI_STUDENT_BASE_MODEL gpt-5.4-mini
azd env set CONTOSO_CONFIGURATION baseline
azd env set CONTOSO_INSTRUCTION_SHA "$(sha256sum src/agent/.agent_configs/baseline/instructions.md | cut -d' ' -f1)"

mkdir -p ".azure/$environment_name"
cp "$preflight_file" ".azure/$environment_name/preflight.json"
rm -f "$preflight_file"

azd provision --no-prompt

project_endpoint="$(azd env get-value FOUNDRY_PROJECT_ENDPOINT 2>/dev/null || true)"
if [[ -z "$project_endpoint" ]]; then
  project_endpoint="$(azd env get-value AZURE_AI_PROJECT_ENDPOINT)"
fi
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

bash infra/deploy-supplemental.sh
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
  :
else
  agent_status=$?
  if (( agent_status != 1 )); then
    exit "$agent_status"
  fi
  azd deploy contoso-travel --no-prompt
fi
bash infra/deploy-supplemental.sh
azd deploy web --no-prompt
bash infra/deploy-supplemental.sh

actual_group="$(azd env get-value AZURE_RESOURCE_GROUP)"
if [[ "$actual_group" != "$resource_group" ]]; then
  printf 'Expected resource group %s, azd reports %s.\n' "$resource_group" "$actual_group" >&2
  exit 5
fi
az group show --name "$resource_group" --query '{name:name,location:location,provisioningState:properties.provisioningState}' -o table
printf 'BRK330 environment ready. Web URL: %s\n' "$(azd env get-value WEB_URL)"
printf 'Teardown command: bash infra/teardown.sh --environment %s\n' "$environment_name"
