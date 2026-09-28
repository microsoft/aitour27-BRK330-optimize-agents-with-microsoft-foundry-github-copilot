# Fine-tuning data contract

The Make it better story fine-tunes `gpt-4.1-mini` from quality-filtered v1 traces. Training data is separate from the frozen four-case evaluation dataset so evaluation remains a true holdout. The live Sweden Central catalog retires fine-tuning and inference for version `2025-04-14` on April 14, 2027, which covers the December 2026 delivery revisit.

## Target corpus

- At least 20 accepted training conversations and 4 validation conversations.
- OpenAI messages JSONL for training and validation artifacts.
- Coverage across compliant planning, policy refusal, multilingual receipts, accessibility constraints, and numeric reconciliation.
- Teacher responses come from baseline v1 using `gpt-5.4` and deterministic fixture tools.
- Every accepted trace passes all four hard gates and the pinned rubric threshold.
- Duplicate prompts, failed tool calls, unsupported CT claims, and inconsistent totals are excluded.

## Provenance

Keep a sidecar manifest containing source response/trace IDs, active agent version, model deployment, instruction SHA, rubric name/version, dataset hashes, curation timestamp, and accept/reject reason. Never place credentials or raw protected telemetry in committed data.

## Separation rules

- `data/evaluation/lightweight-v1/dataset-v2.jsonl` is evaluation-only and must not be copied into training.
- Training and validation examples must use distinct prompts and trace IDs.
- The v1-v4 comparison always uses the same frozen evaluation dataset and evaluator.
- The fine-tuned deployment is evaluated as agent v3 before it can be selected for Agent Optimizer.

The target model deployment name is `contoso-student`, using DeveloperTier capacity 100 for the recorded evaluation. GPT-OSS models are excluded from this workflow.

## Trace-driven workflow

The committed source is [`trace-seed-prompts.jsonl`](trace-seed-prompts.jsonl). These prompts are training-only inputs used to create production-like v1 traces; they are not training rows by themselves. The attendee-run script harvests the resulting `AppGenAIContent` records so every SFT example retains a real trace ID, timestamp, model identity, user message, and teacher response.

Raw trace content, review decisions, generated SFT files, submission logs, and job IDs remain under ignored `.azure/<environment>/training-v3/`. Do not commit those artifacts. The sanitized provenance output records hashes and trace IDs without duplicating message content.

Human review is mandatory. An accepted review row must choose `train` or `validation`, assign one contract category, record a rubric score of at least `0.5`, set every hard gate to `true`, and explain the decision. Curation fails unless it finds at least 20 training and 4 validation traces, satisfies the target category coverage, removes duplicates, and proves zero exact prompt overlap with the frozen evaluation dataset.

## Curated-response comparison

[`curated-gold-v1.jsonl`](curated-gold-v1.jsonl) defines a second 20/4 corpus using the same accepted training-only prompts and source trace lineage, but replaces the harvested final responses with manually reviewed fixture/policy-grounded gold responses. It keeps the same split, category coverage, base model, seed, epochs, instructions, and frozen evaluation as v3. This isolates response-label quality as the only v4 hill-climb lever.

The curated corpus is committed because it contains synthetic fixture data only. Generated upload files and job state remain ignored under `.azure/<environment>/training-v4/`.