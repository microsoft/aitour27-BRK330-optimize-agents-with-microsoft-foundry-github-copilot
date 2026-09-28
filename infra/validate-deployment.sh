#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Run read-only checks against the active generated BRK330 environment.

Usage: infra/validate-deployment.sh

Validates resource-group safety, Hosted Agent details, web health, managed
identity role assignments, and recent Application Insights traces. It creates,
updates, and deletes nothing.
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

resource_group="$(azd env get-value AZURE_RESOURCE_GROUP)"
if [[ "$resource_group" == "rg-brk330-concierge" || ! "$resource_group" =~ ^rg-aitour-brk330-[0-9]{6}$ ]]; then
  printf 'Unsafe or protected resource group: %s\n' "$resource_group" >&2
  exit 2
fi

web_url="$(azd env get-value WEB_URL)"
web_identity="$(azd env get-value WEB_MANAGED_IDENTITY_RESOURCE_ID)"
app_insights="$(azd env get-value AZURE_MONITOR_APP_INSIGHTS_NAME)"
subscription_id="$(az account show --query id -o tsv)"
foundry_account="$(azd env get-value AZURE_AI_ACCOUNT_NAME)"
foundry_project="$(azd env get-value AZURE_AI_PROJECT_NAME)"
foundry_account_id="/subscriptions/$subscription_id/resourceGroups/$resource_group/providers/Microsoft.CognitiveServices/accounts/$foundry_account"
foundry_project_id="$foundry_account_id/projects/$foundry_project"
app_insights_id="/subscriptions/$subscription_id/resourceGroups/$resource_group/providers/Microsoft.Insights/components/$app_insights"

az group show --name "$resource_group" --query '{name:name,state:properties.provisioningState}' -o table
azd ai agent show --output table

health_file="$(mktemp)"
status="$(curl -sS -o "$health_file" -w '%{http_code}' "$web_url/api/health")"
if [[ "$status" != "200" ]]; then
  cat "$health_file" >&2
  rm -f "$health_file"
  printf 'Web health returned HTTP %s.\n' "$status" >&2
  exit 3
fi
python3 -m json.tool "$health_file"
rm -f "$health_file"

web_principal_id="$(az rest \
  --method get \
  --url "https://management.azure.com$web_identity?api-version=2023-01-31" \
  --query properties.principalId \
  -o tsv)"
assignment_count="$(az rest \
  --method get \
  --url "https://management.azure.com/subscriptions/$subscription_id/resourceGroups/$resource_group/providers/Microsoft.Authorization/roleAssignments?api-version=2022-04-01&\$filter=principalId%20eq%20'$web_principal_id'" \
  --query 'length(value)' \
  -o tsv)"
if (( assignment_count < 2 )); then
  printf 'Web identity has only %s role assignment(s); expected registry and agent access.\n' "$assignment_count" >&2
  exit 4
fi

project_principal_id="$(az rest \
  --method get \
  --url "https://management.azure.com$foundry_project_id?api-version=2025-04-01-preview" \
  --query identity.principalId \
  -o tsv)"
foundry_user_role_id="$(az rest \
  --method get \
  --url "https://management.azure.com/subscriptions/$subscription_id/providers/Microsoft.Authorization/roleDefinitions?api-version=2022-04-01" \
  --query "value[?properties.roleName=='Foundry User'].name | [0]" \
  -o tsv)"
foundry_project_manager_role_id="$(az rest \
  --method get \
  --url "https://management.azure.com/subscriptions/$subscription_id/providers/Microsoft.Authorization/roleDefinitions?api-version=2022-04-01" \
  --query "value[?properties.roleName=='Foundry Project Manager'].name | [0]" \
  -o tsv)"
monitoring_reader_role_id="$(az rest \
  --method get \
  --url "https://management.azure.com/subscriptions/$subscription_id/providers/Microsoft.Authorization/roleDefinitions?api-version=2022-04-01" \
  --query "value[?properties.roleName=='Monitoring Reader'].name | [0]" \
  -o tsv)"
project_assignments="$(az rest \
  --method get \
  --url "https://management.azure.com/subscriptions/$subscription_id/providers/Microsoft.Authorization/roleAssignments?api-version=2022-04-01&\$filter=principalId%20eq%20'$project_principal_id'" \
  --query value \
  -o json)"
project_foundry_role_count="$(jq \
    --arg role_id "$foundry_user_role_id" \
    --arg scope "${foundry_account_id,,}" \
    '[.[] | select((.properties.roleDefinitionId | ascii_downcase | endswith($role_id | ascii_downcase)) and (.properties.scope | ascii_downcase) == $scope)] | length' <<<"$project_assignments")"
if (( project_foundry_role_count != 1 )); then
  printf 'Foundry project identity is missing Foundry User at account scope; Agent Insights cannot run reliably.\n' >&2
  exit 5
fi
project_monitoring_role_count="$(jq \
    --arg role_id "$monitoring_reader_role_id" \
    --arg scope "${app_insights_id,,}" \
    '[.[] | select((.properties.roleDefinitionId | ascii_downcase | endswith($role_id | ascii_downcase)) and (.properties.scope | ascii_downcase) == $scope)] | length' <<<"$project_assignments")"
if (( project_monitoring_role_count != 1 )); then
  printf 'Foundry project identity is missing Monitoring Reader on Application Insights.\n' >&2
  exit 6
fi

presenter_principal_id="$(az ad signed-in-user show --query id -o tsv)"
presenter_assignments="$(az rest \
  --method get \
  --url "https://management.azure.com/subscriptions/$subscription_id/providers/Microsoft.Authorization/roleAssignments?api-version=2022-04-01&\$filter=principalId%20eq%20'$presenter_principal_id'" \
  --query value \
  -o json)"
presenter_manager_role_count="$(jq \
    --arg role_id "$foundry_project_manager_role_id" \
    --arg scope "${foundry_account_id,,}" \
    '[.[] | select((.properties.roleDefinitionId | ascii_downcase | endswith($role_id | ascii_downcase)) and (.properties.scope | ascii_downcase) == $scope)] | length' <<<"$presenter_assignments")"
if (( presenter_manager_role_count != 1 )); then
  printf 'Presenter is missing Foundry Project Manager at account scope, which Hosted Agent Insights requires.\n' >&2
  exit 7
fi
presenter_monitoring_role_count="$(jq \
    --arg role_id "$monitoring_reader_role_id" \
    --arg scope "${app_insights_id,,}" \
    '[.[] | select((.properties.roleDefinitionId | ascii_downcase | endswith($role_id | ascii_downcase)) and (.properties.scope | ascii_downcase) == $scope)] | length' <<<"$presenter_assignments")"
if (( presenter_monitoring_role_count != 1 )); then
  printf 'Presenter is missing Monitoring Reader on Application Insights.\n' >&2
  exit 8
fi

az monitor app-insights query \
  --app "$app_insights" \
  --resource-group "$resource_group" \
  --analytics-query 'union traces, requests, dependencies | where timestamp > ago(24h) | summarize count() by itemType | order by itemType asc' \
  -o table

printf 'Deployment validation passed for %s.\n' "$resource_group"
