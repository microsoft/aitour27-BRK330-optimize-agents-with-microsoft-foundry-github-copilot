#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Score versions on the testing questions with the same scorecard, then compare.

Usage:
  bash infra/07-score.sh run --label v1|v2|v2-quality|v2-alt|v3|v3-router|v3-student|v3-tools|v3-tools-student [--repeats N] [--environment brk330-NNNNNN]
  bash infra/07-score.sh compare [--environment brk330-NNNNNN]

run      Scores one version on the 24 testing questions (default 3 repeats, so
         one noisy answer does not decide the result). Records each run in
         .azure/<environment>/scores/runs.jsonl. Billable.
compare  Prints one table: mean score, change vs v1, pass rate, easy/medium/hard,
         weakest area, speed, and tokens. A second table shows each scorecard
         dimension's average per version. Read-only.
EOF
}

source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

phase="${1:-}"
[[ -z "$phase" ]] || shift
label=""
repeats=3
environment_arg=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --label) label="$2"; shift 2 ;;
    --repeats) repeats="$2"; shift 2 ;;
    --environment) environment_arg="$2"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
done
case "$phase" in run|compare) ;; ""|--help|-h) usage; exit 0 ;; *) fail 2 "Unknown phase $phase." ;; esac

use_environment "$environment_arg"

if [[ "$phase" == "compare" ]]; then
  .venv/bin/python src/scripts/compare_scores.py
  exit 0
fi

[[ -n "$label" ]] || fail 2 'Pass --label v1, v2, v2-quality, v2-alt, v3, v3-router, v3-student, v3-tools, or v3-tools-student.'
key="$(label_key "$label")"
version="$(version_for "$label")"
[[ -n "$version" ]] || fail 9 "$label has not been built yet in $environment_name."
model="$(azd env get-value "BRK330_MODEL_$key")"
config="$(azd env get-value "BRK330_CONFIG_$key")"
[[ -f "src/agent/.agent_configs/$config/metadata.yaml" ]] || fail 10 "Config folder .agent_configs/$config is missing."

config_file=".eval-$label.yaml"
.venv/bin/python - "$version" "$model" "$config" "src/agent/$config_file" <<'PY'
import sys
from pathlib import Path

import yaml

version, model, config, output = sys.argv[1:]
settings = yaml.safe_load(Path("src/agent/eval.yaml").read_text(encoding="utf-8"))
settings["agent"].update(
    {"version": version, "model": model, "config": f".agent_configs/{config}/metadata.yaml"}
)
Path(output).write_text(yaml.safe_dump(settings, sort_keys=False), encoding="utf-8")
PY

scores_dir="$state_root/scores"
mkdir -p "$scores_dir"
recorded_version="$(azd env get-value AGENT_CONTOSO_TRAVEL_VERSION)"
restore_recorded_version() { azd env set AGENT_CONTOSO_TRAVEL_VERSION "$recorded_version" >/dev/null; }
trap restore_recorded_version EXIT
azd env set AGENT_CONTOSO_TRAVEL_VERSION "$version" >/dev/null

stamp="$(date -u '+%Y%m%dT%H%M%SZ')"
previous_rounds="$(jq -s --arg lbl "$label" '[.[] | select(.label == $lbl)] | length' "$scores_dir/runs.jsonl" 2>/dev/null || echo 0)"
for (( round = 1; round <= repeats; round++ )); do
  number=$((previous_rounds + round))
  name="brk330-$label-$stamp-r$number"
  log="$scores_dir/$name.log"
  printf 'Scoring %s (version %s), round %d (%d of %d in this run)...\n' "$label" "$version" "$number" "$round" "$repeats"
  (cd src/agent && azd ai agent eval run --agent contoso-travel --config "$config_file" --name "$name" --no-prompt) | tee "$log"
  eval_id="$(grep -Eo 'eval_[A-Za-z0-9]+' "$log" | tail -1 || true)"
  run_id="$(grep -Eo 'evalrun_[A-Za-z0-9]+' "$log" | tail -1 || true)"
  [[ -n "$eval_id" && -n "$run_id" ]] || fail 11 "Could not find the eval and run IDs in $log."
  jq -nc --arg lbl "$label" --arg ver "$version" --arg eval_id "$eval_id" --arg run_id "$run_id" --arg name "$name" \
    '{"label": $lbl, "version": $ver, "eval_id": $eval_id, "run_id": $run_id, "name": $name}' >> "$scores_dir/runs.jsonl"
done
printf 'Done. Compare versions with: bash infra/07-score.sh compare\n'
