#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<'EOF'
Configure the BRK330 Codespaces/dev-container workspace.

Usage: .devcontainer/post-create.sh

Validates the container toolchain, installs the Application Insights Azure CLI
extension, installs or upgrades the Microsoft Foundry agent and fine-tuning azd
extensions, creates `.venv`, and installs root `requirements.txt`. It does not
authenticate, create cloud resources, deploy, or delete anything.
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    usage
    exit 0
fi

# Run every setup step from the repository root, regardless of the caller's directory.
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

# Fail early when the dev container is missing a required command.
required_commands=(git gh node npx az azd python3)
missing_commands=()

for command_name in "${required_commands[@]}"; do
    if ! command -v "$command_name" >/dev/null 2>&1; then
        missing_commands+=("$command_name")
    fi
done

if (( ${#missing_commands[@]} > 0 )); then
    printf 'Missing required commands: %s\n' "${missing_commands[*]}" >&2
    printf 'Rebuild the dev container before retrying.\n' >&2
    exit 1
fi

# Confirm the selected development interpreter meets the repository requirement.
python3 - <<'PY'
import sys

if sys.version_info < (3, 13):
    raise SystemExit(f"Python 3.13+ is required; found {sys.version.split()[0]}")
PY

# Azure CLI uses Debian's system Python, so ensure pip is available for CLI extensions.
# Refresh only signed Debian sources to avoid failures from unrelated apt repositories.
if ! /usr/bin/python3 -m pip --version >/dev/null 2>&1; then
    sudo -n apt-get update \
        -o Dir::Etc::sourcelist=/etc/apt/sources.list.d/debian.sources \
        -o Dir::Etc::sourceparts=-
    sudo -n apt-get install -y python3-pip
fi

# Install the pinned Application Insights extension and verify Azure CLI can load it.
application_insights_extension_version='0.1.19'
installed_application_insights_version="$(az extension show --name application-insights --query version -o tsv 2>/dev/null || true)"
if [[ "$installed_application_insights_version" != "$application_insights_extension_version" ]]; then
    az extension add \
        --name application-insights \
        --version "$application_insights_extension_version" \
        --upgrade \
        --yes
fi

az extension show --name application-insights --query '{name:name,version:version,path:path}' -o json >/dev/null

# Install or upgrade the azd extensions used for Foundry agents and fine-tuning.
foundry_installed_version="$(azd ext list -o json | python3 -c 'import json,sys; print(next((item["installedVersion"] for item in json.load(sys.stdin) if item["id"] == "microsoft.foundry"), ""))')"
if [[ -n "$foundry_installed_version" ]]; then
    azd ext upgrade microsoft.foundry
else
    azd ext install microsoft.foundry
fi

finetune_installed_version="$(azd ext list -o json | python3 -c 'import json,sys; print(next((item["installedVersion"] for item in json.load(sys.stdin) if item["id"] == "azure.ai.finetune"), ""))')"
if [[ -n "$finetune_installed_version" ]]; then
    azd ext upgrade azure.ai.finetune
else
    azd ext install azure.ai.finetune
fi

azd ext list -o json | python3 -c '
import json, sys
extensions = {item["id"]: item["installedVersion"] for item in json.load(sys.stdin)}
required = ("microsoft.foundry", "azure.ai.agents", "azure.ai.finetune")
missing = [extension_id for extension_id in required if not extensions.get(extension_id)]
if missing:
    raise SystemExit(f"Foundry extension installation incomplete: {chr(44).join(missing)}")
'

# Recreate the workspace virtual environment and install its declared dependencies.
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install --requirement requirements.txt

printf '\nBRK330 development environment ready.\n'
printf 'Authenticate before cloud work: az login --use-device-code && azd auth login\n'
printf 'Start the Microsoft Learn and Foundry MCP servers from .vscode/mcp.json.\n'