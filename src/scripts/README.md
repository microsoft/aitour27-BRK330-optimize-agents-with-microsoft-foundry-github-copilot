# Repository scripts

Reproducible local utilities used to build and validate BRK330 assets.

| Script | Side effects | Purpose |
|---|---|---|
| `generate_receipts.py` | Rewrites `data/fixtures/receipts/REC-*.png` | Generate deterministic synthetic receipt images from the canonical fixture values. |
| `run_agent_insights.py` | Optional: starts one billable Insights analysis with `--run`; inspection mode is read-only | Inspect the retained Agent Insights monitor/run history or start one on-demand run without deleting monitor, insight, or agent state. |
| `setup_lightweight_evaluation.py` | Optional: uploads dataset v1 and starts a billable rubric-generation job with `--apply`; default mode is local-only | Validate the frozen contract, register the dataset, generate or reuse the evaluator, and save its review artifact. |
| `validate_fixtures.py` | None | Validate fixture JSON, dates, IDs, references, policy rules, totals, conversion, and images. |

Run scripts from the repository root inside the supported dev container. Use `--help` on validation or automation scripts before running them. Receipt generation has no cloud side effects and requires Pillow from the root `requirements.txt`.
