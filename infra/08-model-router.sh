#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Build v2: the same agent and instructions, but Model Router picks the model.

Usage: bash infra/08-model-router.sh [--mode balanced|quality] [--activate] [--environment brk330-NNNNNN]

--mode balanced (default) builds v2 on the model-router deployment that
bash infra/02-setup.sh created (Balanced routing: cheapest model within a small
quality band).

--mode quality builds v2-quality: it creates or reuses a second deployment,
model-router-quality, whose routing mode is Quality (strongest model for each
prompt, regardless of cost), then creates one agent version that uses it.

Each mode creates one new agent version and smoke-tests it. The portal keeps
using whatever version it used before unless you pass --activate. Running it
again reuses the recorded version.
EOF
}

source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

mode="balanced"
activate=false
environment_arg=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode) mode="$2"; shift 2 ;;
    --activate) activate=true; shift ;;
    --environment) environment_arg="$2"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
done
case "$mode" in
  balanced) label="v2"; deployment="model-router" ;;
  quality) label="v2-quality"; deployment="model-router-quality" ;;
  *) fail 2 "Unknown mode $mode. Use balanced or quality." ;;
esac

use_environment "$environment_arg"
[[ -n "$(version_for v1)" ]] || fail 9 'v1 is not recorded. Run bash infra/02-setup.sh first.'

ensure_quality_router() {
  local account url state
  account="$(azd env get-value AZURE_AI_ACCOUNT_NAME)"
  url="https://management.azure.com/subscriptions/$subscription_id/resourceGroups/$resource_group/providers/Microsoft.CognitiveServices/accounts/$account/deployments/$deployment?api-version=2026-07-01"
  state="$(az rest --method get --url "$url" --query 'properties.routing.mode' -o tsv 2>/dev/null || true)"
  if [[ "${state,,}" == "quality" ]]; then
    printf 'Reusing %s (routing mode: quality).\n' "$deployment"
    return
  fi
  printf 'Creating %s with routing mode quality...\n' "$deployment"
  az rest --method put --url "$url" -o none --body '{
    "sku": {"name": "GlobalStandard", "capacity": 300},
    "properties": {
      "model": {"format": "OpenAI", "name": "model-router", "version": "2025-11-18"},
      "routing": {"mode": "quality"}
    }
  }'
  printf 'Created. Routing mode changes can take up to 5 minutes to take effect.\n'
}

version="$(version_for "$label")"
if [[ -n "$version" ]]; then
  printf 'Reusing %s (contoso-travel version %s).\n' "$label" "$version"
else
  [[ "$mode" != quality ]] || ensure_quality_router
  previous_live="$(live_version)"
  deploy_new_version "$deployment" "$deployment" src/agent/.agent_configs/baseline/instructions.md
  version="$new_version"
  remember_version "$label" "$version" "$deployment" "$deployment"
  [[ "$activate" == true ]] || go_live "$previous_live"
fi

[[ "$activate" != true ]] || go_live "$version"
smoke_test "$version"
printf 'Next: bash infra/07-score.sh run --label %s\n' "$label"
