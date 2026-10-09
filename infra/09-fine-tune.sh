#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Build a fine-tuned student: teach a smaller model (gpt-4.1-mini) from a teacher
version's reviewed answers.

Usage: bash infra/09-fine-tune.sh PHASE [--teacher-label v1|v3|v3-tools] [--activate] [--environment brk330-NNNNNN]

Phases, in order:
  generate  Ask the teacher the 48 training questions (fresh conversation each time).
  harvest   Collect those answers from traces and pre-fill a review sheet.
  curate    Check your review and write the training and validation files.
  submit    Start one fine-tuning job (or reuse the one already started).
  status    Show the job and its recent logs.
  deploy    Deploy the finished model.
  agent     Create the student agent version.

--teacher-label picks whose answers the student learns from (default v1).
Pass it on generate; later phases remember it. The student keeps the teacher's
instructions and changes only the model, so it's one step from the teacher:
  teacher v1 -> label v2-alt,     deployment contoso-student
  teacher v3 -> label v3-student, deployment contoso-student-v3
  teacher v3-tools -> label v3-tools-student, deployment contoso-student-v3-tools

Testing questions are never used for training. Everything private (answers,
review decisions, training files, job IDs) stays under
.azure/<environment>/fine-tune/<teacher>/. The portal keeps its current version
unless you pass --activate to the agent phase.
EOF
}

source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

phase="${1:-}"
if [[ -n "$phase" ]]; then shift; fi
activate=false
teacher_arg=""
environment_arg=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --activate) activate=true; shift ;;
    --teacher-label) teacher_arg="$2"; shift 2 ;;
    --environment) environment_arg="$2"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
done
if [[ "$phase" == "--help" || "$phase" == "-h" || -z "$phase" ]]; then
  usage
  exit 0
fi
case "$phase" in
  generate|harvest|curate|submit|status|deploy|agent) ;;
  *) printf 'Unknown phase: %s\n' "$phase" >&2; usage >&2; exit 2 ;;
esac

use_environment "$environment_arg"
location="$(azd env get-value AZURE_LOCATION)"
foundry_account="$(azd env get-value AZURE_AI_ACCOUNT_NAME)"
workspace_name="$(azd env get-value AZURE_MONITOR_LOG_ANALYTICS_NAME)"

state_dir="$state_root/fine-tune"
mkdir -p "$state_dir"
teacher_file="$state_dir/teacher-label.txt"
teacher="${teacher_arg:-$(cat "$teacher_file" 2>/dev/null || echo v1)}"
case "$teacher" in
  v1) student_label="v2-alt"; student_deployment="contoso-student" ;;
  v3) student_label="v3-student"; student_deployment="contoso-student-v3" ;;
  v3-tools) student_label="v3-tools-student"; student_deployment="contoso-student-v3-tools" ;;
  *) fail 2 "Teacher must be v1, v3, or v3-tools; got $teacher." ;;
esac
if [[ -n "$teacher_arg" && -s "$teacher_file" && "$(cat "$teacher_file")" != "$teacher_arg" && "$phase" != generate ]]; then
  fail 2 "This fine-tune run uses teacher $(cat "$teacher_file"). Run generate --teacher-label $teacher_arg to start a new one."
fi
teacher_key="$(label_key "$teacher")"
teacher_version="$(version_for "$teacher")"
[[ -n "$teacher_version" ]] || fail 9 "Teacher $teacher is not built yet in $environment_name."
teacher_model="$(env_value "BRK330_MODEL_$teacher_key")"
teacher_config="$(env_value "BRK330_CONFIG_$teacher_key")"
instruction_name="$(.venv/bin/python -c 'import sys, yaml; print(yaml.safe_load(open(sys.argv[1])).get("instruction_file", "instructions.md"))' "src/agent/.agent_configs/$teacher_config/metadata.yaml")"
instruction_file="$(realpath "src/agent/.agent_configs/$teacher_config/$instruction_name")"
student_config="student"
# v3 and v3-tools share a config folder, so each student gets its own.
[[ "$teacher" == v1 ]] || student_config="$teacher_config-$student_label"

