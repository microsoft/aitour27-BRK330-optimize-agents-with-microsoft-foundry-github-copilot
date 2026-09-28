#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Build and deploy curated-response fine-tuned agent v4 in resumable phases.

Usage: infra/curated-finetune-v4.sh PHASE --environment brk330-NNNNNN

Phases:
  prepare   Validate committed gold labels and create deterministic 20/4 SFT data.
  submit    Submit or reuse one gpt-4.1-mini supervised fine-tuning job.
  status    Show the persisted fine-tuning job and recent logs.
  deploy    Deploy the succeeded job as contoso-curated-student on DeveloperTier.
  agent-v4  Create/reuse immutable agent v4, activate, smoke-test, print eval command.

The script never deletes resources and refuses the protected prototype group.
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
case "$phase" in prepare|submit|status|deploy|agent-v4) ;; *) printf 'Unknown phase: %s\n' "$phase" >&2; exit 2 ;; esac
[[ "$environment_name" =~ ^brk330-[0-9]{6}$ ]] || { printf 'Environment must match brk330-NNNNNN.\n' >&2; exit 3; }
for command_name in az azd jq python3 sha256sum; do command -v "$command_name" >/dev/null || { printf 'Missing command %s.\n' "$command_name" >&2; exit 4; }; done
[[ -x .venv/bin/python ]] || { printf 'Python environment not found.\n' >&2; exit 5; }

export AZURE_DEV_USER_AGENT=microsoft_foundry_skill
az account show >/dev/null
azd auth login --check-status >/dev/null
azd env select "$environment_name"
resource_group="$(azd env get-value AZURE_RESOURCE_GROUP)"
subscription_id="$(azd env get-value AZURE_SUBSCRIPTION_ID)"
location="$(azd env get-value AZURE_LOCATION)"
foundry_account="$(azd env get-value AZURE_AI_ACCOUNT_NAME)"
project_endpoint="$(azd env get-value FOUNDRY_PROJECT_ENDPOINT 2>/dev/null || azd env get-value AZURE_AI_PROJECT_ENDPOINT)"
[[ "$resource_group" != "rg-brk330-concierge" ]] || { printf 'Refusing protected prototype resource group.\n' >&2; exit 6; }
[[ "$resource_group" =~ ^rg-aitour-brk330-[0-9]{6}$ ]] || { printf 'Unexpected resource group: %s\n' "$resource_group" >&2; exit 7; }
az account set --subscription "$subscription_id"

state_dir=".azure/$environment_name/training-v4"
mkdir -p "$state_dir"
gold_file="data/training/curated-gold-v1.jsonl"
holdout_file="data/evaluation/lightweight-v1/dataset-v2.jsonl"
scope_file="data/training/fine-tuning-scope-v1.json"
instruction_file="src/agent/.agent_configs/baseline/instructions.md"
train_file="$state_dir/train.jsonl"
validation_file="$state_dir/validation.jsonl"
provenance_file="$state_dir/provenance.json"
job_id_file="$state_dir/job-id.txt"
job_suffix="brk330-curated-student-v1"
deployment_name="contoso-curated-student"

case "$phase" in
  prepare)
    .venv/bin/python src/training/curated_dataset.py \
      --gold "$gold_file" --holdout "$holdout_file" --scope "$scope_file" \
      --instructions "$instruction_file" --train "$train_file" \
      --validation "$validation_file" --provenance "$provenance_file"
    sha256sum "$train_file" "$validation_file" "$provenance_file"
    ;;

  submit)
    [[ -s "$train_file" && -s "$validation_file" && -s "$provenance_file" ]] || { printf 'Run prepare first.\n' >&2; exit 8; }
    if [[ -s "$job_id_file" ]]; then printf 'Reusing fine-tuning job %s.\n' "$(cat "$job_id_file")"; exit 0; fi
    arm_location="https://management.azure.com/subscriptions/$subscription_id/providers/Microsoft.CognitiveServices/locations/$location"
    quota="$(az rest --method get --url "$arm_location/usages?api-version=2025-06-01" -o json | jq -c '.value[] | select(.name.value == "OpenAI.GlobalStandard.gpt4.1-mini-finetune")')"
    [[ -n "$quota" ]] || { printf 'Fine-tuning quota record missing.\n' >&2; exit 9; }
    remaining=$(( $(jq -r '.limit' <<<"$quota") - $(jq -r '.currentValue' <<<"$quota") ))
    (( remaining >= 10 )) || { printf 'Fine-tuning quota insufficient: %d.\n' "$remaining" >&2; exit 10; }
    job_config="$state_dir/fine-tune-job.yaml"
    cat > "$job_config" <<EOF
name: brk330-curated-student-training
description: Curated-response SFT of the Caldova concierge
model: gpt-4.1-mini
method:
  type: supervised
  supervised:
    hyperparameters:
      epochs: 3
seed: 331
suffix: $job_suffix
extra_body:
  trainingType: GlobalStandard
