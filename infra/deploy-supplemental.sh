#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Deploy the Container Apps web surface and its least-privilege RBAC.

Usage: infra/deploy-supplemental.sh

Inputs are read from the active azd environment. The script discovers the ACR,
Application Insights, and Log Analytics resources created by the Foundry
provider. It is idempotent and writes nonsecret outputs back to azd.
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

resource_group="$(azd env get-value AZURE_RESOURCE_GROUP)"
environment_name="$(azd env get-value AZURE_ENV_NAME)"
location="$(azd env get-value AZURE_LOCATION)"
foundry_account="$(azd env get-value AZURE_AI_ACCOUNT_NAME)"
foundry_project="$(azd env get-value AZURE_AI_PROJECT_NAME)"
principal_id="$(az ad signed-in-user show --query id -o tsv)"
hosted_agent_principal_id="$(azd env get-values -o json | python3 -c '
import json
import sys

values = json.load(sys.stdin)
print(values.get("AGENT_CONTOSO_TRAVEL_INSTANCE_IDENTITY_PRINCIPAL_ID", ""))
')"

if [[ "$resource_group" == "rg-brk330-concierge" ]]; then
  printf 'Refusing to modify protected prototype resource group.\n' >&2
  exit 2
fi

role_definitions_file="$(mktemp)"
trap 'rm -f "$role_definitions_file"' EXIT
subscription_id="$(az account show --query id -o tsv)"
web_resource_id="/subscriptions/$subscription_id/resourceGroups/$resource_group/providers/Microsoft.App/containerApps/contoso-travel-web"
web_image="$(az rest --method get --url "https://management.azure.com$web_resource_id?api-version=2024-03-01" --query 'properties.template.containers[0].image' -o tsv 2>/dev/null || true)"
configure_registry=false
if [[ -n "$web_image" ]]; then
  configure_registry=true
else
  web_image='mcr.microsoft.com/k8se/quickstart:latest'
fi

az rest --method get --url "https://management.azure.com/subscriptions/$subscription_id/providers/Microsoft.Authorization/roleDefinitions?api-version=2022-04-01" --query value -o json > "$role_definitions_file"

role_id() {
  python3 - "$role_definitions_file" "$1" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    definitions = json.load(handle)
matches = [
    item["name"]
    for item in definitions
    if item.get("properties", {}).get("roleName") == sys.argv[2]
]
if len(matches) != 1:
    raise SystemExit(f"Expected one role named {sys.argv[2]!r}; found {len(matches)}")
print(matches[0])
PY
}

acr_pull_role="$(role_id 'AcrPull')"
agent_consumer_role="$(role_id 'Foundry Agent Consumer')"
foundry_user_role="$(role_id 'Foundry User')"
foundry_project_manager_role="$(role_id 'Foundry Project Manager')"
metrics_publisher_role="$(role_id 'Monitoring Metrics Publisher')"
monitoring_reader_role="$(role_id 'Monitoring Reader')"

for value in "$acr_pull_role" "$agent_consumer_role" "$foundry_user_role" "$foundry_project_manager_role" "$metrics_publisher_role" "$monitoring_reader_role"; do
  if [[ -z "$value" ]]; then
    printf 'A required Azure role definition could not be resolved.\n' >&2
    exit 4
  fi
done

outputs="$(az deployment group create \
  --resource-group "$resource_group" \
  --name "brk330-web-$environment_name" \
  --template-file infra/supplemental.bicep \
  --parameters \
    location="$location" \
    environmentName="$environment_name" \
    foundryAccountName="$foundry_account" \
    projectName="$foundry_project" \
    principalId="$principal_id" \
    hostedAgentInstancePrincipalId="$hosted_agent_principal_id" \
    acrPullRoleId="$acr_pull_role" \
    foundryAgentConsumerRoleId="$agent_consumer_role" \
    foundryUserRoleId="$foundry_user_role" \
    foundryProjectManagerRoleId="$foundry_project_manager_role" \
    monitoringMetricsPublisherRoleId="$metrics_publisher_role" \
    monitoringReaderRoleId="$monitoring_reader_role" \
    webImage="$web_image" \
    configureRegistry="$configure_registry" \
  --query properties.outputs -o json)"

output_value() {
  OUTPUTS="$outputs" python3 - "$1" <<'PY'
import json
import os
import sys
outputs = json.loads(os.environ["OUTPUTS"])
requested = sys.argv[1].casefold()
matching_key = next((key for key in outputs if key.casefold() == requested), None)
if matching_key is None:
  raise SystemExit(f"Deployment output {sys.argv[1]!r} was not returned")
print(outputs[matching_key]["value"])
PY
}

for key in APPLICATIONINSIGHTS_CONNECTION_STRING AZURE_CONTAINER_APPS_ENV_NAME AZURE_CONTAINER_REGISTRY_ENDPOINT AZURE_CONTAINER_REGISTRY_NAME AZURE_MONITOR_APP_INSIGHTS_NAME AZURE_MONITOR_LOG_ANALYTICS_NAME WEB_MANAGED_IDENTITY_CLIENT_ID WEB_MANAGED_IDENTITY_RESOURCE_ID WEB_URL; do
  azd env set "$key" "$(output_value "$key")"
done

printf 'Supplemental web environment ready: %s\n' "$(output_value WEB_URL)"
