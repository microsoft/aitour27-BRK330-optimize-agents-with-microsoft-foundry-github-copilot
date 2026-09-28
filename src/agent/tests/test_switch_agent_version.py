from __future__ import annotations

import importlib.util
from pathlib import Path

from azure.ai.projects.models import AgentVersionStatus


SCRIPT = Path(__file__).resolve().parents[3] / "infra" / "switch-agent-version.py"
SPEC = importlib.util.spec_from_file_location("switch_agent_version", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_status_value_normalizes_sdk_enum_and_string() -> None:
    assert MODULE.status_value(AgentVersionStatus.ACTIVE) == "active"
    assert MODULE.status_value("active") == "active"