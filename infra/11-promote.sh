#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Turn a reviewed optimizer candidate into v3, or choose which version goes live.

Usage:
  bash infra/11-promote.sh deploy --candidate ID [--environment brk330-NNNNNN]
  bash infra/11-promote.sh router [--environment brk330-NNNNNN]
  bash infra/11-promote.sh go-live --label v1|v2|v2-quality|v2-alt|v3|v3-router|v3-student [--environment brk330-NNNNNN]

deploy   Creates one new agent version from src/agent/.agent_configs/<ID>/
         (downloaded by bash infra/10-optimize.sh apply) and records it as v3. The portal
         keeps its current version. Retest it with: bash infra/07-score.sh run --label v3
router   Optional, after v3. Runs v3's exact instructions on Model Router
         (Balanced) and records it as v3-router. One change from v3: the model.
         Retest it with: bash infra/07-score.sh run --label v3-router
go-live  Points the portal and default endpoint at the chosen version. Only do
         this after comparing scores. Older versions stay available, so you can
         switch back the same way.
EOF
}

source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

phase="${1:-}"
[[ -z "$phase" ]] || shift
candidate=""
label=""
environment_arg=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --candidate) candidate="$2"; shift 2 ;;
    --label) label="$2"; shift 2 ;;
    --environment) environment_arg="$2"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
done
case "$phase" in deploy|router|go-live) ;; ""|--help|-h) usage; exit 0 ;; *) fail 2 "Unknown phase $phase." ;; esac

use_environment "$environment_arg"

case "$phase" in
  deploy)
    [[ -n "$candidate" ]] || fail 2 'Pass --candidate <ID>.'
    candidate_dir="src/agent/.agent_configs/$candidate"
    [[ -s "$candidate_dir/metadata.yaml" ]] || fail 6 "Run infra/10-optimize.sh apply --candidate $candidate first."
    read -r model instruction_file < <(.venv/bin/python - "$candidate_dir" <<'PY'
import sys
from pathlib import Path

import yaml

folder = Path(sys.argv[1])
metadata = yaml.safe_load((folder / "metadata.yaml").read_text(encoding="utf-8"))
print(metadata["model"], (folder / metadata.get("instruction_file", "instructions.md")).resolve())
PY
)
    version="$(version_for v3)"
    if [[ -n "$version" && "$(azd env get-value BRK330_CONFIG_V3)" == "$candidate" ]]; then
      printf 'Reusing v3 (contoso-travel version %s).\n' "$version"
    else
      previous_live="$(live_version)"
      deploy_new_version "$model" "$candidate" "$instruction_file"
      version="$new_version"
      remember_version v3 "$version" "$model" "$candidate"
      go_live "$previous_live"
    fi
    smoke_test "$version"
    printf 'Next: bash infra/07-score.sh run --label v3, then bash infra/07-score.sh compare\n'
    printf 'Optional: bash infra/11-promote.sh router (v3 instructions on Model Router)\n'
    ;;

  router)
    v3_config="$(env_value BRK330_CONFIG_V3)"
    [[ -n "$v3_config" && -n "$(version_for v3)" ]] || fail 9 'Build v3 first: bash infra/11-promote.sh deploy --candidate <ID>'
    router_config="$v3_config-router"
    version="$(version_for v3-router)"
    if [[ -n "$version" ]]; then
      printf 'Reusing v3-router (contoso-travel version %s).\n' "$version"
    else
      instruction_name="$(.venv/bin/python -c 'import sys, yaml; print(yaml.safe_load(open(sys.argv[1])).get("instruction_file", "instructions.md"))' "src/agent/.agent_configs/$v3_config/metadata.yaml")"
      mkdir -p "src/agent/.agent_configs/$router_config"
      printf 'model: model-router\ninstruction_file: ../%s/%s\n' "$v3_config" "$instruction_name" \
        > "src/agent/.agent_configs/$router_config/metadata.yaml"
      instruction_file="$(cd "src/agent/.agent_configs/$router_config" && realpath "../$v3_config/$instruction_name")"
      previous_live="$(live_version)"
      deploy_new_version model-router "$router_config" "$instruction_file"
      version="$new_version"
      remember_version v3-router "$version" model-router "$router_config"
      go_live "$previous_live"
    fi
    smoke_test "$version"
    printf 'Next: bash infra/07-score.sh run --label v3-router, then bash infra/07-score.sh compare\n'
    ;;

  go-live)
    [[ -n "$label" ]] || fail 2 'Pass --label v1, v2, v2-quality, v2-alt, v3, v3-router, or v3-student.'
    version="$(version_for "$label")"
    [[ -n "$version" ]] || fail 9 "$label has not been built yet in $environment_name."
    go_live "$version"
    smoke_test "$version"
    printf 'Start a new conversation in the portal to see %s.\n' "$label"
    ;;
esac
