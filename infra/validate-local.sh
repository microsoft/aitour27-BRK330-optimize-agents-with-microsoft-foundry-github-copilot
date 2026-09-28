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
"$python_bin" -m compileall -q src infra/switch-agent-version.py
"$python_bin" -m pytest -q src/agent/tests src/web/tests
node --check src/web/static/app.js

for file in .devcontainer/devcontainer.json .vscode/mcp.json; do
  "$python_bin" -m json.tool "$file" >/dev/null
done

"$python_bin" - <<'PY'
import yaml
from pathlib import Path
manifest = yaml.safe_load(Path("azure.yaml").read_text(encoding="utf-8"))
assert manifest["infra"]["provider"] == "microsoft.foundry"
assert set(manifest["services"]) == {"ai-project", "contoso-travel", "web"}
assert manifest["services"]["contoso-travel"]["codeConfiguration"]["runtime"] == "python_3_13"
PY

for script in .devcontainer/post-create.sh infra/*.sh; do
  bash -n "$script"
done

bicep_output="$(mktemp --suffix=.json)"
trap 'rm -f "$bicep_output"' EXIT
if command -v az >/dev/null 2>&1; then
  az bicep build --file infra/supplemental.bicep --outfile "$bicep_output" >/dev/null
elif command -v bicep >/dev/null 2>&1; then
  bicep build infra/supplemental.bicep --outfile "$bicep_output" >/dev/null
elif [[ -x /tmp/bicep ]]; then
  /tmp/bicep build infra/supplemental.bicep --outfile "$bicep_output" >/dev/null
else
  printf 'Bicep CLI not found. Rebuild the dev container before retrying.\n' >&2
  exit 3
fi
printf 'Local validation passed.\n'
