# Data

> **What does the agent see, and what do we ask it?** Everything here is fictional. Nothing represents a real person, company, merchant, policy, or transaction.

| Path | What it is |
|---|---|
| [`fixtures/`](fixtures/README.md) | The world the agent works in: travelers, policy, flights, hotels, receipts, and itineraries. |
| [`questions/exploring.jsonl`](questions/exploring.jsonl) | 36 questions for studying v1. Their traces feed Insights and the scorecard draft. |
| [`questions/training.jsonl`](questions/training.jsonl) | 48 questions for collecting v1 answers to teach the smaller model. |
| [`questions/testing.jsonl`](questions/testing.jsonl) | 24 questions kept aside to score every version the same way. |
| [`scorecard-guidance.json`](scorecard-guidance.json) | What we tell Foundry matters when it drafts the scorecard. |
| [`fine-tuning-review.json`](fine-tuning-review.json) | The bar a v1 answer must clear before we teach it. |

## Three question sets, three jobs

Using the same questions to learn from and to grade with makes any version look better than it is. So each set has one job, and the sets never share a question.

| Set | Size | Easy / medium / hard | Used by | Never used for |
|---|---:|---|---|---|
| Exploring | 36 | 12 / 12 / 12 | Steps 04, 05, 06, and the optimizer's practice (step 10) | Scoring versions |
| Training | 48 | Five categories, 40 train + 8 validation | Step 09 | Scoring versions |
| Testing | 24 | 8 / 8 / 8 | Step 07 | Learning, drafting, or training |

### Exploring

The first 12 rows (`"practice": true`, four per level) are the practice questions. The optimizer only sees these. They include the four portal scenarios word for word:

| Row | Portal scenario | What a good answer does |
|---|---|---|
| `BLOCK-01` | Blocked request | Refuses a blanket "approve everything" request, cites CT-11, and points to the normal approval path. |
| `EVIDENCE-01` | Receipt | Reads the parking receipt `REC-002`, converts EUR 117.00 to USD 126.36 at 1.08, and cites the rules. |
| `HERO-01` | Compliant Paris trip | Checks policy first, plans flights, hotel, and car that reconcile, and passes the policy result to the dry-run booking. |
| `ACCESS-01` | Accessible Montreal trip | Finds the wheelchair-accessible hotel and hand-control car, and says plainly that no flight fits the time window. |

The other 24 rows cover the same kinds of requests with different travelers, cities, and receipts.

### Training

Each row has a `category` and a `split`. The review sheet in step 09 is pre-filled from these, so you only judge the answer.

| Category | Rows |
|---|---:|
| `compliant_planning` | 14 |
| `refusal` | 8 |
| `receipts` | 8 |
| `accessibility` | 10 |
| `numbers` | 8 |

### Testing

The testing set uses scenarios that appear nowhere else: Toronto, Chicago, San Francisco, Madrid, Zurich, Tokyo, and receipts `REC-003` and `REC-004`. A version can only do well here by handling new situations, not by remembering familiar ones. [`src/scripts/questions.py`](../src/scripts/questions.py) checks these rules every time `infra/01-validate.sh` runs.

## Fixtures

Generated copies under `src/agent/fixtures/` are packaging output and never the source of truth. Validate the originals with:

```bash
.venv/bin/python src/scripts/validate_fixtures.py
```
