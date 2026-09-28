# Evaluation comparison scorecard

Use this scorecard for the frozen v1-v4 comparison. Quality, latency, and cost remain separate so an improvement in one does not hide a regression in another.

## Version summary

| Version | Strategy | Eval run | Quality mean | Passed | Latency P50 | Latency P95 | Input tokens | Output tokens | Total tokens | Estimated cost |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| v1 | Baseline `gpt-5.4` | `evalrun_d518cfe6064d4d51ba6be97b4c211a60` | 0.600 | 2/4 | 10.809 s | 36.499 s | 24,335 | 5,184 | 29,519 | Pending price snapshot |
| v2 | Model Router | `evalrun_8afcad0acc194c07a8948f38eed7b6e1` | 0.625 | 4/4 | 9.185 s | 65.496 s | 54,155 | 6,692 | 60,847 | Pending exact router meter |
| v3 | Fine-tuned student | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| v4 | Promoted optimizer candidate | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Pending |

## Baseline v1 details

| Case | Quality | Result | Latency | Input tokens | Output tokens | Total tokens |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| INS-01 | 0.325 | Fail | 36.499 s | 12,965 | 2,655 | 15,620 |
| INS-02 | 0.770 | Pass | 9.740 s | 2,963 | 595 | 3,558 |
| INS-03 | 0.905 | Pass | 10.809 s | 3,497 | 907 | 4,404 |
| INS-04 | 0.400 | Fail | 13.023 s | 4,910 | 1,027 | 5,937 |

P50 and P95 use Foundry's nearest-rank display convention. With four rows, P50 is the second-fastest observation and P95 is the slowest. Agent token counts come from each evaluation output item's target sample; the rubric judge used another 31,989 tokens and is evaluation overhead, not evaluated-system cost.

## Model Router v2 details

| Case | Quality | Result | Latency | Input tokens | Output tokens | Total tokens |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| INS-01 | 0.650 | Pass | 65.496 s | 31,682 | 3,285 | 34,967 |
| INS-02 | 0.570 | Pass | 8.302 s | 3,043 | 492 | 3,535 |
| INS-03 | 0.725 | Pass | 9.185 s | 3,585 | 858 | 4,443 |
| INS-04 | 0.556 | Pass | 34.366 s | 15,845 | 2,057 | 17,902 |

The v2 rubric judge used another 27,097 tokens. Compared with v1, v2 improved pass count from 2/4 to 4/4 and mean quality by `0.025`. P50 improved by `1.624 s` (15.0%), but evaluated-agent tokens increased by 31,328 (106.1%) and P95 latency increased by `28.997 s` (79.4%). The fast half became faster while the slow tail became substantially slower; these operational signals are not folded into the quality score.

## Cost method

The evaluation API does not return billed USD. Preserve a dated Azure price snapshot for each deployment before calculating cost:

$$
\text{estimated cost} = \frac{\text{input tokens}}{10^6} \times \text{input price per million} + \frac{\text{output tokens}}{10^6} \times \text{output price per million}
$$

Record the currency, region, model or router selection, input rate, output rate, and price retrieval date beside every estimate. Until those inputs are pinned, total tokens are the cost proxy and estimated cost remains pending rather than using a fabricated rate.

On 2026-09-28, the Azure Retail Prices API returned no exact `model-router` meter for Azure OpenAI in `swedencentral`. Keep the v2 USD estimate pending until the routed-model billing meter or actual Cost Management usage can be attributed to this run.
