# Local utilities

> **Need to prepare or inspect one artifact without running the full demo?** These small utilities handle focused jobs such as validating fixtures, running Insights, exporting evaluation results, and cleaning files for publication.

| Ref | Script | What it does | What it changes |
|---:|---|---|---|
| S01 | [`generate_receipts.py`](generate_receipts.py) | Builds deterministic synthetic receipt images from canonical fixture values. | Rewrites `data/fixtures/receipts/REC-*.png`. |
| S02 | [`validate_fixtures.py`](validate_fixtures.py) | Checks fixture JSON, dates, IDs, references, policy rules, totals, conversions, and images. | Nothing; this is read-only. |
| S03 | [`run_agent_insights.py`](run_agent_insights.py) | Shows retained Insights history or starts one on-demand analysis with `--run`. | Inspection is read-only; `--run` starts a billable cloud analysis. |
| S04 | [`setup_lightweight_evaluation.py`](setup_lightweight_evaluation.py) | Checks the evaluation dataset and rubric, then optionally registers them with Foundry. | Default mode is local-only; `--apply` uploads dataset v2 and starts a billable rubric-generation job. |
| S05 | [`export_evaluation_run.py`](export_evaluation_run.py) | Downloads one reviewed evaluation run and its row-level evidence. | Writes raw environment-specific JSON that must remain private until reviewed. |
| S06 | [`sanitize_evaluation_artifacts.py`](sanitize_evaluation_artifacts.py) | Removes creator, resource, response, session, and trace identifiers from selected exports. | Rewrites only the JSON files explicitly passed with `--apply`. |

> **Publishing evaluation evidence?** Run S05 to export it, inspect the raw files privately, then run S06 before publication. Never publish an untouched S05 export.

Run these tools from the repository root only when the main [`instructions/`](../../instructions/README.md) point to them. The `S01` through `S06` labels are handles, not a required sequence. Use `--help` before running an automation command. Receipt generation requires Pillow from the root [`requirements.txt`](../../requirements.txt).
