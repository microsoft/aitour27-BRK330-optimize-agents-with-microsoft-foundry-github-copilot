#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Run all non-cloud BRK330 validation checks.

Usage: infra/validate-local.sh

Requires the supported dev container and completed post-create setup. The command
reads repository files, compiles code/templates, and runs tests. It creates no
Azure resources and does not authenticate.
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

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
  exit 2
fi

# -----------------------------------------------------------------------------
# Validate deterministic fixtures and the frozen local evaluation contract.
"$python_bin" src/scripts/validate_fixtures.py
"$python_bin" src/scripts/setup_lightweight_evaluation.py >/dev/null

# -----------------------------------------------------------------------------
# Compile source, run focused agent/web tests, and parse browser JavaScript.
"$python_bin" -m compileall -q src infra/switch-agent-version.py
"$python_bin" -m pytest -q src/agent/tests src/web/tests
node --check src/web/static/app.js

# -----------------------------------------------------------------------------
# Parse standalone JSON configuration files.
for file in \
  .devcontainer/devcontainer.json \
  .vscode/mcp.json \
  data/evaluation/lightweight-v1/rubric-source.json \
  data/training/fine-tuning-scope-v1.json; do
  "$python_bin" -m json.tool "$file" >/dev/null
done

# -----------------------------------------------------------------------------
# Parse every training prompt as an independent JSONL record.
while IFS= read -r line; do
  printf '%s' "$line" | "$python_bin" -m json.tool >/dev/null
done < data/training/trace-seed-prompts.jsonl

while IFS= read -r line; do
  printf '%s' "$line" | "$python_bin" -m json.tool >/dev/null
done < data/training/curated-gold-v1.jsonl

# -----------------------------------------------------------------------------
# Verify deployment, versioned evaluation, and holdout invariants together.
"$python_bin" - <<'PY'
import json
import yaml
from pathlib import Path
manifest = yaml.safe_load(Path("azure.yaml").read_text(encoding="utf-8"))
assert manifest["infra"]["provider"] == "microsoft.foundry"
assert set(manifest["services"]) == {"ai-project", "contoso-travel", "web"}
assert manifest["services"]["contoso-travel"]["codeConfiguration"]["runtime"] == "python_3_13"
deployments = {
  deployment["name"]: deployment
  for deployment in manifest["services"]["ai-project"]["deployments"]
}
assert deployments["gpt-5.4"]["sku"]["capacity"] == 200
assert deployments["gpt-5.4-mini"]["sku"]["capacity"] == 200
assert deployments["gpt-4.1-mini"]["sku"]["capacity"] == 100
candidate_selector = manifest["services"]["contoso-travel"]["env"]["OPTIMIZATION_CANDIDATE_ID"]
assert candidate_selector == "${CONTOSO_CONFIGURATION}"
eval_config = yaml.safe_load(Path("src/agent/eval.yaml").read_text(encoding="utf-8"))
assert eval_config["dataset"]["version"] == "2"
assert eval_config["options"]["max_samples"] == 4
assert eval_config["options"]["max_candidates"] == 3
router_eval = yaml.safe_load(
  Path("src/agent/eval-model-router-v2.yaml").read_text(encoding="utf-8")
)
assert router_eval["agent"]["version"] == "2"
assert router_eval["agent"]["model"] == "model-router"
assert router_eval["dataset"] == eval_config["dataset"]
assert router_eval["evaluators"] == eval_config["evaluators"]
assert router_eval["options"] == eval_config["options"]
student_eval = yaml.safe_load(
  Path("src/agent/eval-student-v3.yaml").read_text(encoding="utf-8")
)
assert student_eval["agent"]["version"] == "3"
assert student_eval["agent"]["model"] == "contoso-student"
assert student_eval["dataset"] == eval_config["dataset"]
assert student_eval["evaluators"] == eval_config["evaluators"]
assert student_eval["options"] == eval_config["options"]
curated_eval = yaml.safe_load(
  Path("src/agent/eval-curated-student-v4.yaml").read_text(encoding="utf-8")
)
assert curated_eval["agent"]["version"] == "4"
assert curated_eval["agent"]["model"] == "contoso-curated-student"
assert curated_eval["dataset"] == eval_config["dataset"]
assert curated_eval["evaluators"] == eval_config["evaluators"]
assert curated_eval["options"] == eval_config["options"]
def jsonl(path):
  return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]

def normalized(value):
  return " ".join(value.casefold().split())

seed_prompts = [normalized(row["prompt"]) for row in jsonl("data/training/trace-seed-prompts.jsonl")]
holdout_prompts = {normalized(row["query"]) for row in jsonl("data/evaluation/lightweight-v1/dataset-v2.jsonl")}
assert len(seed_prompts) == 30
assert len(seed_prompts) == len(set(seed_prompts))
assert not set(seed_prompts) & holdout_prompts
PY

# -----------------------------------------------------------------------------
# Check every shell entry point without executing its cloud operations.
for script in .devcontainer/post-create.sh infra/*.sh; do
  bash -n "$script"
done

# -----------------------------------------------------------------------------
# Compile every Bicep template into a temporary directory.
bicep_output_dir="$(mktemp -d)"
trap 'rm -rf "$bicep_output_dir"' EXIT
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
    exit 3
  fi
done
printf 'Local validation passed.\n'
