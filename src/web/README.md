# Travel Concierge demo app

> **How can I see whether an agent change helped the user?**
>
> The Travel Concierge portal replays the same requests against the active `contoso-travel` Hosted Agent and makes its decisions, tool evidence, version, latency, and token usage visible.

| On screen | What it tells you |
|---|---|
| Runtime banner | Active agent version, model, and configuration. |
| Decision banner | Whether the request was approved, blocked, or missing policy evidence. |
| Tool timeline | Which deterministic tools ran and what they returned. |
| Metadata | Response ID, latency, and token usage. |

The application uses `AIProjectClient.get_openai_client(agent_name=...)` rather than constructing preview endpoint URLs. It queries the endpoint version selector so every result shows the actual active and latest versions.

After changing endpoint routing, refresh the page and start a new request. The `/api/health` endpoint resolves the current active version so the runtime banner and result metadata show what the user actually reached.

## 1. Environment

| Variable | Purpose |
|---|---|
| `FOUNDRY_PROJECT_ENDPOINT` | Foundry project endpoint. `AZURE_AI_PROJECT_ENDPOINT` is accepted as a fallback. |
| `CONTOSO_AGENT_NAME` | Hosted Agent name; defaults to `contoso-travel`. |
| `CONTOSO_FIXTURES_DIR` | Optional fixture root override for local/container use. |
| `CONTOSO_MODEL_DEPLOYMENT` | Metadata fallback when version tags are unavailable. |
| `CONTOSO_CONFIGURATION` | Configuration-name fallback. |
| `CONTOSO_INSTRUCTION_SHA` | Instruction-hash fallback. |

Authentication uses `DefaultAzureCredential`; no API keys are stored by the app.

## 2. Local validation

```bash
.venv/bin/python -m pytest src/web/tests
```

A live run requires Azure authentication and a deployed Hosted Agent. Speakers should follow the main [`instructions/`](../../instructions/README.md) and numbered [`infra/`](../../infra/README.md) workflow rather than running this app directly or targeting the protected prototype resource group.