training_file: local:$train_file
validation_file: local:$validation_file
EOF
    submit_log="$state_dir/submit.log"
    azd ai finetuning jobs submit --project-endpoint "$project_endpoint" --subscription "$subscription_id" --file "$job_config" --no-prompt | tee "$submit_log"
    job_id="$(grep -Eo 'ftjob-[A-Za-z0-9_-]+' "$submit_log" | tail -1 || true)"
    [[ -n "$job_id" ]] || { printf 'No job ID returned; inspect %s.\n' "$submit_log" >&2; exit 11; }
    printf '%s\n' "$job_id" > "$job_id_file"
    printf 'Curated fine-tuning job submitted: %s\n' "$job_id"
    ;;

  status)
    [[ -s "$job_id_file" ]] || { printf 'Run submit first.\n' >&2; exit 12; }
    azd ai finetuning jobs show --project-endpoint "$project_endpoint" --subscription "$subscription_id" --id "$(cat "$job_id_file")" --logs --output json | tee "$state_dir/job-status.raw.log"
    ;;

  deploy)
    [[ -s "$job_id_file" ]] || { printf 'Run submit first.\n' >&2; exit 13; }
    job_id="$(cat "$job_id_file")"
    raw_status="$state_dir/job-status.raw.log"
    azd ai finetuning jobs show --project-endpoint "$project_endpoint" --subscription "$subscription_id" --id "$job_id" --output json > "$raw_status"
    sed -n '/^[[:space:]]*{/,$p' "$raw_status" > "$state_dir/job-status.json"
    jq -e . "$state_dir/job-status.json" >/dev/null || { printf 'Invalid status JSON; inspect %s.\n' "$raw_status" >&2; exit 14; }
    status="$(jq -r '.status' "$state_dir/job-status.json" | tr '[:upper:]' '[:lower:]')"
    [[ "$status" == "succeeded" ]] || { printf 'Job %s is %s.\n' "$job_id" "$status" >&2; exit 15; }
    deployments_url="https://management.azure.com/subscriptions/$subscription_id/resourceGroups/$resource_group/providers/Microsoft.CognitiveServices/accounts/$foundry_account/deployments"
    existing="$(az rest --method get --url "$deployments_url?api-version=2025-06-01" -o json | jq -r --arg name "$deployment_name" '[.value[]|select(.name==$name)|.properties.provisioningState][0]//empty')"
    if [[ "$existing" == "Succeeded" ]]; then printf 'Reusing %s deployment.\n' "$deployment_name"; exit 0; fi
    quota="$(az rest --method get --url "https://management.azure.com/subscriptions/$subscription_id/providers/Microsoft.CognitiveServices/locations/$location/usages?api-version=2025-06-01" -o json | jq -c '.value[]|select(.name.value=="OpenAI.DeveloperTier.gpt4.1-mini-finetune")')"
    remaining=$(( $(jq -r '.limit' <<<"$quota") - $(jq -r '.currentValue' <<<"$quota") ))
    (( remaining >= 120 )) || { printf 'DeveloperTier quota insufficient: %d.\n' "$remaining" >&2; exit 16; }
    azd ai finetuning jobs deploy --project-endpoint "$project_endpoint" --subscription "$subscription_id" --job-id "$job_id" --deployment-name "$deployment_name" --model-format OpenAI --sku DeveloperTier --capacity 100 --version 1 --no-prompt
    ;;

  agent-v4)
    deployments_url="https://management.azure.com/subscriptions/$subscription_id/resourceGroups/$resource_group/providers/Microsoft.CognitiveServices/accounts/$foundry_account/deployments"
    state="$(az rest --method get --url "$deployments_url/$deployment_name?api-version=2025-06-01" -o json | jq -r '.properties.provisioningState')"
    [[ "$state" == "Succeeded" ]] || { printf '%s is not ready: %s\n' "$deployment_name" "$state" >&2; exit 17; }
    azd env set AZURE_AI_MODEL_DEPLOYMENT_NAME "$deployment_name"
    azd env set CONTOSO_CONFIGURATION curated-student
    azd env set CONTOSO_INSTRUCTION_SHA "$(sha256sum "$instruction_file"|cut -d' ' -f1)"
    version="$(azd env get-value AGENT_CONTOSO_TRAVEL_VERSION 2>/dev/null || true)"
    case "$version" in 3) azd deploy contoso-travel --no-prompt ;; 4) printf 'Reusing recorded contoso-travel v4.\n' ;; *) printf 'Expected agent v3 or v4; found %s.\n' "$version" >&2; exit 18 ;; esac
    [[ "$(azd env get-value AGENT_CONTOSO_TRAVEL_VERSION)" == "4" ]] || { printf 'Expected immutable agent v4.\n' >&2; exit 19; }
    bash infra/deploy-supplemental.sh
    .venv/bin/python infra/switch-agent-version.py --version 4 --project-endpoint "$project_endpoint" --apply
    azd ai agent invoke 'For employee EMP-001, state the applicable booking lead-time policy and cite the rule ID. Do not prepare or submit an itinerary.' --no-prompt
    printf 'Curated-response student v4 is active.\nEvaluation command:\n'
    printf '  cd src/agent && AZURE_DEV_USER_AGENT=microsoft_foundry_skill azd ai agent eval run --agent contoso-travel --config eval-curated-student-v4.yaml --name brk330-v4-curated-student\n'
    ;;
esac