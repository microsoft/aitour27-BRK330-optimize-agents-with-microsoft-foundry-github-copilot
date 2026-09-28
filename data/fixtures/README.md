# Deterministic travel fixtures

Synthetic data used by the Contoso Travel Concierge. No company, employee, merchant, inventory, policy, or receipt in this folder is real.

## Contents

| Folder | Purpose |
|---|---|
| `catalogs/` | Deterministic flight, hotel, car, airport, city, and exchange-rate inventory. |
| `employees/` | Fictional Caldova traveler profiles. |
| `itineraries/` | Known multi-tool itinerary examples and expected policy checks. |
| `policy/` | Human-readable and structured Caldova travel-policy rules. |
| `receipts/` | Structured receipt truth plus generated PNG images. |

Travel and receipt dates are fixed in the second half of 2027 so recorded demos do not depend on the current date. Exchange rates are explicitly fixture values for repeatable calculations, not live financial rates.

## Validate

From the repository root:

```bash
python src/scripts/validate_fixtures.py
```

The validator is read-only. It checks JSON parsing, future dates, unique IDs, cross-file references, itinerary windows, policy references, receipt arithmetic, currency conversion, and generated receipt images.

## Regenerate receipt images

```bash
python src/scripts/generate_receipts.py
python src/scripts/validate_fixtures.py
```

Image generation is deterministic. Keep each PNG synchronized with its corresponding JSON file.
