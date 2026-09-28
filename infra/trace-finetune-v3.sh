#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Build and deploy trace-driven fine-tuned agent v3 in resumable phases.

Usage: infra/trace-finetune-v3.sh PHASE --environment brk330-NNNNNN

Phases:
  generate  Invoke retained v1 in isolated sessions for training-only prompts.
  harvest   Export v1 AppGenAIContent rows and create a human review template.
  curate    Validate the completed review and create deterministic 20/4 SFT data.
  submit    Check fine-tuning quota and submit or reuse one SFT job.
  status    Show the persisted fine-tuning job and recent logs.
  deploy    Deploy a succeeded job as contoso-student on DeveloperTier capacity 100.
  agent-v3  Create/reuse immutable agent v3, activate, smoke-test, print eval command.

Generated trace content, review decisions, SFT files, logs, and job state stay
under ignored .azure/<environment>/training-v3/. The script never deletes Azure
resources and refuses the protected prototype resource group.
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
if [[ "$phase" == "--help" || "$phase" == "-h" || -z "$phase" ]]; then
  usage
  exit 0
fi
case "$phase" in
  generate|harvest|curate|submit|status|deploy|agent-v3) ;;
  *) printf 'Unknown phase: %s\n' "$phase" >&2; usage >&2; exit 2 ;;
esac
if [[ ! "$environment_name" =~ ^brk330-[0-9]{6}$ ]]; then
  printf 'Environment must match brk330-NNNNNN.\n' >&2
  exit 3
fi
for command_name in az azd jq python3 sha256sum; do
  command -v "$command_name" >/dev/null 2>&1 || {
    printf 'Missing command %s. Rebuild the dev container.\n' "$command_name" >&2
    exit 4
  }
done
[[ -x .venv/bin/python ]] || {
  printf 'Python environment not found at .venv/bin/python.\n' >&2
  exit 5
}

export AZURE_DEV_USER_AGENT=microsoft_foundry_skill
az account show >/dev/null
azd auth login --check-status >/dev/null
azd env select "$environment_name"

actual_environment="$(azd env get-value AZURE_ENV_NAME)"
resource_group="$(azd env get-value AZURE_RESOURCE_GROUP)"
subscription_id="$(azd env get-value AZURE_SUBSCRIPTION_ID)"
location="$(azd env get-value AZURE_LOCATION)"
foundry_account="$(azd env get-value AZURE_AI_ACCOUNT_NAME)"
project_endpoint="$(azd env get-value FOUNDRY_PROJECT_ENDPOINT 2>/dev/null || azd env get-value AZURE_AI_PROJECT_ENDPOINT)"
workspace_name="$(azd env get-value AZURE_MONITOR_LOG_ANALYTICS_NAME)"
if [[ "$actual_environment" != "$environment_name" ]]; then
  printf 'Selected environment %s, expected %s.\n' "$actual_environment" "$environment_name" >&2
  exit 6
fi
if [[ "$resource_group" == "rg-brk330-concierge" ]]; then
  printf 'Refusing to modify protected prototype resource group.\n' >&2
  exit 7
fi
if [[ ! "$resource_group" =~ ^rg-aitour-brk330-[0-9]{6}$ ]]; then
  printf 'Resource group %s is outside the generated BRK330 naming contract.\n' "$resource_group" >&2
  exit 8
fi
az account set --subscription "$subscription_id"

state_dir=".azure/$environment_name/training-v3"
mkdir -p "$state_dir"
seed_file="data/training/trace-seed-prompts.jsonl"
holdout_file="data/evaluation/lightweight-v1/dataset-v2.jsonl"
scope_file="data/training/fine-tuning-scope-v1.json"
instruction_file="src/agent/.agent_configs/baseline/instructions.md"
raw_file="$state_dir/v1-traces.raw.json"
candidates_file="$state_dir/v1-traces.candidates.jsonl"
review_file="$state_dir/v1-traces.review.jsonl"
train_file="$state_dir/train.jsonl"
validation_file="$state_dir/validation.jsonl"
provenance_file="$state_dir/provenance.json"
job_id_file="$state_dir/job-id.txt"

