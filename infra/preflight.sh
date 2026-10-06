#!/usr/bin/env bash
set -euo pipefail

# -----------------------------------------------------------------------------
usage() {
  cat <<'EOF'
Run read-only BRK330 Azure and toolchain readiness checks.

Usage: infra/preflight.sh [--subscription NAME_OR_ID] [--location REGION] [--output FILE] [--verbose]

Set BRK330_SUBSCRIPTION and BRK330_LOCATION before running. Command-line flags
override those values when supplied.

The command creates no Azure resources. It exits nonzero when a core prerequisite
is missing and records optional advanced capability findings separately. By
default it prints only READY or NOT READY; --verbose prints the redacted report.
EOF
}

subscription="${BRK330_SUBSCRIPTION:-}"
location="${BRK330_LOCATION:-}"
output=""
verbose=false

# -----------------------------------------------------------------------------
# Resolve the learner-selected Azure target; explicit flags override environment values.
while [[ $# -gt 0 ]]; do
  case "$1" in
    --subscription) subscription="$2"; shift 2 ;;
    --location) location="$2"; shift 2 ;;
    --output) output="$2"; shift 2 ;;
    --verbose) verbose=true; shift ;;
    --help|-h) usage; exit 0 ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ -z "$subscription" || -z "$location" ]]; then
  printf 'Set BRK330_SUBSCRIPTION and BRK330_LOCATION, or pass --subscription and --location.\n' >&2
  exit 2
fi

# -----------------------------------------------------------------------------
# Confirm the supported dev-container toolchain is available.
missing=()
for command_name in git gh node npx az azd python3; do
  command -v "$command_name" >/dev/null 2>&1 || missing+=("$command_name")
