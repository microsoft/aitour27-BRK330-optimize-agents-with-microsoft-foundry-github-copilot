# Evaluation comparison scorecard

Use this scorecard for the frozen v1-v4 comparison. Quality, latency, and cost remain separate so an improvement in one does not hide a regression in another.

## Version summary

| Version | Strategy | Eval run | Quality mean | Passed | Latency P50 | Latency P95 | Input tokens | Output tokens | Total tokens | Estimated cost |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| v1 | Baseline `gpt-5.4` | `evalrun_d518cfe6064d4d51ba6be97b4c211a60` | 0.600 | 2/4 | 10.809 s | 36.499 s | 24,335 | 5,184 | 29,519 | Pending price snapshot |
| v2 | Model Router | `evalrun_8afcad0acc194c07a8948f38eed7b6e1` | 0.625 | 4/4 | 9.185 s | 65.496 s | 54,155 | 6,692 | 60,847 | Pending exact router meter |
| v3 | Fine-tuned `gpt-4.1-mini` student | `evalrun_7e5acaacf6384e26be18848e6fd68c0b` | 0.270 | 0/4 | 6.873 s | 18.736 s | 4,950 | 2,347 | 7,297 | Pending price snapshot |
| v4 | Curated-response fine-tuned student | `evalrun_31bae94024db445bb788397c3fc9aa59` | 0.334 | 1/4 | 5.016 s | 14.868 s | 4,950 | 1,274 | 6,224 | Pending price snapshot |
| v5 | Promoted optimizer candidate | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Pending |

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

Model Router uses **Balanced** routing by default, trading cost and quality per request rather than applying one fixed model strategy to every row. This run reflects that split: INS-02 and INS-03 remained fast and compact, while the harder INS-01 and INS-04 cases consumed 52,869 of 60,847 evaluated-agent tokens and drove the slower tail. Quality eligibility improved across the suite, but the extra cost proxy was concentrated in the difficult cases. The evaluation artifacts do not expose reliable routed-model attribution, so do not infer which underlying model served an individual row.

## Fine-tuned student v3 details

| Case | Quality | Result | Latency | Input tokens | Output tokens | Total tokens |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| INS-01 | 0.264 | Fail | 18.736 s | 1,237 | 658 | 1,895 |
| INS-02 | 0.370 | Fail | 6.873 s | 1,237 | 397 | 1,634 |
| INS-03 | 0.265 | Fail | 9.910 s | 1,230 | 872 | 2,102 |
| INS-04 | 0.183 | Fail | 6.061 s | 1,246 | 420 | 1,666 |

The v3 rubric judge used another 13,995 tokens. Compared with v1, v3 reduced P50 latency by `3.936 s` (36.4%), P95 by `17.763 s` (48.7%), and evaluated-agent tokens by 22,222 (75.3%). It did not retain quality: mean quality fell from `0.600` to `0.270`, every frozen row failed, and the independent smoke trace attributed CT-02 lead-time policy to CT-04.

## Curated-response student v4 details

| Case | Quality | Result | Latency | Input tokens | Output tokens | Total tokens |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| INS-01 | 0.236 | Fail | 14.868 s | 1,237 | 400 | 1,637 |
| INS-02 | 0.605 | Pass | 4.326 s | 1,237 | 237 | 1,474 |
| INS-03 | 0.160 | Fail | 8.488 s | 1,230 | 378 | 1,608 |
| INS-04 | 0.333 | Fail | 5.016 s | 1,246 | 259 | 1,505 |

The v4 rubric judge used another 12,972 tokens. Compared with trace-response v3, curated labels improved mean quality by `0.063`, raised pass count from 0/4 to 1/4, reduced P50 by `1.857 s`, P95 by `3.868 s`, and evaluated-agent tokens by 1,073. The controlled label-quality lever helped, but v4 remained below threshold on three rows and independently attributed CT-02 lead time to CT-03.

## V1-v4 selection decision

V2 is the best eligible optimizer baseline. It is the only version that passed all four frozen rows without evaluator errors and did not have the student policy-attribution hard-gate regression. V3 proves that distillation can reduce latency and token usage, while v4 proves curated labels can recover some quality and further improve efficiency. Both students are rejected because operational savings cannot compensate for failed quality and policy gates. Retain all versions unchanged, reroute to v2, and reserve v5 for an approved Agent Optimizer promotion.

## Cost method

The evaluation API does not return billed USD. Preserve a dated Azure price snapshot for each deployment before calculating cost:

$$
\text{estimated cost} = \frac{\text{input tokens}}{10^6} \times \text{input price per million} + \frac{\text{output tokens}}{10^6} \times \text{output price per million}
$$

Record the currency, region, model or router selection, input rate, output rate, and price retrieval date beside every estimate. Until those inputs are pinned, total tokens are the cost proxy and estimated cost remains pending rather than using a fabricated rate.

On 2026-09-28, the Azure Retail Prices API returned no exact `model-router` meter for Azure OpenAI in `swedencentral`. Keep the v2 USD estimate pending until the routed-model billing meter or actual Cost Management usage can be attributed to this run.
