#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Ask one version a whole question set, so its traces are ready to study.

Usage: bash infra/04-run-questions.sh [--set exploring|training|testing] [--label v1]
                                      [--repeats N] [--parallel N] [--limit N]
                                      [--environment brk330-NNNNNN]

Defaults: --set exploring --label v1 --repeats 3 --parallel 1.
Running each question three times gives Insights and the scorecard draft a
steady picture instead of one lucky (or unlucky) answer. --parallel 2 or 3
finishes sooner; timings get a little noisier because answers share capacity.

Each question uses a fresh conversation pinned to that version, so the portal
is never switched. Answers, timings, and a per-level summary are saved under
.azure/<environment>/questions/. This makes billable model calls.
EOF
}

source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

question_set="exploring"
label="v1"
repeats=3
parallel=1
limit=""
environment_arg=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --set) question_set="$2"; shift 2 ;;
    --label) label="$2"; shift 2 ;;
    --repeats) repeats="$2"; shift 2 ;;
    --parallel) parallel="$2"; shift 2 ;;
    --limit) limit="$2"; shift 2 ;;
    --environment) environment_arg="$2"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
done
case "$question_set" in exploring|training|testing) ;; *) fail 2 "Unknown set $question_set." ;; esac

use_environment "$environment_arg"
version="$(version_for "$label")"
[[ -n "$version" ]] || fail 9 "$label has not been built yet in $environment_name."

printf 'Asking %s v%s (%s) the %s questions, %s time(s) each.\n' \
  "contoso-travel" "$version" "$label" "$question_set" "$repeats"
extra=()
[[ -z "$limit" ]] || extra+=(--limit "$limit")
.venv/bin/python src/scripts/run_questions.py \
  --set "$question_set" --version "$version" --repeats "$repeats" --parallel "$parallel" "${extra[@]}"
printf 'Wait a few minutes for traces to arrive before running Insights.\n'
