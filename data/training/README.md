# Fine-tuning data contract

> **Can a smaller model keep the agent's quality while using fewer tokens?** We train a student on reviewed examples, test it against four cases it never saw, and keep the previous agent version when quality regresses.

| Version | One lever changed | What we learned |
|---|---|---|
| v3 | Model: `gpt-5.4` to fine-tuned `gpt-4.1-mini` | The student was faster and used fewer tokens, but quality regressed. |
| v4 | Labels: harvested responses to reviewed gold responses | Better examples helped, but did not recover enough quality. |

[![The same four-case evaluation shows the v3 regression and partial v4 recovery](../../instructions/img/FineTuning-v4-Evaluations.png)](../../instructions/img/FineTuning-v4-Evaluations.png)

Training data stays separate from the four-case evaluation set so the student is tested on prompts it did not see during training. Check current model support and lifecycle details in [`docs/technology-status.md`](../../docs/technology-status.md) before reproducing this optional experiment.

## Target corpus

- At least 20 accepted training conversations and 4 validation conversations.
- OpenAI messages JSONL for training and validation artifacts.
- Coverage across compliant planning, policy refusal, multilingual receipts, accessibility constraints, and numeric reconciliation.
- Teacher responses come from baseline v1 using `gpt-5.4` and deterministic fixture tools.
- Every accepted trace passes all four hard gates and the pinned rubric threshold.
- Duplicate prompts, failed tool calls, unsupported CT claims, and inconsistent totals are excluded.

## Provenance: where did each example come from?

The ignored private sidecar keeps source response IDs, trace IDs, job IDs, timestamps, and raw review state. Committed provenance keeps hashes, synthetic row IDs, model and instruction configuration, category coverage, and accept/reject decisions. Never commit credentials, tenant identifiers, raw protected telemetry, or cloud trace identifiers.

## Separation rules

- `data/evaluation/lightweight-v1/dataset-v2.jsonl` is evaluation-only and must not be copied into training.
- Training and validation examples must use distinct prompts and trace IDs.
- The v1-v4 comparison always uses the same four-case dataset and multi-dimensional rubric evaluator.
- The fine-tuned deployment is evaluated as agent v3 before it can be selected for Agent Optimizer.

The target model deployment name is `contoso-student`, using DeveloperTier capacity 100 for the recorded evaluation. GPT-OSS models are excluded from this workflow.

## Trace-driven workflow

The committed source is [`trace-seed-prompts.jsonl`](trace-seed-prompts.jsonl). These prompts are training-only inputs used to create production-like v1 traces; they are not training rows by themselves. The attendee-run script harvests the resulting `AppGenAIContent` records so the private review workspace can connect each example to its source trace, model, user message, and teacher response.

Raw trace content, detailed review state, generated SFT files, submission logs, and job IDs remain under ignored `.azure/<environment>/training-v3/`. Do not commit those artifacts. Committed provenance records hashes and synthetic row identifiers without publishing cloud trace or response IDs.

Human review is mandatory. An accepted review row must choose `train` or `validation`, assign one category, record a rubric score of at least `0.5`, set every hard check to `true`, and explain the decision. Curation stops unless it finds at least 20 training and 4 validation traces, covers the target categories, removes duplicates, and proves zero exact prompt overlap with the four-case evaluation dataset.

## Curated-response comparison

[`curated-gold-v1.jsonl`](curated-gold-v1.jsonl) defines a second 20/4 corpus using the same accepted training-only prompts and source lineage, but replaces the harvested final responses with manually reviewed, fixture-backed gold responses. It keeps the same split, category coverage, base model, seed, epochs, instructions, and four-case evaluation as v3. Only response-label quality changes, so we can tell whether better examples helped.

The curated corpus is committed because it contains synthetic fixture data only. Generated upload files and job state remain ignored under `.azure/<environment>/training-v4/`.