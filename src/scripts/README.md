# Local utilities

> **What do the numbered scripts call under the hood?** You rarely run these directly. Each one prints `--help`.

| Script | What it does | What it changes |
|---|---|---|
| [`questions.py`](questions.py) | Checks the three question sets: sizes, levels, practice rows, no shared questions, test-only scenarios, and portal prompts. | Nothing. |
| [`run_questions.py`](run_questions.py) | Asks one agent version a question set (step 04 and step 09). | Billable calls; saves answers and timings under `.azure/<environment>/questions/`. |
| [`run_agent_insights.py`](run_agent_insights.py) | Shows Insights history, or starts a run with `--run`; `--save` writes findings without IDs (step 05). | `--run` starts a billable analysis. |
| [`build_scorecard.py`](build_scorecard.py) | Local check by default. `--apply` uploads the question sets and drafts the scorecard from traces (step 06). | `--apply` creates datasets and an evaluator. |
| [`compare_scores.py`](compare_scores.py) | Builds the comparison table from recorded scoring runs (step 07 `compare`). | Nothing in Azure; writes a private summary. |
| [`validate_fixtures.py`](validate_fixtures.py) | Checks fixture IDs, dates, references, policy rules, totals, and images. | Nothing. |
| [`generate_receipts.py`](generate_receipts.py) | Rebuilds the synthetic receipt images from fixture values. | Rewrites `data/fixtures/receipts/REC-*.png`. |

Run them from the repository root with `.venv/bin/python`.
