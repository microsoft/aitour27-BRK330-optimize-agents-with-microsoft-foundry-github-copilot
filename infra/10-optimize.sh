#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Let Agent Optimizer try better instructions for the version you picked.

Usage: bash infra/10-optimize.sh PHASE [--from-label v1|v2|v2-quality|v2-alt] [--candidate ID] [--watch]
                                  [--environment brk330-NNNNNN]

Phases:
  submit  Start one optimizer job (3 candidates) from the chosen version.
          It practices on the 12 practice questions, never the testing ones.
  status  Show the job and each candidate's practice score. Add --watch to keep
          checking until the job finishes.
  apply   Download one candidate's files into src/agent/.agent_configs/<ID>/.

Nothing goes live here. Read every candidate, then use infra/11-promote.sh to
turn the one you trust into v3 and retest it on the testing questions.
EOF
}

source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

phase="${1:-}"
if [[ -n "$phase" ]]; then shift; fi
from_label="v1"
candidate=""
watch=false
environment_arg=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --from-label) from_label="$2"; shift 2 ;;
    --candidate) candidate="$2"; shift 2 ;;
    --watch) watch=true; shift ;;
    --environment) environment_arg="$2"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
done
if [[ "$phase" == "--help" || "$phase" == "-h" || -z "$phase" ]]; then usage; exit 0; fi
case "$phase" in submit|status|apply) ;; *) fail 2 "Unknown phase: $phase" ;; esac

use_environment "$environment_arg"
state_dir="$state_root/optimizer"
mkdir -p "$state_dir"
operation_id_file="$state_dir/operation-id.txt"
config=".eval-optimizer.yaml"

case "$phase" in
  submit)
    if [[ -s "$operation_id_file" ]]; then
      printf 'Reusing optimizer job %s. Check it with: bash infra/10-optimize.sh status\n' "$(cat "$operation_id_file")"
      exit 0
    fi
    key="$(label_key "$from_label")"
    version="$(version_for "$from_label")"
    [[ -n "$version" ]] || fail 9 "$from_label has not been built yet in $environment_name."
    model="$(azd env get-value "BRK330_MODEL_$key")"
    agent_config="$(azd env get-value "BRK330_CONFIG_$key")"
    .venv/bin/python - "$version" "$model" "$agent_config" "src/agent/$config" <<'PY'
import json
import sys
from pathlib import Path

import yaml

version, model, agent_config, output = sys.argv[1:]
settings = yaml.safe_load(Path("src/agent/eval.yaml").read_text(encoding="utf-8"))
settings["name"] = "brk330-practice"
settings["agent"].update(
    {"version": version, "model": model, "config": f".agent_configs/{agent_config}/metadata.yaml"}
)
# The optimizer ignores max_samples, so hand it only the 12 practice rows, never the testing set.
rows = [json.loads(line) for line in Path("data/questions/exploring.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
practice = [row for row in rows if row.get("practice")]
assert len(practice) == 12, f"expected 12 practice rows, found {len(practice)}"
Path("src/agent/.eval-practice.jsonl").write_text("".join(json.dumps(row) + "\n" for row in practice), encoding="utf-8")
settings["dataset"] = {"local_uri": ".eval-practice.jsonl", "name": "brk330-practice", "version": "1"}
settings["options"]["max_samples"] = 12
Path(output).write_text(yaml.safe_dump(settings, sort_keys=False), encoding="utf-8")
PY
    log="$state_dir/submit.log"
    recorded_version="$(azd env get-value AGENT_CONTOSO_TRAVEL_VERSION)"
    source_metadata="src/agent/.agent_configs/$agent_config/metadata.yaml"
    cp "$source_metadata" "$state_dir/source-metadata.yaml"
    restore_local_state() {
      cp "$state_dir/source-metadata.yaml" "$source_metadata"
      azd env set AGENT_CONTOSO_TRAVEL_VERSION "$recorded_version" >/dev/null
    }
    trap restore_local_state EXIT
    azd env set AGENT_CONTOSO_TRAVEL_VERSION "$version" >/dev/null
    printf 'Starting the optimizer from %s (contoso-travel version %s)...\n' "$from_label" "$version"
    (cd src/agent && azd ai agent optimize --agent contoso-travel --config "$config" --no-wait --no-prompt) | tee "$log"
    operation_id="$(grep -Eo 'opt_[A-Za-z0-9_-]+' "$log" | tail -1 || true)"
    [[ -n "$operation_id" ]] || fail 8 "No optimizer job ID returned; read $log."
    printf '%s\n' "$operation_id" > "$operation_id_file"
    printf '%s\n' "$from_label" > "$state_dir/from-label.txt"
    printf 'Optimizer job started: %s\nCheck it with: bash infra/10-optimize.sh status\n' "$operation_id"
    ;;

  status)
    [[ -s "$operation_id_file" ]] || fail 9 'Run submit first.'
    operation_id="$(cat "$operation_id_file")"
    # Passing --project-endpoint returns an empty result; azd resolves the project itself.
    watch_flag=()
    [[ "$watch" != true ]] || watch_flag=(--watch)
    (cd src/agent && azd ai agent optimize status "$operation_id" "${watch_flag[@]}" --no-prompt)
    (cd src/agent && azd ai agent optimize status "$operation_id" --output json --no-prompt) > "$state_dir/status.json"
    printf '\nFull details saved to %s/status.json\n' "$state_dir"
    printf 'Read every candidate before choosing one. A higher practice score is a hint, not proof.\n'
    printf 'Download one with: bash infra/10-optimize.sh apply --candidate <ID>\n'
    ;;

  apply)
    [[ -n "$candidate" ]] || fail 2 'Pass --candidate <ID> from the status output.'
    cp azure.yaml "$state_dir/azure.yaml.before-apply"
    # optimize apply also rewrites the baseline config; keep every existing version's files as they were.
    rm -rf "$state_dir/agent_configs.before-apply"
    cp -R src/agent/.agent_configs "$state_dir/agent_configs.before-apply"
    (cd src/agent && azd ai agent optimize apply --agent contoso-travel --candidate "$candidate" --no-prompt)
    if ! cmp -s azure.yaml "$state_dir/azure.yaml.before-apply"; then
      cp "$state_dir/azure.yaml.before-apply" azure.yaml
      printf 'Kept azure.yaml unchanged; versions pick their config through CONTOSO_CONFIGURATION.\n'
    fi
    for saved in "$state_dir/agent_configs.before-apply"/*/; do
      name="$(basename "$saved")"
      [[ "$name" != "$candidate" ]] || continue
      if ! diff -rq "$saved" "src/agent/.agent_configs/$name" >/dev/null 2>&1; then
        rm -rf "src/agent/.agent_configs/$name"
        cp -R "$saved" "src/agent/.agent_configs/$name"
        printf 'Kept .agent_configs/%s unchanged; the candidate lives in its own folder.\n' "$name"
      fi
    done
    [[ -s "src/agent/.agent_configs/$candidate/metadata.yaml" ]] || fail 10 "Candidate files did not arrive in src/agent/.agent_configs/$candidate/."
    printf 'Candidate files: src/agent/.agent_configs/%s/\n' "$candidate"
    printf 'Compare its instructions.md with the baseline, then run:\n'
    printf '  bash infra/11-promote.sh deploy --candidate %s\n' "$candidate"
    ;;
esac