case "$phase" in
  generate)
    recorded_version="$(azd env get-value AGENT_CONTOSO_TRAVEL_VERSION 2>/dev/null || true)"
    if [[ "$recorded_version" != "2" && "$recorded_version" != "3" ]]; then
      printf 'Trace generation expects retained v2 or v3; found %s.\n' "${recorded_version:-unset}" >&2
      exit 9
    fi
    teacher_capacity=200
    quota_reserve=40
    arm_location="https://management.azure.com/subscriptions/$subscription_id/providers/Microsoft.CognitiveServices/locations/$location"
    deployments_url="https://management.azure.com/subscriptions/$subscription_id/resourceGroups/$resource_group/providers/Microsoft.CognitiveServices/accounts/$foundry_account/deployments"
    quota="$(az rest --method get --url "$arm_location/usages?api-version=2025-06-01" -o json | jq -c '.value[] | select(.name.value == "OpenAI.GlobalStandard.gpt-5.4")')"
    [[ -n "$quota" ]] || { printf 'Teacher quota record was not returned.\n' >&2; exit 10; }
    remaining=$(( $(jq -r '.limit' <<<"$quota") - $(jq -r '.currentValue' <<<"$quota") ))
    existing_capacity="$(az rest --method get --url "$deployments_url/gpt-5.4?api-version=2025-06-01" -o json | jq -r '.sku.capacity')"
    additional_capacity=$((teacher_capacity - existing_capacity))
    if (( additional_capacity < 0 )); then additional_capacity=0; fi
    required_remaining=$((additional_capacity + quota_reserve))
    if (( remaining < required_remaining )); then
      printf 'Teacher quota is insufficient: remaining=%d, required=%d (%d additional + %d reserve).\n' \
        "$remaining" "$required_remaining" "$additional_capacity" "$quota_reserve" >&2
      exit 11
    fi
    printf 'Teacher quota: remaining=%d; current capacity=%d; target=%d; reserve=%d.\n' \
      "$remaining" "$existing_capacity" "$teacher_capacity" "$quota_reserve"
    az deployment group create \
      --subscription "$subscription_id" \
      --resource-group "$resource_group" \
      --name "brk330-teacher-capacity-$environment_name" \
      --template-file infra/teacher-capacity.bicep \
      --parameters foundryAccountName="$foundry_account" capacity="$teacher_capacity" \
      --query properties.outputs -o table
    date -u '+%Y-%m-%dT%H:%M:%SZ' > "$state_dir/generation-start.txt"
    : > "$state_dir/generation.log"
    count=0
    while IFS= read -r prompt; do
      count=$((count + 1))
      printf '\n[%02d] %s\n' "$count" "$prompt" | tee -a "$state_dir/generation.log"
      azd ai agent invoke \
        --version 1 \
        --protocol responses \
        --new-session \
        --new-conversation \
        "$prompt" \
        --no-prompt | tee -a "$state_dir/generation.log"
    done < <(jq -r '.prompt' "$seed_file")
    date -u '+%Y-%m-%dT%H:%M:%SZ' > "$state_dir/generation-complete.txt"
    printf 'Generated %d isolated v1 training traces without changing the active endpoint.\n' "$count"
    printf 'Wait for telemetry ingestion, then run harvest.\n'
    ;;

  harvest)
    [[ -f "$state_dir/generation-start.txt" ]] || {
      printf 'Run the generate phase first.\n' >&2
      exit 10
    }
    start_time="$(cat "$state_dir/generation-start.txt")"
    workspace_id="$(az monitor log-analytics workspace show \
      --workspace-name "$workspace_name" --resource-group "$resource_group" \
      --query customerId -o tsv)"
    query="AppGenAIContent
