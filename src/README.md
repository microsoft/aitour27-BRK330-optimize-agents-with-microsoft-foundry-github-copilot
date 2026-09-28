# Source

Implementation for the Contoso Travel Concierge and its continuous-improvement workflow.

| Folder | Purpose |
|---|---|
| [`agent/`](agent/README.md) | Python 3.13 Microsoft Foundry Hosted Agent using Agent Framework, Responses, deterministic tools, and optimizer-ready configuration. |
| [`web/`](web/README.md) | Persistent FastAPI behavior surface used to replay the same scenarios against sequential agent versions. |
| [`scripts/`](scripts/README.md) | Deterministic asset generation and local validation utilities. |
| `evaluation/` | Added in Sprint 05 for baseline/comparison runners and result provenance. |
| `training/` | Added in Sprint 05 for trace curation and fine-tuning workflows. |

The canonical runtime data is under [`../data/fixtures/`](../data/fixtures/README.md). Azure provisioning and validation are under [`../infra/`](../infra/README.md).
