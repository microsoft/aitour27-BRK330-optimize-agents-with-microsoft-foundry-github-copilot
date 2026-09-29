# Source

Implementation for the Contoso Travel Concierge and its continuous-improvement workflow.

| Folder | Purpose |
|---|---|
| [`agent/`](agent/README.md) | Python 3.13 Microsoft Foundry Hosted Agent using Agent Framework, Responses, deterministic tools, and optimizer-ready configuration. |
| [`web/`](web/README.md) | Persistent FastAPI behavior surface used to replay the same scenarios against sequential agent versions. |
| [`scripts/`](scripts/README.md) | Deterministic asset generation and local validation utilities. |
| [`agent/.foundry/`](agent/.foundry/) | Versioned evaluator, dataset references, metadata, and measured evaluation result provenance. |
| [`training/`](training/) | Trace curation, reviewed-data validation, and fine-tuning workflows. |

The canonical runtime data is under [`../data/fixtures/`](../data/fixtures/README.md). Azure provisioning and validation are under [`../infra/`](../infra/README.md).
