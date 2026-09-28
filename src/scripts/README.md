# Repository scripts

Reproducible local utilities used to build and validate BRK330 assets.

| Script | Side effects | Purpose |
|---|---|---|
| `generate_receipts.py` | Rewrites `data/fixtures/receipts/REC-*.png` | Generate deterministic synthetic receipt images from the canonical fixture values. |
| `validate_fixtures.py` | None | Validate fixture JSON, dates, IDs, references, policy rules, totals, conversion, and images. |

Run scripts from the repository root inside the supported dev container. Use `--help` on validation or automation scripts before running them. Receipt generation has no cloud side effects and requires Pillow from the root `requirements.txt`.
