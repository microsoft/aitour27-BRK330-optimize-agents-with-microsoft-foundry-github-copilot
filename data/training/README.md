# Fine-tuning data contract

The Make it better story fine-tunes `gpt-5.4-mini` from quality-filtered v1 traces. Training data is separate from the frozen four-case evaluation dataset so evaluation remains a true holdout.

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

The target model deployment name is `contoso-student`. GPT-OSS models are excluded from this workflow.