run_dir="$state_dir/$teacher"
mkdir -p "$run_dir"
questions_file="data/questions/training.jsonl"
holdout_file="data/questions/testing.jsonl"
scope_file="data/fine-tuning-review.json"
raw_file="$run_dir/traces.raw.json"
candidates_file="$run_dir/traces.candidates.jsonl"
review_file="$run_dir/traces.review.jsonl"
train_file="$run_dir/train.jsonl"
validation_file="$run_dir/validation.jsonl"
provenance_file="$run_dir/provenance.json"
job_id_file="$run_dir/job-id.txt"
printf 'Teacher: %s (contoso-travel version %s, %s). Student: %s on %s.\n' \
  "$teacher" "$teacher_version" "$teacher_model" "$student_label" "$student_deployment"

case "$phase" in
  generate)
    printf '%s\n' "$teacher" > "$teacher_file"
    date -u '+%Y-%m-%dT%H:%M:%SZ' > "$run_dir/generation-start.txt"
    .venv/bin/python src/scripts/run_questions.py --set training --version "$teacher_version" --repeats 1
    date -u '+%Y-%m-%dT%H:%M:%SZ' > "$run_dir/generation-complete.txt"
    printf 'Asked %s all training questions without changing the portal.\n' "$teacher"
    printf 'Wait a few minutes for traces to arrive, then run: bash infra/09-fine-tune.sh harvest\n'
    ;;

  harvest)
    [[ -f "$run_dir/generation-start.txt" ]] || {
      printf 'Run the generate phase first.\n' >&2
      exit 10
    }
    start_time="$(cat "$run_dir/generation-start.txt")"
    end_time="$(cat "$run_dir/generation-complete.txt" 2>/dev/null || date -u '+%Y-%m-%dT%H:%M:%SZ')"
    workspace_id="$(az monitor log-analytics workspace show \
      --workspace-name "$workspace_name" --resource-group "$resource_group" \
      --query customerId -o tsv)"
    query="AppGenAIContent
| where TimeGenerated between (datetime($start_time) .. (datetime($end_time) + 15m))
| where AgentName == \"contoso-travel\"
| where ModelName startswith \"$teacher_model\"
| where isnotempty(InputMessages) and isnotempty(OutputMessages)
| project TimeGenerated, TraceId, SpanId, ParentSpanId, AgentName, ModelName, RoleName, InputMessages, OutputMessages
| order by TimeGenerated asc"
    printf 'KQL harvest query:\n%s\n' "$query"
    # Install the log-analytics extension silently so its prompt never lands in the JSON output.
    AZURE_EXTENSION_USE_DYNAMIC_INSTALL=yes_without_prompt az monitor log-analytics query \
      --workspace "$workspace_id" \
      --analytics-query "$query" \
      -o json > "$raw_file"
    .venv/bin/python src/training/trace_dataset.py transform \
      --raw "$raw_file" \
      --holdout "$holdout_file" \
      --questions "$questions_file" \
      --candidates "$candidates_file" \
      --review "$review_file"
    printf 'Your turn to review: open %s.\n' "$review_file"
    printf 'Category and split are pre-filled. For each answer you would be happy to teach,\n'
    printf 'set accepted to true, give it a review score, tick every check, and write a short reason.\n'
    printf 'You need at least 30 training and 6 validation answers before curate.\n'
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
      --teacher-version "$teacher_version" \
      --teacher-model "$teacher_model" \
      --train "$train_file" \
      --validation "$validation_file" \
      --provenance "$provenance_file"
    sha256sum "$train_file" "$validation_file" "$provenance_file"
    printf 'Training files are ready. Next: bash infra/09-fine-tune.sh submit\n'
    ;;

  submit)
    [[ -s "$train_file" && -s "$validation_file" && -s "$provenance_file" ]] || {
      printf 'Run curate successfully before submit.\n' >&2
      exit 12
    }
    if [[ -s "$job_id_file" ]]; then
      previous_job="$(cat "$job_id_file")"
      previous_status="$(azd ai finetuning jobs show \
        --project-endpoint "$project_endpoint" --subscription "$subscription_id" \
        --id "$previous_job" --output json 2>/dev/null | sed -n '/^[[:space:]]*{/,$p' \
        | jq -r '.. | objects | .status? // empty' 2>/dev/null | head -1 | tr '[:upper:]' '[:lower:]')"
      if [[ "$previous_status" != failed && "$previous_status" != cancelled ]]; then
        printf 'Reusing fine-tuning job %s (%s).\n' "$previous_job" "${previous_status:-unknown}"
        exit 0
      fi
      mv "$job_id_file" "$run_dir/job-id.$previous_job.$previous_status.txt"
      printf 'Previous job %s %s; submitting a new one.\n' "$previous_job" "$previous_status"
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
    submit_log="$run_dir/submit.log"
    job_config="$run_dir/fine-tune-job.yaml"
    suffix="brk330-contoso-student-$teacher"
    cat > "$job_config" <<EOF
