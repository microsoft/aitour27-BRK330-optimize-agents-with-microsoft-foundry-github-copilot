# Source

Implementation for the Contoso Travel Concierge and its continuous-improvement workflow.

> This folder contains implementation internals. Speakers and attendees should run the documented workflow from [`../instructions/`](../instructions/README.md) using the numbered steps under [`../infra/`](../infra/README.md), rather than invoking source files directly.

| Folder | Purpose |
|---|---|
| [`agent/`](agent/README.md) | Python 3.13 Microsoft Foundry Hosted Agent using Agent Framework, Responses, deterministic tools, and optimizer-ready configuration. |
| [`web/`](web/README.md) | Persistent FastAPI behavior surface used to replay the same scenarios against sequential agent versions. |
| [`scripts/`](scripts/README.md) | Question runner, scorecard builder, score comparison, Insights runner, and fixture checks used by the numbered steps. |
| [`training/`](training/) | Turns reviewed v1 answers into fine-tuning files (step 09). |
| [`../data/fixtures/`](../data/fixtures/README.md) | Canonical runtime catalogs, traveler profiles, policy, receipts, and itineraries. |
| [`../infra/`](../infra/README.md) | Numbered Azure provisioning, validation, optimization, routing, and cleanup workflow. |
