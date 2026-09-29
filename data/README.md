# Data

> **What evidence does the agent use, and how do we know a change helped?** This folder contains the fictional data used to build, evaluate, and improve the travel concierge. Nothing here represents a real person, company, merchant, policy, or transaction.

| Folder | Question it answers | Contents |
|---|---|---|
| [`fixtures/`](fixtures/README.md) | What can the agent see and act on? | Catalogs, travelers, policy, receipts, and itineraries. |
| [`evaluation/`](evaluation/) | How do we know one version is better? | Insights prompts, expected behavior, rubric criteria, and measured results. |
| [`training/`](training/README.md) | What examples teach the student model? | Reviewed traces, curated responses, provenance, and holdout checks. |

Use utility [S02](../src/scripts/README.md) to validate runtime fixtures from the repository root:

```bash
.venv/bin/python src/scripts/validate_fixtures.py
```

Generated copies under `src/agent/fixtures/` are packaging artifacts and are never the source of truth.