| where TimeGenerated >= datetime($start_time)
| where AgentName == \"contoso-travel\"
| where ModelName in (\"gpt-5.4\", \"gpt-5.4-2026-03-05\")
| where isnotempty(InputMessages) and isnotempty(OutputMessages)
| project TimeGenerated, TraceId, SpanId, ParentSpanId, AgentName, ModelName, RoleName, InputMessages, OutputMessages
| order by TimeGenerated asc"
    printf 'KQL harvest query:\n%s\n' "$query"
    az monitor log-analytics query \
      --workspace "$workspace_id" \
      --analytics-query "$query" \
      -o json > "$raw_file"
    .venv/bin/python src/training/trace_dataset.py transform \
      --raw "$raw_file" \
      --holdout "$holdout_file" \
      --candidates "$candidates_file" \
      --review "$review_file"
    printf 'Human review required. Edit %s; set accepted, split, category, rubric_score, every hard gate, and review_reason.\n' "$review_file"
    printf 'Do not run curate until at least 20 train and 4 validation traces pass review.\n'
    ;;

  curate)
    [[ -f "$review_file" ]] || {
      printf 'Run harvest and complete %s first.\n' "$review_file" >&2
      exit 11
    }
    .venv/bin/python src/training/trace_dataset.py curate \
      --candidates "$candidates_file" \
      --review "$review_file" \
      --holdout "$holdout_file" \
      --scope "$scope_file" \
      --instructions "$instruction_file" \
      --train "$train_file" \
      --validation "$validation_file" \
      --provenance "$provenance_file"
    sha256sum "$train_file" "$validation_file" "$provenance_file"
    printf 'Screenshot checkpoint: review decisions and 20/4 split (save as Trace-Dataset-Curation.png).\n'
    ;;

  submit)
    [[ -s "$train_file" && -s "$validation_file" && -s "$provenance_file" ]] || {
      printf 'Run curate successfully before submit.\n' >&2
      exit 12
    }
    if [[ -s "$job_id_file" ]]; then
      printf 'Reusing fine-tuning job %s.\n' "$(cat "$job_id_file")"
      exit 0
    fi
    arm_location="https://management.azure.com/subscriptions/$subscription_id/providers/Microsoft.CognitiveServices/locations/$location"
    quota="$(az rest --method get --url "$arm_location/usages?api-version=2025-06-01" -o json | jq -c '.value[] | select(.name.value == "OpenAI.GlobalStandard.gpt4.1-mini-finetune")')"
    [[ -n "$quota" ]] || { printf 'Fine-tuning quota record was not returned.\n' >&2; exit 13; }
    remaining=$(( $(jq -r '.limit' <<<"$quota") - $(jq -r '.currentValue' <<<"$quota") ))
    if (( remaining < 10 )); then
      printf 'Fine-tuning quota is insufficient: remaining=%d, required=10.\n' "$remaining" >&2
      exit 14
    fi
    printf 'Fine-tuning quota remaining: %d.\n' "$remaining"
    deployments_url="https://management.azure.com/subscriptions/$subscription_id/resourceGroups/$resource_group/providers/Microsoft.CognitiveServices/accounts/$foundry_account/deployments"
    existing_base="$(az rest --method get --url "$deployments_url?api-version=2025-06-01" -o json | jq -r '[.value[] | select(.name == "gpt-4.1-mini") | .properties.provisioningState][0] // empty')"
    if [[ "$existing_base" == "Succeeded" ]]; then
      printf 'Reusing gpt-4.1-mini base deployment.\n'
    else
      base_quota="$(az rest --method get --url "$arm_location/usages?api-version=2025-06-01" -o json | jq -c '.value[] | select(.name.value == "OpenAI.GlobalStandard.gpt4.1-mini")')"
      [[ -n "$base_quota" ]] || { printf 'gpt-4.1-mini inference quota record was not returned.\n' >&2; exit 15; }
      base_remaining=$(( $(jq -r '.limit' <<<"$base_quota") - $(jq -r '.currentValue' <<<"$base_quota") ))
      if (( base_remaining < 120 )); then
        printf 'gpt-4.1-mini inference quota is insufficient: remaining=%d, required=120.\n' "$base_remaining" >&2
        exit 16
      fi
      az deployment group create \
        --subscription "$subscription_id" \
        --resource-group "$resource_group" \
        --name "brk330-student-base-$environment_name" \
        --template-file infra/student-base.bicep \
        --parameters foundryAccountName="$foundry_account" capacity=100 \
        --query properties.outputs -o table
    fi
    submit_log="$state_dir/submit.log"
    job_config="$state_dir/fine-tune-job.yaml"
    cat > "$job_config" <<EOF
