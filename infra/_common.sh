# Shared setup for the numbered BRK330 scripts. Source this file; do not run it.
#
# Version labels used across the session:
#   v1      gpt-5.4 baseline (bash infra/02-setup.sh)
#   v2      Model Router, Balanced mode (bash infra/08-model-router.sh)
#   v2-quality  Model Router, Quality mode (bash infra/08-model-router.sh --mode quality)
#   v2-alt  fine-tuned student (bash infra/09-fine-tune.sh)
#   v3      reviewed optimizer candidate (bash infra/11-promote.sh deploy)
#   v3-router  v3's instructions on Model Router, Balanced (bash infra/11-promote.sh router)
#   v3-student  v3's instructions on a model fine-tuned from v3's answers (bash infra/09-fine-tune.sh --teacher-label v3)
# Each label maps to an immutable Hosted Agent version stored in the azd
# environment as BRK330_VERSION_<LABEL>, with its model and config alongside.

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"
export AZURE_DEV_USER_AGENT=microsoft_foundry_skill
smoke_prompt='For employee EMP-001, state the applicable booking lead-time policy and cite the rule ID. Do not prepare or submit an itinerary.'

fail() {
  local status="$1"
  shift
  printf '%s\n' "$*" >&2
  exit "$status"
}

# azd prints "key not found" on stdout, so keep the output only when the lookup succeeds.
env_value() {
  local value
  value="$(azd env get-value "$1" 2>/dev/null)" || return 0
  printf '%s' "$value"
}

# Select the session environment and stop early if anything looks unsafe.
use_environment() {
  local requested="${1:-}"
  local command_name
  for command_name in az azd jq python3 sha256sum; do
    command -v "$command_name" >/dev/null 2>&1 || fail 4 "Missing command $command_name. Rebuild the dev container."
  done
  [[ -x .venv/bin/python ]] || fail 5 'Python environment not found at .venv/bin/python. Rebuild the dev container.'
  az account show >/dev/null 2>&1 || fail 4 'Sign in first: az login --use-device-code'
  azd auth login --check-status >/dev/null 2>&1 || fail 4 'Sign in first: azd auth login'
  if [[ -n "$requested" ]]; then
    [[ "$requested" =~ ^brk330-[0-9]{6}$ ]] || fail 3 'Environment must match brk330-NNNNNN.'
    azd env select "$requested" >/dev/null
  fi
  environment_name="$(azd env get-value AZURE_ENV_NAME)"
  resource_group="$(azd env get-value AZURE_RESOURCE_GROUP)"
  subscription_id="$(azd env get-value AZURE_SUBSCRIPTION_ID)"
  [[ "$resource_group" != "rg-brk330-concierge" ]] || fail 7 'Refusing the protected prototype resource group.'
  [[ "$resource_group" =~ ^rg-aitour-brk330-[0-9]{6}$ ]] || fail 8 "Resource group $resource_group is not a generated BRK330 group."
  az account set --subscription "$subscription_id"
  project_endpoint="$(env_value FOUNDRY_PROJECT_ENDPOINT)"
  [[ -n "$project_endpoint" ]] || project_endpoint="$(env_value AZURE_AI_PROJECT_ENDPOINT)"
  state_root=".azure/$environment_name"
  mkdir -p "$state_root"
}

label_key() {
  case "$1" in
    v1) printf 'V1' ;;
    v2) printf 'V2' ;;
    v2-quality) printf 'V2_QUALITY' ;;
    v2-alt) printf 'V2_ALT' ;;
    v3) printf 'V3' ;;
    v3-router) printf 'V3_ROUTER' ;;
    v3-student) printf 'V3_STUDENT' ;;
    *) fail 2 "Unknown label $1. Use v1, v2, v2-quality, v2-alt, v3, v3-router, or v3-student." ;;
  esac
}

# Print the agent version recorded for a label, or nothing if it is not built yet.
version_for() {
  env_value "BRK330_VERSION_$(label_key "$1")"
}

remember_version() {
  local key
  key="$(label_key "$1")"
  azd env set "BRK330_VERSION_$key" "$2" >/dev/null
  azd env set "BRK330_MODEL_$key" "$3" >/dev/null
  azd env set "BRK330_CONFIG_$key" "$4" >/dev/null
  printf 'Recorded %s as contoso-travel version %s (%s, config %s).\n' "$1" "$2" "$3" "$4"
}

# Print the version currently answering the portal and the default endpoint.
live_version() {
  local value
  value="$(.venv/bin/python infra/switch-agent-version.py \
    --version "$(version_for v1)" --project-endpoint "$project_endpoint" | jq -r '.previous_version')"
  [[ "$value" =~ ^[0-9]+$ ]] || value="$(version_for v1)"
  printf '%s' "$value"
}

go_live() {
  .venv/bin/python infra/switch-agent-version.py \
    --version "$1" --project-endpoint "$project_endpoint" --apply >/dev/null
  printf 'The portal now uses contoso-travel version %s.\n' "$1"
}

# Deploy one new immutable version with the given model and config.
# Leaves the live version unchanged unless the caller activates it afterwards.
deploy_new_version() {
  local model="$1" config="$2" instruction_file="$3"
  local previous_model previous_config previous_sha
  previous_model="$(azd env get-value AZURE_AI_MODEL_DEPLOYMENT_NAME)"
  previous_config="$(azd env get-value CONTOSO_CONFIGURATION)"
  previous_sha="$(azd env get-value CONTOSO_INSTRUCTION_SHA)"
  azd env set AZURE_AI_MODEL_DEPLOYMENT_NAME "$model" >/dev/null
  azd env set CONTOSO_CONFIGURATION "$config" >/dev/null
  azd env set CONTOSO_INSTRUCTION_SHA "$(sha256sum "$instruction_file" | cut -d' ' -f1)" >/dev/null
  azd deploy contoso-travel --no-prompt
  new_version="$(azd env get-value AGENT_CONTOSO_TRAVEL_VERSION)"
  azd env set AZURE_AI_MODEL_DEPLOYMENT_NAME "$previous_model" >/dev/null
  azd env set CONTOSO_CONFIGURATION "$previous_config" >/dev/null
  azd env set CONTOSO_INSTRUCTION_SHA "$previous_sha" >/dev/null
  bash infra/deploy-supplemental.sh
}

smoke_test() {
  (cd src/agent && azd ai agent invoke --version "$1" --protocol responses \
    --new-session --new-conversation --no-prompt "$smoke_prompt")
}
