#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Run all non-cloud BRK330 validation checks.

Usage: bash infra/01-validate.sh [--verbose]

Requires the supported dev container and completed post-create setup. The command
reads repository files, compiles code/templates, and runs tests. It creates no
Azure resources and does not authenticate. Successful check output is hidden by
default; --verbose shows it.
EOF
}

verbose=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --verbose) verbose=true; shift ;;
    --help|-h) usage; exit 0 ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
done

validation_log="$(mktemp)"
bicep_output_dir=""
cleanup() {
  rm -f "$validation_log"
  [[ -z "$bicep_output_dir" ]] || rm -rf "$bicep_output_dir"
}
report_failure() {
  status=$?
  trap - ERR
  printf 'Local validation: NOT READY.\n' >&2
  exit "$status"
}
run_check() {
  if [[ "$verbose" == true ]]; then
    "$@"
    return
  fi
  if "$@" >"$validation_log" 2>&1; then
    return
  else
    status=$?
  fi
  cat "$validation_log" >&2
  return "$status"
}
trap cleanup EXIT
trap report_failure ERR

# -----------------------------------------------------------------------------
# Resolve the repository Python environment before running any checks.
python_bin="${PYTHON_BIN:-.venv/bin/python}"
if [[ "$python_bin" == */* ]]; then
  python_available=false
  [[ -x "$python_bin" ]] && python_available=true
else
  python_available=false
  command -v "$python_bin" >/dev/null 2>&1 && python_available=true
fi
if [[ "$python_available" != true ]]; then
  printf 'Python environment not found at %s. Rebuild the container or run post-create.\n' "$python_bin" >&2
  printf 'Local validation: NOT READY.\n' >&2
  exit 2
fi

# -----------------------------------------------------------------------------
# Validate fixtures, the three question sets, and the scorecard inputs.
run_check "$python_bin" src/scripts/validate_fixtures.py
run_check "$python_bin" src/scripts/questions.py
run_check "$python_bin" src/scripts/build_scorecard.py

# -----------------------------------------------------------------------------
# Compile source, run focused agent/web tests, and parse browser JavaScript.
run_check "$python_bin" -m compileall -q src infra/switch-agent-version.py
run_check "$python_bin" -m pytest -q src/agent/tests src/web/tests
run_check node --check src/web/static/app.js

# -----------------------------------------------------------------------------
# Parse standalone JSON configuration files.
for file in \
  .devcontainer/devcontainer.json \
  .vscode/mcp.json \
  data/scorecard-guidance.json \
  data/fine-tuning-review.json; do
  "$python_bin" -m json.tool "$file" >/dev/null
done

# -----------------------------------------------------------------------------
# Verify model deployments and the shared test config together.
"$python_bin" - <<'PY'
import yaml
from pathlib import Path
manifest = yaml.safe_load(Path("azure.yaml").read_text(encoding="utf-8"))
assert manifest["infra"]["provider"] == "microsoft.foundry"
assert set(manifest["services"]) == {"ai-project", "contoso-travel", "web"}
assert manifest["services"]["contoso-travel"]["codeConfiguration"]["runtime"] == "python_3_13"
capacity = {
  deployment["name"]: deployment["sku"]["capacity"]
  for deployment in manifest["services"]["ai-project"]["deployments"]
}
assert capacity == {
  "gpt-5.4": 300,
  "gpt-5.4-mini": 300,
  "gpt-4.1-mini": 100,
  "model-router": 300,
  "insights-judge": 500,
}, capacity
candidate_selector = manifest["services"]["contoso-travel"]["env"]["OPTIMIZATION_CANDIDATE_ID"]
assert candidate_selector == "${CONTOSO_CONFIGURATION}"
eval_config = yaml.safe_load(Path("src/agent/eval.yaml").read_text(encoding="utf-8"))
assert eval_config["dataset"]["name"] == "brk330-testing"
assert eval_config["dataset"]["local_uri"] == "../../data/questions/testing.jsonl"
assert eval_config["evaluators"] == [{"name": "brk330-travel-scorecard", "version": "1"}]
assert eval_config["options"]["max_samples"] == 24
assert eval_config["options"]["max_candidates"] == 3
PY

# -----------------------------------------------------------------------------
# Check every shell entry point without executing its cloud operations.
for script in .devcontainer/post-create.sh infra/*.sh; do
  bash -n "$script"
done

# -----------------------------------------------------------------------------
# Compile every Bicep template into a temporary directory.
bicep_output_dir="$(mktemp -d)"
for template in infra/*.bicep; do
  output="$bicep_output_dir/$(basename "${template%.bicep}").json"
  if command -v az >/dev/null 2>&1; then
    az bicep build --file "$template" --outfile "$output" >/dev/null
  elif command -v bicep >/dev/null 2>&1; then
    bicep build "$template" --outfile "$output" >/dev/null
  elif [[ -x /tmp/bicep ]]; then
    /tmp/bicep build "$template" --outfile "$output" >/dev/null
  else
    printf 'Bicep CLI not found. Rebuild the dev container before retrying.\n' >&2
    printf 'Local validation: NOT READY.\n' >&2
    exit 3
  fi
done
printf 'Local validation: READY.\n'
