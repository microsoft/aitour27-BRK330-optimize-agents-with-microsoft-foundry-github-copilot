"""Contoso Travel Concierge hosted agent using the Responses protocol."""
from __future__ import annotations

import hashlib
import logging
import os

from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from agent_framework_foundry_hosting import ResponsesHostServer
from azure.ai.agentserver.optimization import OptimizationConfig, load_config
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

from tools.definitions import ALL_TOOLS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("contoso-travel")


def load_runtime_config() -> tuple[OptimizationConfig, str, str]:
    """Load the active immutable config and return it with instructions/hash."""
    config = load_config()
    if config is None:
        raise RuntimeError(
            "No optimization configuration found. Expected "
            ".agent_configs/baseline/metadata.yaml or an applied candidate."
        )
    instructions = config.compose_instructions()
    if not instructions.strip():
        raise RuntimeError("The active optimization configuration has no instructions.")
    instruction_hash = hashlib.sha256(instructions.encode("utf-8")).hexdigest()
    return config, instructions, instruction_hash


def main() -> None:
    load_dotenv()
    project_endpoint = os.getenv("FOUNDRY_PROJECT_ENDPOINT") or os.getenv(
        "AZURE_AI_PROJECT_ENDPOINT"
    )
    if not project_endpoint:
        raise RuntimeError(
            "Set FOUNDRY_PROJECT_ENDPOINT or AZURE_AI_PROJECT_ENDPOINT."
        )

    config, instructions, instruction_hash = load_runtime_config()
    model = config.model or os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME")
    if not model:
        raise RuntimeError("The active config must specify a model deployment.")

    logger.info(
        "Starting agent version=%s model=%s config_source=%s instruction_sha=%s",
        os.getenv("FOUNDRY_AGENT_VERSION", "local"),
        model,
        config.source,
        instruction_hash[:12],
    )

    client = FoundryChatClient(
        project_endpoint=project_endpoint,
        model=model,
        credential=DefaultAzureCredential(),
    )
    agent = Agent(
        client=client,
        instructions=instructions,
        tools=ALL_TOOLS,
        default_options={"store": False},
    )
    ResponsesHostServer(agent).run()


if __name__ == "__main__":
    main()
