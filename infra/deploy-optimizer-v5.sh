#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Deploy the reviewed Agent Optimizer candidate as immutable contoso-travel v5.

Usage: infra/deploy-optimizer-v5.sh --environment brk330-NNNNNN

Uses normal azd deployment, refreshes RBAC, activates v5, and runs one policy
smoke test. It never deletes retained versions or resources.
EOF
}

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"
environment_name=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --environment) environment_name="$2"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
done
[[ "$environment_name" =~ ^brk330-[0-9]{6}$ ]] || { printf 'Environment must match brk330-NNNNNN.\n' >&2; exit 3; }
for command_name in az azd jq python3 sha256sum; do command -v "$command_name" >/dev/null || { printf 'Missing command %s.\n' "$command_name" >&2; exit 4; }; done
[[ -x .venv/bin/python ]] || { printf 'Python environment not found.\n' >&2; exit 5; }

candidate_id="cand_opt_86d7c7531b21417ab4581f1266ea4c24_0002"
candidate_dir="src/agent/.agent_configs/$candidate_id"
candidate_metadata="$candidate_dir/metadata.yaml"
candidate_instructions="$candidate_dir/instructions.md"
[[ -s "$candidate_metadata" && -s "$candidate_instructions" ]] || { printf 'Reviewed candidate files are missing.\n' >&2; exit 6; }

export AZURE_DEV_USER_AGENT=microsoft_foundry_skill
az account show >/dev/null
azd auth login --check-status >/dev/null
azd env select "$environment_name"
resource_group="$(azd env get-value AZURE_RESOURCE_GROUP)"
project_endpoint="$(azd env get-value FOUNDRY_PROJECT_ENDPOINT 2>/dev/null || azd env get-value AZURE_AI_PROJECT_ENDPOINT)"
[[ "$resource_group" != "rg-brk330-concierge" ]] || { printf 'Refusing protected prototype resource group.\n' >&2; exit 7; }
[[ "$resource_group" =~ ^rg-aitour-brk330-[0-9]{6}$ ]] || { printf 'Unexpected resource group: %s\n' "$resource_group" >&2; exit 8; }

candidate_model="$(.venv/bin/python -c 'import sys,yaml; print(yaml.safe_load(open(sys.argv[1]))["model"])' "$candidate_metadata")"
[[ "$candidate_model" == "model-router" ]] || { printf 'Candidate model must remain model-router; found %s.\n' "$candidate_model" >&2; exit 9; }
.venv/bin/python - "$candidate_id" <<'PY'
import sys, yaml
from pathlib import Path
candidate = sys.argv[1]
manifest = yaml.safe_load(Path("azure.yaml").read_text(encoding="utf-8"))
selected = manifest["services"]["contoso-travel"]["env"]["OPTIMIZATION_CANDIDATE_ID"]
if selected != candidate:
    raise SystemExit(f"azure.yaml selects {selected!r}, expected {candidate!r}")
PY

recorded_version="$(azd env get-value AGENT_CONTOSO_TRAVEL_VERSION 2>/dev/null || true)"
case "$recorded_version" in
  4) ;;
  5) printf 'Reusing recorded contoso-travel v5.\n' ;;
  *) printf 'Expected recorded agent v4 or v5; found %s.\n' "${recorded_version:-unset}" >&2; exit 10 ;;
esac

instruction_sha="$(sha256sum "$candidate_instructions" | cut -d' ' -f1)"
azd env set AZURE_AI_MODEL_DEPLOYMENT_NAME model-router
azd env set CONTOSO_CONFIGURATION "$candidate_id"
azd env set CONTOSO_INSTRUCTION_SHA "$instruction_sha"

if [[ "$recorded_version" == "4" ]]; then azd deploy contoso-travel --no-prompt; fi
[[ "$(azd env get-value AGENT_CONTOSO_TRAVEL_VERSION)" == "5" ]] || { printf 'Expected immutable agent v5 after deploy.\n' >&2; exit 11; }

bash infra/deploy-supplemental.sh
.venv/bin/python infra/switch-agent-version.py --version 5 --project-endpoint "$project_endpoint" --apply
agent_json="$(pushd src/agent >/dev/null && azd ai agent show --output json; popd >/dev/null)"
[[ "$(jq -r '.version' <<<"$agent_json")" == "5" ]] || { printf 'Agent v5 is not active.\n' >&2; exit 12; }
[[ "$(jq -r '.definition.environment_variables.AZURE_AI_MODEL_DEPLOYMENT_NAME' <<<"$agent_json")" == "model-router" ]] || { printf 'Agent v5 does not reference Model Router.\n' >&2; exit 13; }
[[ "$(jq -r '.definition.environment_variables.CONTOSO_CONFIGURATION' <<<"$agent_json")" == "$candidate_id" ]] || { printf 'Agent v5 does not reference reviewed candidate 2.\n' >&2; exit 14; }

pushd src/agent >/dev/null
azd ai agent invoke 'For employee EMP-001, state the applicable booking lead-time policy and cite the rule ID. Do not prepare or submit an itinerary.' --no-prompt
popd >/dev/null

printf 'Reviewed optimizer candidate v5 is active. Candidate instruction SHA256: %s\n' "$instruction_sha"
printf 'Evaluation command:\n'
printf '  cd src/agent && AZURE_DEV_USER_AGENT=microsoft_foundry_skill azd ai agent eval run --agent contoso-travel --config eval-optimizer-v5.yaml --name brk330-v5-optimizer\n'