name: brk330-contoso-student-$teacher-training
description: Trace-driven SFT of the Caldova concierge, taught by $teacher
model: gpt-4.1-mini
method:
  type: supervised
  supervised:
    hyperparameters:
      epochs: 3
seed: 331
suffix: $suffix
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
        --top 20 --output json > "$run_dir/jobs.json"
      job_id="$(jq -r --arg suffix "$suffix" '.. | objects | select((.suffix? // "") == $suffix) | (.id // .jobId // .job_id // empty)' "$run_dir/jobs.json" | head -1)"
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
      --id "$(cat "$job_id_file")" --logs --output json | tee "$run_dir/job-status.json"
    ;;

  deploy)
    [[ -s "$job_id_file" ]] || { printf 'No persisted job ID. Run submit first.\n' >&2; exit 19; }
    job_id="$(cat "$job_id_file")"
    raw_status="$run_dir/job-status.raw.log"
    azd ai finetuning jobs show \
      --project-endpoint "$project_endpoint" --subscription "$subscription_id" \
      --id "$job_id" --output json > "$raw_status"
    sed -n '/^[[:space:]]*{/,$p' "$raw_status" > "$run_dir/job-status.json"
    jq -e . "$run_dir/job-status.json" >/dev/null || {
      printf 'Fine-tuning status output did not contain valid JSON; inspect %s.\n' "$raw_status" >&2
      exit 20
    }
    status="$(jq -r '.. | objects | .status? // empty' "$run_dir/job-status.json" | head -1 | tr '[:upper:]' '[:lower:]')"
    [[ "$status" == "succeeded" ]] || {
      printf 'Fine-tuning job %s is %s, not succeeded.\n' "$job_id" "${status:-unknown}" >&2
      exit 21
    }
    deployments_url="https://management.azure.com/subscriptions/$subscription_id/resourceGroups/$resource_group/providers/Microsoft.CognitiveServices/accounts/$foundry_account/deployments"
    existing="$(az rest --method get --url "$deployments_url?api-version=2025-06-01" -o json | jq -r --arg name "$student_deployment" '[.value[] | select(.name == $name) | .properties.provisioningState][0] // empty')"
    if [[ "$existing" == "Succeeded" ]]; then
      printf 'Reusing %s deployment.\n' "$student_deployment"
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
        --job-id "$job_id" --deployment-name "$student_deployment" \
        --model-format OpenAI --sku DeveloperTier --capacity 100 --version 1 --no-prompt
    fi
    printf 'Next: bash infra/09-fine-tune.sh agent\n'
    ;;

  agent)
    deployments_url="https://management.azure.com/subscriptions/$subscription_id/resourceGroups/$resource_group/providers/Microsoft.CognitiveServices/accounts/$foundry_account/deployments"
    student_state="$(az rest --method get --url "$deployments_url/$student_deployment?api-version=2025-06-01" -o json | jq -r '.properties.provisioningState')"
    [[ "$student_state" == "Succeeded" ]] || fail 21 "$student_deployment is not ready: $student_state"
    if [[ "$student_config" != student ]]; then
      mkdir -p "src/agent/.agent_configs/$student_config"
      printf 'model: %s\ninstruction_file: ../%s/%s\n' "$student_deployment" "$teacher_config" "$instruction_name" \
        > "src/agent/.agent_configs/$student_config/metadata.yaml"
    fi
    version="$(version_for "$student_label")"
    if [[ -n "$version" ]]; then
      printf 'Reusing %s (contoso-travel version %s).\n' "$student_label" "$version"
    else
      previous_live="$(live_version)"
      deploy_new_version "$student_deployment" "$student_config" "$instruction_file"
      version="$new_version"
      remember_version "$student_label" "$version" "$student_deployment" "$student_config"
      [[ "$activate" == true ]] || go_live "$previous_live"
    fi
    [[ "$activate" != true ]] || go_live "$version"
    smoke_test "$version"
    printf 'Next: bash infra/07-score.sh run --label %s\n' "$student_label"
    ;;
esac