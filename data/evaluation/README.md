# Evaluation dataset

Machine-readable exports of `.plan/test-prompts.md`.

## Files

| File | Purpose |
|---|---|
| `prompts-50.jsonl` | Full 50-prompt library (EVAL-050) |
| `prompts-20.jsonl` | Fixed 20-prompt recorded subset (EVAL-020). **Do not change composition** — this set must be identical across baseline, routed, student, and optimizer comparisons. |
| `expected-behaviors-20.jsonl` | Per-prompt expected tools, policy rule citations, and outcomes for the 20-subset |
| `rubric.json` | Caldova rubric (RUB-001) with 6 dimensions and separate quality/cost/latency metrics |

Regenerate with:

```bash
python3 scripts/build_eval_dataset.py
```
