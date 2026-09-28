#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

usage() {
  cat <<'EOF'
Run Agent Optimizer from the selected immutable v2 baseline.

Usage: infra/optimize-v5.sh PHASE --environment brk330-NNNNNN

Phases:
  submit  Submit/reuse one three-candidate optimizer job and persist its ID.
  status  Show candidate status/results for human review.

This script never applies, deploys, promotes, or deletes a candidate. Candidate
application requires a separate explicit approval after reviewing every result.
EOF
}

phase="${1:-}"
if [[ -n "$phase" ]]; then shift; fi
environment_name=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --environment) environment_name="$2"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
done
if [[ "$phase" == "--help" || "$phase" == "-h" || -z "$phase" ]]; then usage; exit 0; fi
case "$phase" in submit|status) ;; *) printf 'Unknown phase: %s\n' "$phase" >&2; exit 2 ;; esac
[[ "$environment_name" =~ ^brk330-[0-9]{6}$ ]] || { printf 'Environment must match brk330-NNNNNN.\n' >&2; exit 3; }
for command_name in az azd jq python3; do command -v "$command_name" >/dev/null || { printf 'Missing command %s.\n' "$command_name" >&2; exit 4; }; done
[[ -x .venv/bin/python ]] || { printf 'Python environment not found.\n' >&2; exit 5; }

export AZURE_DEV_USER_AGENT=microsoft_foundry_skill
az account show >/dev/null
azd auth login --check-status >/dev/null
azd env select "$environment_name"
resource_group="$(azd env get-value AZURE_RESOURCE_GROUP)"
project_endpoint="$(azd env get-value FOUNDRY_PROJECT_ENDPOINT 2>/dev/null || azd env get-value AZURE_AI_PROJECT_ENDPOINT)"
[[ "$resource_group" != "rg-brk330-concierge" ]] || { printf 'Refusing protected prototype resource group.\n' >&2; exit 5; }
[[ "$resource_group" =~ ^rg-aitour-brk330-[0-9]{6}$ ]] || { printf 'Unexpected resource group: %s\n' "$resource_group" >&2; exit 6; }

state_dir=".azure/$environment_name/optimizer-v5"
mkdir -p "$state_dir"
operation_id_file="$state_dir/operation-id.txt"
config="eval-model-router-v2.yaml"

case "$phase" in
  submit)
    if [[ -s "$operation_id_file" ]]; then
      printf 'Reusing optimizer operation %s.\n' "$(cat "$operation_id_file")"
      exit 0
    fi
    baseline="$(.venv/bin/python infra/switch-agent-version.py --version 2 --project-endpoint "$project_endpoint")"
    if [[ "$(jq -r '.previous_version' <<<"$baseline")" != "2" ]]; then
      printf 'Active endpoint is not v2. Reroute to v2 before optimizer submission.\n' >&2
      exit 7
    fi
    log="$state_dir/submit.log"
    pushd src/agent >/dev/null
    azd ai agent optimize \
      --agent contoso-travel \
      --config "$config" \
      --no-wait \
      --no-prompt | tee "$repo_root/$log"
    popd >/dev/null
    operation_id="$(grep -Eo 'opt_[A-Za-z0-9_-]+' "$log" | tail -1 || true)"
    [[ -n "$operation_id" ]] || { printf 'No optimizer operation ID returned; inspect %s.\n' "$log" >&2; exit 8; }
    printf '%s\n' "$operation_id" > "$operation_id_file"
    printf 'Optimizer operation submitted: %s\n' "$operation_id"
    ;;

  status)
    [[ -s "$operation_id_file" ]] || { printf 'Run submit first.\n' >&2; exit 9; }
    operation_id="$(cat "$operation_id_file")"
    pushd src/agent >/dev/null
    azd ai agent optimize status "$operation_id" \
      --project-endpoint "$project_endpoint" \
      --output json | tee "$repo_root/$state_dir/status.raw.log"
    popd >/dev/null
    printf 'Review all candidate IDs, scores, and configuration differences before applying anything.\n'
    ;;
esac