done
if (( ${#missing[@]} > 0 )); then
  printf 'Missing commands: %s. Rebuild the dev container.\n' "${missing[*]}" >&2
  exit 3
fi

# -----------------------------------------------------------------------------
# Verify both Azure CLI sessions and select the requested subscription locally.
az account show >/dev/null
azd auth login --check-status >/dev/null
az account set --subscription "$subscription"
subscription_id="$(az account show --query id -o tsv)"
subscription_name="$(az account show --query name -o tsv)"
principal_id="$(az ad signed-in-user show --query id -o tsv)"

# -----------------------------------------------------------------------------
# Download read-only model-catalog and quota snapshots for the selected region.
catalog_file="$(mktemp)"
usage_file="$(mktemp)"
trap 'rm -f "$catalog_file" "$usage_file"' EXIT
arm_base="https://management.azure.com/subscriptions/$subscription_id/providers/Microsoft.CognitiveServices/locations/$location"
az rest --method get --url "$arm_base/models?api-version=2025-06-01" --query value -o json > "$catalog_file"
az rest --method get --url "$arm_base/usages?api-version=2025-06-01" --query value -o json > "$usage_file"
if python3 - "$output" "$subscription_id" "$subscription_name" "$principal_id" "$location" "$catalog_file" "$usage_file" "$verbose" <<'PY'
import json
import sys
from datetime import datetime, timezone

# -----------------------------------------------------------------------------
# Load the temporary Azure catalog and quota snapshots.
with open(sys.argv[6], encoding="utf-8") as handle:
  catalog = json.load(handle)
with open(sys.argv[7], encoding="utf-8") as handle:
  usage = json.load(handle)

available = {}
for item in catalog:
  model = item.get("model", {})
  name = model.get("name")
  version = model.get("version")
  if not name or not version:
    continue
  record = {
    "version": version,
    "lifecycle_status": model.get("lifecycleStatus", "Unknown"),
    "deprecation": model.get("deprecation", {}),
    "skus": sorted(
      {
        sku.get("name", "")
        for sku in model.get("skus", [])
        if sku.get("name")
      }
    ),
    "sku_deprecation_dates": sorted(
      {
        f"{sku.get('name')}:{sku.get('deprecationDate')}"
        for sku in model.get("skus", [])
        if sku.get("name") and sku.get("deprecationDate")
      }
    ),
    "capabilities": model.get("capabilities", {}),
  }
  available.setdefault(name, {}).setdefault(version, record)

# -----------------------------------------------------------------------------
# Index quota records by Azure's stable quota name.
quota_by_name = {
  item.get("name", {}).get("value"): {
    "localized_name": item.get("name", {}).get("localizedValue"),
    "current": item.get("currentValue", 0),
    "limit": item.get("limit", 0),
    "remaining": item.get("limit", 0) - item.get("currentValue", 0),
    "unit": item.get("unit"),
  }
  for item in usage
  if item.get("name", {}).get("value")
}

# -----------------------------------------------------------------------------
# Core models must be ready before setup; advanced capabilities produce warnings.
required = {
  "gpt-5.4": {
    "version": "2026-03-05",
    "sku": "GlobalStandard",
    "quota": "OpenAI.GlobalStandard.gpt-5.4",
    "minimum_remaining": 300,
  },
  "gpt-5.4-mini": {
    "version": "2026-03-17",
    "sku": "GlobalStandard",
    "quota": "OpenAI.GlobalStandard.gpt-5.4-mini",
    "minimum_remaining": 300,
  },
  "gpt-4.1-mini": {
    "version": "2025-04-14",
    "sku": "GlobalStandard",
    "quota": "OpenAI.GlobalStandard.gpt4.1-mini",
    "minimum_remaining": 100,
  },
  "model-router": {
    "version": "2025-11-18",
    "sku": "GlobalStandard",
    "quota": "OpenAI.GlobalStandard.ModelRouter",
    "minimum_remaining": 300,
  },
  "insights-judge": {
    "catalog_name": "gpt-5.6-sol",
    "version": "2026-07-09",
    "sku": "GlobalStandard",
    "quota": "OpenAI.GlobalStandard.gpt-5.6-sol",
    "minimum_remaining": 500,
  },
}
advanced = {
  "gpt-4.1-mini-fine-tuning": {
    "catalog_name": "gpt-4.1-mini",
    "version": "2025-04-14",
    "sku": "GlobalStandard",
    "capability": "globalFineTune",
    "quota": "OpenAI.GlobalStandard.gpt4.1-mini-finetune",
    "minimum_remaining": 10,
  },
}


# -----------------------------------------------------------------------------
# Combine catalog, capability, SKU, and remaining-quota checks for one model.
def capability(name, requirement):
  catalog_name = requirement.get("catalog_name", name)
  record = available.get(catalog_name, {}).get(requirement["version"])
  capability_name = requirement.get("capability")
  capability_ready = not capability_name or (
    record and record["capabilities"].get(capability_name) == "true"
  )
  quota = quota_by_name.get(requirement["quota"])
  quota_ready = bool(
    quota and quota["remaining"] >= requirement["minimum_remaining"]
  )
  return {
    "catalog_name": catalog_name,
    "required_version": requirement["version"],
    "required_sku": requirement["sku"],
    "required_capability": capability_name,
    "catalog_available": bool(
      record
      and requirement["sku"] in record["skus"]
      and capability_ready
    ),
    "quota_name": requirement["quota"],
    "minimum_remaining_quota": requirement["minimum_remaining"],
    "quota_ready": quota_ready,
    "available": bool(record and capability_ready and quota_ready),
    "catalog": record,
    "quota": quota,
  }


# -----------------------------------------------------------------------------
# Evaluate required and optional capabilities independently.
core_models = {
  name: capability(name, requirement) for name, requirement in required.items()
}
advanced_models = {
  name: capability(name, requirement) for name, requirement in advanced.items()
}
missing = [
  name for name, status in core_models.items() if not status["available"]
]
warnings = []
for name, status in {**core_models, **advanced_models}.items():
  catalog_record = status.get("catalog") or {}
  lifecycle = catalog_record.get("lifecycle_status")
  if lifecycle and lifecycle != "GenerallyAvailable":
    warnings.append(
      f"{name} {catalog_record.get('version')} lifecycle is {lifecycle}"
    )
  if not status.get("quota_ready"):
    warnings.append(f"{name} has insufficient remaining quota")

# -----------------------------------------------------------------------------
# Build one machine-readable readiness report for recording and recovery.
report = {
  "checked_at": datetime.now(timezone.utc).isoformat(),
  "subscription_id": sys.argv[2],
  "subscription_name": sys.argv[3],
  "principal_id": sys.argv[4],
  "location": sys.argv[5],
  "core_models": core_models,
  "advanced_models": advanced_models,
  "core_ready": not missing,
  "missing_core_models": missing,
  "warnings": warnings,
  "notes": [
    "gpt-oss models are intentionally excluded from fine-tuning.",
    "Agent Optimizer preview/allow-list access must be verified in the target project.",
    "Foundry and Microsoft Learn MCP status is verified in VS Code Agent mode.",
  ],
}

# -----------------------------------------------------------------------------
# Redact account identity from console output used in recordings.
public_report = {
  **report,
  "subscription_id": "<redacted>",
  "subscription_name": "<redacted>",
  "principal_id": "<redacted>",
}
if sys.argv[8] == "true":
  print(json.dumps(public_report, indent=2))

# -----------------------------------------------------------------------------
# Write the full private report only when the learner explicitly requests a file.
if sys.argv[1]:
  with open(sys.argv[1], "w", encoding="utf-8") as handle:
    handle.write(json.dumps(report, indent=2) + "\n")
if missing:
  raise SystemExit(5)
PY
then
  printf 'Preflight: READY in %s.\n' "$location"
else
  status=$?
  printf 'Preflight: NOT READY in %s.\n' "$location" >&2
  if [[ -n "$output" && -s "$output" ]]; then
    printf 'Details: %s\n' "$output" >&2
  fi
  exit "$status"
fi
