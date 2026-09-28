# Evaluation comparison scorecard

Use this scorecard for the frozen v1-v4 comparison. Quality, latency, and cost remain separate so an improvement in one does not hide a regression in another.

## Version summary

| Version | Strategy | Eval run | Quality mean | Passed | Latency P50 | Latency P95 | Input tokens | Output tokens | Total tokens | Estimated cost |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| v1 | Baseline `gpt-5.4` | `evalrun_d518cfe6064d4d51ba6be97b4c211a60` | 0.600 | 2/4 | 11.916 s | 36.499 s | 24,335 | 5,184 | 29,519 | Pending price snapshot |
| v2 | Model Router | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| v3 | Fine-tuned student | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| v4 | Promoted optimizer candidate | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Pending |

## Baseline v1 details

| Case | Quality | Result | Latency | Input tokens | Output tokens | Total tokens |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| INS-01 | 0.325 | Fail | 36.499 s | 12,965 | 2,655 | 15,620 |
| INS-02 | 0.770 | Pass | 9.740 s | 2,963 | 595 | 3,558 |
| INS-03 | 0.905 | Pass | 10.809 s | 3,497 | 907 | 4,404 |
| INS-04 | 0.400 | Fail | 13.023 s | 4,910 | 1,027 | 5,937 |

P50 is the midpoint of the two central observations. P95 uses nearest-rank selection for this four-case holdout. Agent token counts come from each evaluation output item's target sample; the rubric judge used another 31,989 tokens and is evaluation overhead, not evaluated-system cost.

## Cost method

The evaluation API does not return billed USD. Preserve a dated Azure price snapshot for each deployment before calculating cost:

$$
\text{estimated cost} = \frac{\text{input tokens}}{10^6} \times \text{input price per million} + \frac{\text{output tokens}}{10^6} \times \text{output price per million}
$$

Record the currency, region, model or router selection, input rate, output rate, and price retrieval date beside every estimate. Until those inputs are pinned, total tokens are the cost proxy and estimated cost remains pending rather than using a fabricated rate.
