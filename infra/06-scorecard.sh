#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Turn v1's traces into a scorecard that defines a good answer.

Usage: bash infra/06-scorecard.sh [--check] [--environment brk330-NNNNNN]

Uploads the exploring and testing question sets, then asks Foundry to draft the
brk330-travel-scorecard from four inputs: v1's exploring traces (step 04), the
v1 agent itself, the exploring questions, and our guidance plus the Insights
findings (step 05). An existing scorecard is reused, never replaced, so every
version is graded the same way. --check runs the local checks only.
EOF
}

source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

apply_flag=(--apply)
environment_arg=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --check) apply_flag=(); shift ;;
    --environment) environment_arg="$2"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
done

use_environment "$environment_arg"
if (( ${#apply_flag[@]} )); then
  [[ -f "$state_root/questions/exploring-v1-latest.json" ]] || fail 9 'Run infra/04-run-questions.sh first; the scorecard is built from those traces.'
  [[ -f "$state_root/insights/findings.json" ]] || printf 'No saved Insights findings; drafting from traces and guidance only.\n'
fi
.venv/bin/python src/scripts/build_scorecard.py "${apply_flag[@]}" --project-endpoint "$project_endpoint"
printf 'Open the draft under %s/scorecard/ and read it before scoring anything.\n' "$state_root"
