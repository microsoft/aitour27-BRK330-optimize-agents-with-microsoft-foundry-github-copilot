# Deterministic travel fixtures

> **How can we demo travel planning without depending on live airline, hotel, or exchange-rate APIs?** These fictional fixtures create a small, controlled travel world. The agent can search it, apply policy, reconcile receipts, and produce evidence we can inspect and repeat.

No company, employee, merchant, inventory item, policy, or receipt in this folder is real.

[![The Travel Concierge uses fixture-backed travel, receipt, tool, and policy evidence](../../instructions/img/HERO-01.png)](../../instructions/img/HERO-01.png)

## 1. Contents

| Folder | Purpose |
|---|---|
| [`catalogs/`](catalogs/) | Flight, hotel, car, airport, city, and exchange-rate inventory. |
| [`employees/`](employees/) | Fictional Caldova traveler profiles. |
| [`itineraries/`](itineraries/) | Known multi-tool itinerary examples and expected policy checks. |
| [`policy/`](policy/) | Human-readable and structured Caldova travel-policy rules. |
| [`receipts/`](receipts/) | Structured receipt truth plus generated PNG images. |

The JSON files are the source of truth. Receipt PNGs are visual versions generated from the receipt JSON, and the deployment process copies fixtures into the agent package. Those generated copies are never the source of truth.

Travel and receipt dates are fixed in the second half of 2027 so every recorded run uses the same itinerary window. Exchange rates are fixture values for repeatable calculations, not live financial rates.

## 2. Validate

From the repository root, run utility [S02](../../src/scripts/README.md):

```bash
.venv/bin/python src/scripts/validate_fixtures.py
```

The validator is read-only. It checks JSON parsing, fixed date windows, unique IDs, cross-file references, policy references, receipt arithmetic, currency conversion, and generated receipt images.

## 3. Regenerate receipt images

Use utility [S01](../../src/scripts/README.md), then validate the result with S02:

```bash
.venv/bin/python src/scripts/generate_receipts.py
.venv/bin/python src/scripts/validate_fixtures.py
```

Image generation is deterministic. Keep each PNG synchronized with its corresponding JSON file.
