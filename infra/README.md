# Infrastructure

> **Which script do I run next, and what will it change?** The scripts are numbered in the order you use them. Each one prints `--help`, tells you what to run next, and can be run again safely.

```text
Make it work                01 validate -> 02 setup -> 03 check
Understand where it struggles   04 run questions -> 05 insights
Make it better              06 scorecard -> 07 score v1
                            08 model router (v2)   -> 07 score v2
                            09 fine-tune (v2-alt)  -> 07 score v2-alt
Make it scale               10 optimize -> 11 promote (v3) -> 07 score v3 -> 07 compare
Clean up                    12 teardown
```

## Scripts

| Step | Script | Changes in Azure | What it does |
|---:|---|---|---|
| 01 | [`01-validate.sh`](01-validate.sh) | Nothing | Checks fixtures, the three question sets, the scorecard inputs, tests, and templates. Setup runs it for you. |
| 02 | [`02-setup.sh`](02-setup.sh) | Creates billable resources | Signs you in if needed, proposes your subscription and `eastus2`, checks quota, then builds everything: five model deployments, Hosted Agent v1, monitoring, and the portal. |
| 03 | [`03-check.sh`](03-check.sh) | Nothing (reads only) | Confirms the five models, the agent, the portal, permissions, and traces are all healthy. |
| 04 | [`04-run-questions.sh`](04-run-questions.sh) | Billable model calls | Asks one version a whole question set (default: v1, exploring set, 3 times each) so its traces are ready to study. |
| 05 | [`05-insights.sh`](05-insights.sh) | Billable analysis | Runs Agent Insights over recent traces with `insights-judge` and saves the findings. |
| 06 | [`06-scorecard.sh`](06-scorecard.sh) | Uploads datasets; billable draft | Drafts the scorecard from v1's traces, the agent, the exploring questions, and the Insights findings. Reuses it if it exists. |
| 07 | [`07-score.sh`](07-score.sh) | Billable scoring in `run`; reads only in `compare` | Scores one version on the 24 testing questions, or prints the comparison table. |
| 08 | [`08-model-router.sh`](08-model-router.sh) | New agent version; `--mode quality` also adds a model deployment | Builds v2: same instructions, Model Router picks the model (Balanced). `--mode quality` builds v2-quality on a Quality-mode router. |
| 09 | [`09-fine-tune.sh`](09-fine-tune.sh) | Billable job, model deployment, new agent version | Builds a smaller model taught from a teacher's reviewed answers: v2-alt from v1 (default), or v3-student with `--teacher-label v3`. |
| 10 | [`10-optimize.sh`](10-optimize.sh) | Billable optimizer job | Lets Agent Optimizer propose three instruction changes from the version you pick, using practice questions only. |
| 11 | [`11-promote.sh`](11-promote.sh) | New agent version; `go-live` switches the portal | Turns a reviewed candidate into v3, optionally runs v3's instructions on Model Router as v3-router (`router`), or switches the portal to the version you choose. |
| 12 | [`12-teardown.sh`](12-teardown.sh) | Deletes the environment | Asks twice, then deletes and purges the generated resource group. |

Helpers you do not run directly:

- [`_common.sh`](_common.sh) holds the shared sign-in check, safety checks, and version labels.
- [`preflight.sh`](preflight.sh) checks the region, model versions, and quota. Setup calls it.
- [`deploy-supplemental.sh`](deploy-supplemental.sh) and [`supplemental.bicep`](supplemental.bicep) add the portal and the permissions the provider does not create.
- [`switch-agent-version.py`](switch-agent-version.py) shows or changes which version the portal uses.

## Version labels

Every change creates a new, unchangeable agent version. The scripts remember which version is which in the azd environment, so you only need to remember the labels.

| Label | What changed | Built by | Model |
|---|---|---|---|
| v1 | Starting point | 02 | `gpt-5.4` |
| v2 | Model choice | 08 | `model-router` (Balanced routing) |
| v2-quality | Model choice, Quality routing | 08 `--mode quality` | `model-router-quality` (Quality routing, capacity 300) |
| v2-alt | Smaller trained model | 09 | `contoso-student` (fine-tuned `gpt-4.1-mini`) |
| v3 | Instructions, proposed by the optimizer and reviewed by you | 11 | The model of the version you optimized |
| v3-router | v3's instructions on Model Router (optional) | 11 `router` | `model-router` (Balanced) |
| v3-student | v3's instructions on a model fine-tuned from v3's answers (optional) | 09 `--teacher-label v3` | `contoso-student-v3` (fine-tuned `gpt-4.1-mini`) |

v2 and v2-alt both start from v1 and change one thing each. Only `go-live` (or `--activate`) changes what the portal uses.

## Models and capacity

Setup deploys every model the session needs, so nobody waits on a manual deployment later.

| Deployment | Model | Capacity (thousand tokens per minute) | Used for |
|---|---|---:|---|
| `gpt-5.4` | `gpt-5.4` 2026-03-05 | 300 | v1, the optimizer's reasoning |
| `gpt-5.4-mini` | `gpt-5.4-mini` 2026-03-17 | 300 | Scorecard judge |
| `gpt-4.1-mini` | `gpt-4.1-mini` 2025-04-14 | 100 | Base for fine-tuning |
| `model-router` | `model-router` 2025-11-18 | 300 | v2 |
| `insights-judge` | `gpt-5.6-sol` 2026-07-09 | 500 | Agent Insights (reads every trace in the window, so it needs headroom) |

The fine-tuned `contoso-student` is deployed by step 09 on Developer tier. Preflight refuses to start if any core model lacks the quota above.

## Getting started

```bash
bash infra/02-setup.sh
```

Press Enter to keep the proposed subscription and `eastus2`, then confirm. For automation:

```bash
bash infra/02-setup.sh --subscription "<subscription-name-or-id>" --location eastus2 --yes
```

Every later script uses the selected azd environment. Pass `--environment brk330-NNNNNN` if you work with more than one.

## Safety

- Generated environments use `rg-aitour-brk330-NNNNNN`. Every script refuses other resource groups and always refuses `rg-brk330-concierge`.
- Nothing deletes agent versions, jobs, datasets, or traces except step 12.
- Private outputs (answers, traces, review sheets, job IDs, scores) stay under the ignored `.azure/<environment>/` folder.

See [`rbac-matrix.md`](rbac-matrix.md) for who needs which role and why.
