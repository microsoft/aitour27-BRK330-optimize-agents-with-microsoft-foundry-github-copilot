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

"$python_bin" src/scripts/validate_fixtures.py
"$python_bin" src/scripts/setup_lightweight_evaluation.py >/dev/null
"$python_bin" -m compileall -q src infra/switch-agent-version.py
"$python_bin" -m pytest -q src/agent/tests src/web/tests
node --check src/web/static/app.js

for file in \
  .devcontainer/devcontainer.json \
  .vscode/mcp.json \
  data/evaluation/lightweight-v1/rubric-source.json \
  data/training/fine-tuning-scope-v1.json; do
  "$python_bin" -m json.tool "$file" >/dev/null
done

"$python_bin" - <<'PY'
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
assert deployments["gpt-5.4-mini"]["sku"]["capacity"] == 200
assert (
  manifest["services"]["contoso-travel"]["env"]["OPTIMIZATION_CANDIDATE_ID"]
  == "${CONTOSO_CONFIGURATION}"
)
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
PY

for script in .devcontainer/post-create.sh infra/*.sh; do
  bash -n "$script"
done

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
