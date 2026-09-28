# FastAPI demo surface

Persistent demonstration UI for replaying the same scenarios against the active `contoso-travel` Hosted Agent version.

The application uses `AIProjectClient.get_openai_client(agent_name=...)` rather than constructing preview endpoint URLs. It queries the endpoint version selector so every result shows the actual active and latest versions.

## Environment

| Variable | Purpose |
|---|---|
| `FOUNDRY_PROJECT_ENDPOINT` | Foundry project endpoint. `AZURE_AI_PROJECT_ENDPOINT` is accepted as a fallback. |
| `CONTOSO_AGENT_NAME` | Hosted Agent name; defaults to `contoso-travel`. |
| `CONTOSO_FIXTURES_DIR` | Optional fixture root override for local/container use. |
| `CONTOSO_MODEL_DEPLOYMENT` | Metadata fallback when version tags are unavailable. |
| `CONTOSO_CONFIGURATION` | Configuration-name fallback. |
| `CONTOSO_INSTRUCTION_SHA` | Instruction-hash fallback. |

Authentication uses `DefaultAzureCredential`; no API keys are stored by the app.

## Local validation

```bash
pytest src/web/tests
```

A live local run requires Azure authentication and a deployed Hosted Agent. Use the repository preflight/setup workflow rather than targeting the protected prototype resource group.
