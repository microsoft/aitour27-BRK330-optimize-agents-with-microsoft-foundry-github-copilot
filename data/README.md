# Data

Synthetic, deterministic inputs and measured evidence for the BRK330 continuous-improvement demos. Nothing in this folder represents a real company, employee, merchant, policy, or transaction.

| Folder | Stage | Purpose |
|---|---|---|
| [`fixtures/`](fixtures/README.md) | Build | Canonical catalogs, traveler profiles, itineraries, policy, receipts, and generated images used by the Hosted Agent. |
| [`evaluation/`](evaluation/) | Observe/evaluate | Demo 1 Insights seed prompts and expected evidence. Sprint 05 adds the frozen comparison contract and canonical results. |
| `training/` | Optimize | Added in Sprint 05 for trace-derived distillation data and provenance. |

Validate runtime fixtures from the repository root:

```bash
python src/scripts/validate_fixtures.py
```

Generated copies under `src/agent/fixtures/` are packaging artifacts and are never the source of truth.