name: brk330-contoso-student-training
description: Trace-driven SFT of the Caldova concierge baseline
model: gpt-4.1-mini
method:
  type: supervised
  supervised:
    hyperparameters:
      epochs: 3
seed: 331
suffix: brk330-contoso-student-v1
extra_body:
  trainingType: GlobalStandard
training_file: local:$train_file
validation_file: local:$validation_file
EOF
    azd ai finetuning jobs submit \
      --project-endpoint "$project_endpoint" \
      --subscription "$subscription_id" \
      --file "$job_config" \
      --no-prompt | tee "$submit_log"
    job_id="$(grep -Eo 'ftjob-[A-Za-z0-9_-]+' "$submit_log" | tail -1 || true)"
    if [[ -z "$job_id" ]]; then
      azd ai finetuning jobs list \
        --project-endpoint "$project_endpoint" --subscription "$subscription_id" \
        --top 20 --output json > "$state_dir/jobs.json"
      job_id="$(jq -r '.. | objects | select((.suffix? // "") == "brk330-contoso-student-v1") | (.id // .jobId // .job_id // empty)' "$state_dir/jobs.json" | head -1)"
    fi
    [[ -n "$job_id" ]] || { printf 'Submission returned no recoverable job ID; inspect %s.\n' "$submit_log" >&2; exit 17; }
    printf '%s\n' "$job_id" > "$job_id_file"
    printf 'Fine-tuning job submitted: %s\n' "$job_id"
    printf 'Run the status phase later; this script does not poll indefinitely.\n'
    ;;

  status)
    [[ -s "$job_id_file" ]] || { printf 'No persisted job ID. Run submit first.\n' >&2; exit 18; }
    azd ai finetuning jobs show \
      --project-endpoint "$project_endpoint" --subscription "$subscription_id" \
      --id "$(cat "$job_id_file")" --logs --output json | tee "$state_dir/job-status.json"
    ;;

  deploy)
    [[ -s "$job_id_file" ]] || { printf 'No persisted job ID. Run submit first.\n' >&2; exit 19; }
    job_id="$(cat "$job_id_file")"
    raw_status="$state_dir/job-status.raw.log"
    azd ai finetuning jobs show \
      --project-endpoint "$project_endpoint" --subscription "$subscription_id" \
      --id "$job_id" --output json > "$raw_status"
    sed -n '/^[[:space:]]*{/,$p' "$raw_status" > "$state_dir/job-status.json"
    jq -e . "$state_dir/job-status.json" >/dev/null || {
      printf 'Fine-tuning status output did not contain valid JSON; inspect %s.\n' "$raw_status" >&2
      exit 20
    }
    status="$(jq -r '.. | objects | .status? // empty' "$state_dir/job-status.json" | head -1 | tr '[:upper:]' '[:lower:]')"
    [[ "$status" == "succeeded" ]] || {
      printf 'Fine-tuning job %s is %s, not succeeded.\n' "$job_id" "${status:-unknown}" >&2
      exit 21
    }
    deployments_url="https://management.azure.com/subscriptions/$subscription_id/resourceGroups/$resource_group/providers/Microsoft.CognitiveServices/accounts/$foundry_account/deployments"
    existing="$(az rest --method get --url "$deployments_url?api-version=2025-06-01" -o json | jq -r '[.value[] | select(.name == "contoso-student") | .properties.provisioningState][0] // empty')"
    if [[ "$existing" == "Succeeded" ]]; then
      printf 'Reusing contoso-student deployment.\n'
    else
      arm_location="https://management.azure.com/subscriptions/$subscription_id/providers/Microsoft.CognitiveServices/locations/$location"
      quota="$(az rest --method get --url "$arm_location/usages?api-version=2025-06-01" -o json | jq -c '.value[] | select(.name.value == "OpenAI.DeveloperTier.gpt4.1-mini-finetune")')"
      [[ -n "$quota" ]] || { printf 'Student deployment quota record was not returned.\n' >&2; exit 19; }
      remaining=$(( $(jq -r '.limit' <<<"$quota") - $(jq -r '.currentValue' <<<"$quota") ))
      if (( remaining < 120 )); then
        printf 'Student deployment quota is insufficient: remaining=%d, required=120 (100 target + 20 reserve).\n' "$remaining" >&2
        exit 20
      fi
      azd ai finetuning jobs deploy \
        --project-endpoint "$project_endpoint" --subscription "$subscription_id" \
        --job-id "$job_id" --deployment-name contoso-student \
        --model-format OpenAI --sku DeveloperTier --capacity 100 --version 1 --no-prompt
    fi
    printf 'Screenshot checkpoint: fine-tuning job metrics and contoso-student deployment (save as Fine-Tuning-v3.png).\n'
    ;;

  agent-v3)
    deployments_url="https://management.azure.com/subscriptions/$subscription_id/resourceGroups/$resource_group/providers/Microsoft.CognitiveServices/accounts/$foundry_account/deployments"
    student_state="$(az rest --method get --url "$deployments_url/contoso-student?api-version=2025-06-01" -o json | jq -r '.properties.provisioningState')"
    [[ "$student_state" == "Succeeded" ]] || { printf 'contoso-student is not ready: %s\n' "$student_state" >&2; exit 21; }
    instruction_sha="$(sha256sum "$instruction_file" | cut -d' ' -f1)"
    azd env set AZURE_AI_MODEL_DEPLOYMENT_NAME contoso-student
    azd env set CONTOSO_CONFIGURATION student
    azd env set CONTOSO_INSTRUCTION_SHA "$instruction_sha"
    recorded_version="$(azd env get-value AGENT_CONTOSO_TRAVEL_VERSION 2>/dev/null || true)"
    case "$recorded_version" in
      2) azd deploy contoso-travel --no-prompt ;;
      3) printf 'Reusing recorded contoso-travel v3.\n' ;;
      *) printf 'Expected recorded agent v2 or v3; found %s.\n' "${recorded_version:-unset}" >&2; exit 22 ;;
    esac
    [[ "$(azd env get-value AGENT_CONTOSO_TRAVEL_VERSION)" == "3" ]] || {
      printf 'Expected immutable agent v3 after deploy.\n' >&2
      exit 23
    }
    bash infra/deploy-supplemental.sh
    .venv/bin/python infra/switch-agent-version.py \
      --version 3 --project-endpoint "$project_endpoint" --apply
    agent_json="$(azd ai agent show --output json)"
    [[ "$(jq -r '.version' <<<"$agent_json")" == "3" ]] || { printf 'Agent v3 is not active.\n' >&2; exit 24; }
    [[ "$(jq -r '.definition.environment_variables.AZURE_AI_MODEL_DEPLOYMENT_NAME' <<<"$agent_json")" == "contoso-student" ]] || {
      printf 'Active v3 does not reference contoso-student.\n' >&2
      exit 25
    }
    azd ai agent invoke \
      'For employee EMP-001, state the applicable booking lead-time policy and cite the rule ID. Do not prepare or submit an itinerary.' \
      --no-prompt
    printf 'Fine-tuned student v3 is active. Capture screenshots before evaluation.\n'
    printf 'Evaluation command:\n'
    printf '  cd src/agent && AZURE_DEV_USER_AGENT=microsoft_foundry_skill azd ai agent eval run --agent contoso-travel --config eval-student-v3.yaml --name brk330-v3-student\n'
    ;;
esac