#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Run read-only checks against the active generated BRK330 environment.

Usage: infra/validate-deployment.sh [--verbose]

Validates resource-group safety, Hosted Agent details, web health, managed
identity role assignments, and recent Application Insights traces. It creates,
updates, and deletes nothing. By default it prints only READY or NOT READY;
--verbose shows resource, agent, health, and trace details.
EOF
}

verbose=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --verbose) verbose=true; shift ;;
    --help|-h) usage; exit 0 ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
done

report_failure() {
  status=$?
  trap - ERR
  printf 'Deployment validation: NOT READY.\n' >&2
  exit "$status"
}
not_ready() {
  status="$1"
  shift
  printf '%s\n' "$*" >&2
  printf 'Deployment validation: NOT READY.\n' >&2
  exit "$status"
}
show_output() {
  if [[ "$verbose" == true ]]; then
    "$@"
  else
    "$@" >/dev/null
  fi
}
trap report_failure ERR

resource_group="$(azd env get-value AZURE_RESOURCE_GROUP)"
if [[ "$resource_group" == "rg-brk330-concierge" || ! "$resource_group" =~ ^rg-aitour-brk330-[0-9]{6}$ ]]; then
  not_ready 2 "Unsafe or protected resource group: $resource_group"
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

show_output az group show --name "$resource_group" --query '{name:name,state:properties.provisioningState}' -o table
show_output azd ai agent show --output table

health_file="$(mktemp)"
status="$(curl -sS -o "$health_file" -w '%{http_code}' "$web_url/api/health")"
if [[ "$status" != "200" ]]; then
  cat "$health_file" >&2
  rm -f "$health_file"
  not_ready 3 "Web health returned HTTP $status."
fi
show_output python3 -m json.tool "$health_file"
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
  not_ready 4 "Web identity has only $assignment_count role assignment(s); expected registry and agent access."
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
  not_ready 5 'Foundry project identity is missing Foundry User at account scope; Agent Insights cannot run reliably.'
fi
project_monitoring_role_count="$(jq \
    --arg role_id "$monitoring_reader_role_id" \
    --arg scope "${app_insights_id,,}" \
    '[.[] | select((.properties.roleDefinitionId | ascii_downcase | endswith($role_id | ascii_downcase)) and (.properties.scope | ascii_downcase) == $scope)] | length' <<<"$project_assignments")"
if (( project_monitoring_role_count != 1 )); then
  not_ready 6 'Foundry project identity is missing Monitoring Reader on Application Insights.'
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
  not_ready 7 'Presenter is missing Foundry Project Manager at account scope, which Hosted Agent Insights requires.'
fi
presenter_monitoring_role_count="$(jq \
    --arg role_id "$monitoring_reader_role_id" \
    --arg scope "${app_insights_id,,}" \
    '[.[] | select((.properties.roleDefinitionId | ascii_downcase | endswith($role_id | ascii_downcase)) and (.properties.scope | ascii_downcase) == $scope)] | length' <<<"$presenter_assignments")"
if (( presenter_monitoring_role_count != 1 )); then
  not_ready 8 'Presenter is missing Monitoring Reader on Application Insights.'
fi

show_output az monitor app-insights query \
  --app "$app_insights" \
  --resource-group "$resource_group" \
  --analytics-query 'union traces, requests, dependencies | where timestamp > ago(24h) | summarize count() by itemType | order by itemType asc' \
  -o table

printf 'Deployment validation: READY for %s.\n' "$resource_group"
