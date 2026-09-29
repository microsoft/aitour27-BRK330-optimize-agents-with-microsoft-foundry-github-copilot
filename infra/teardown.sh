#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Delete and purge a generated BRK330 environment.

Usage: infra/teardown.sh [--environment brk330-NNNNNN]

The script refuses resource groups outside the rg-aitour-brk330-* namespace and
always refuses rg-brk330-concierge. It requires two interactive confirmations:
the full resource-group name followed by an explicit y/N purge approval.
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

if [[ -n "$environment_name" ]]; then
  azd env select "$environment_name"
else
  environment_name="$(azd env get-value AZURE_ENV_NAME)"
fi
resource_group="$(azd env get-value AZURE_RESOURCE_GROUP)"

if [[ "$resource_group" == "rg-brk330-concierge" || ! "$resource_group" =~ ^rg-aitour-brk330-[0-9]{6}$ ]]; then
  printf 'Refusing to delete unsafe resource group: %s\n' "$resource_group" >&2
  exit 3
fi

subscription_id="$(az account show --query id -o tsv)"
subscription_name="$(az account show --query name -o tsv)"
printf 'Subscription:   %s (%s)\nEnvironment:    %s\nResource group: %s\n' \
  "$subscription_name" "$subscription_id" "$environment_name" "$resource_group"

read -r -p "Type the full resource group name to confirm deletion: " confirmation
if [[ "$confirmation" != "$resource_group" ]]; then
  printf 'Confirmation did not match; nothing deleted.\n' >&2
  exit 4
fi

read -r -p "Permanently delete and purge this resource group? [y/N]: " purge_confirmation
if [[ ! "$purge_confirmation" =~ ^[Yy]$ ]]; then
  printf 'Purge was not approved; nothing deleted.\n' >&2
  exit 5
fi

azd down --force --purge
if [[ "$(az group exists --name "$resource_group")" == "true" ]]; then
  printf 'Resource group deletion was submitted but %s still exists. Verify in Azure.\n' "$resource_group" >&2
  exit 6
fi
printf 'Deleted and purged %s.\n' "$resource_group"
