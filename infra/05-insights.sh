#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Ask Agent Insights to read recent traces and explain where the agent struggles.

Usage: bash infra/05-insights.sh [--label v1] [--inspect] [--lookback-hours N] [--environment brk330-NNNNNN]

By default this starts one Insights run over the last 3 hours of traces using
the insights-judge deployment, waits for it, prints the findings, and saves
them (without IDs) to .azure/<environment>/insights/findings.json so step 06
can use them. --inspect only reads and saves existing findings.

--label names whose traces you're checking. v1 saves to findings.json (used by
step 06); any other label saves to findings-<label>.json, so a later check on
v3 never overwrites v1's findings. Insights reads every trace in the window, so
for a later check, run the exploring questions on that version first and use a
short window (for example --lookback-hours 1).
EOF
}

source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

run_flag=(--run)
lookback=3
label="v1"
environment_arg=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --inspect) run_flag=(); shift ;;
    --lookback-hours) lookback="$2"; shift 2 ;;
    --label) label="$2"; shift 2 ;;
    --environment) environment_arg="$2"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
done

use_environment "$environment_arg"
label_key "$label" >/dev/null
[[ -f "$state_root/questions/exploring-v$(version_for "$label")-latest.json" ]] || \
  printf 'Tip: run bash infra/04-run-questions.sh --label %s first so there are fresh traces to read.\n' "$label"
save_file="$state_root/insights/findings.json"
[[ "$label" == v1 ]] || save_file="$state_root/insights/findings-$label.json"

.venv/bin/python src/scripts/run_agent_insights.py \
  "${run_flag[@]}" \
  --lookback-hours "$lookback" \
  --model-deployment insights-judge \
  --project-endpoint "$project_endpoint" \
  --save "$save_file"
