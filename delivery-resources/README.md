# BRK330 delivery resources

> **How do I want to deliver this session?** Choose the recorded path for the most predictable delivery, or reproduce the demos live when you have rehearsed the environment and measured your own results.

## Core materials

| Item | Link | Notes |
|---|---|---|
| Delivery deck | Avail 10.12.26  | Required before final publication |
| Session recording | Coming soon | Add the reviewed hosted recording URL after production |
| Attendee landing page | [README](../README.md) | Public starting point |
| Attendee instructions | [Instructions](../instructions/README.md) | Complete cloud rebuild, optimization, validation, and cleanup path |

## Choose a delivery path

| Path | Best for | Start here |
|---|---|---|
| **A — Reviewed recordings** | Predictable delivery with no cloud wait time. Available after recordings are published. | Open the deck, review each recording, and rehearse the transitions. |
| **B — Live reproduction** | Experienced presenters with Azure access and rehearsal time. | Follow the [`instructions/`](../instructions/README.md), then use the numbered [`infra/`](../infra/README.md) steps. |

Until Path A is published, use the sanitized screenshots and measured scorecard to rehearse the story. Do not invent a live result to match a slide.

## Delivery checklist

- [ ] Review the [session README](../README.md).
- [ ] Choose Path A or Path B.
- [ ] Open the deck and review the presenter notes below.
- [ ] If using Path A, review every recording and rehearse transitions.
- [ ] If using Path B, run the preflight and validate the environment before delivery.
- [ ] Update deck values when your measured results differ from the recorded evidence.

## Session preparation

Complete the checklist above, then rehearse the run of show. The times below total 45 minutes.

| Segment | Time | Purpose |
|---|---:|---|
| Opening and challenge | 5 min | Establish why agent quality, latency, and cost must be measured separately. |
| Make it work | 10 min | Run the travel concierge and use Insights to turn production-like traces into actionable findings. |
| Make it better | 12 min | Use a multi-dimensional rubric evaluator, then change only the model strategy with Model Router. |
| Fine-tuning lesson | 3 min | Reference retained v3/v4 regressions to show why good data and human oversight matter. |
| Make it scale | 10 min | Run Agent Optimizer, inspect its prompt-only candidate, and stop at the administrative promotion boundary. |
| Playbook and close | 5 min | Reinforce one-lever experiments and human promote/reject/revise decisions. |

## Presenter notes

- Use the root README as the attendee entry point.
- Keep the session centered on the cost and quality challenge, the travel
  concierge, the hill-climbing loop, and the repeatable optimization playbook.
- Freeze the evidence and evaluator within an experiment, change exactly one
  lever, then report quality, policy, latency, tokens, and cost separately.
- Fine-tuning is a short measured lesson, not a live training demo.
- Stop Agent Optimizer after candidate prompt review. Promotion is an optional
  post-session code reference and remains human-controlled.
- Add the public central delivery deck URL when it becomes available.

## Demo reproducibility

**Implementation status:** Core implementation, screenshots, and public evidence review are complete. Deck and recording publication are deferred.

The canonical live path uses the scripts and measured artifacts linked from the
attendee instructions. The three edited demo targets remain 4 minutes for
Insights, 6 minutes for evaluation and Model Router, and 5 minutes for Agent
Optimizer. Cut cloud wait time; never fabricate results or force a winner.

For a demo reset, reroute to retained v2, start a new conversation, and verify the runtime banner:

```bash
azd env select "$BRK330_ENVIRONMENT"
project_endpoint="$(azd env get-value FOUNDRY_PROJECT_ENDPOINT)"
.venv/bin/python infra/switch-agent-version.py \
  --version 2 \
  --project-endpoint "$project_endpoint" \
  --apply
```

For a clean rebuild, run numbered infrastructure [Step 10](../infra/README.md) only with both confirmations, then run [Step 03](../infra/README.md). Review the proposed subscription and region before confirming setup, then set `BRK330_ENVIRONMENT` to the new environment name it prints.

After recordings are published, use the reviewed recording when preview access, quota, or cloud latency prevents a live segment. Until then, use the committed sanitized screenshots and [measured scorecard](../data/evaluation/lightweight-v1/comparison-scorecard.md). Preserve v1-v4 and optimizer provenance; do not delete or recreate versions on stage.

## Setup notes

- Run numbered infrastructure [Step 03](../infra/README.md) and confirm the learner-selected subscription and region.
- Keep Model Router v2 as the Agent Optimizer baseline.
- Open a new session after endpoint routing changes.
- Complete the readiness checklist before recording and publication.

## Support

Content owner or contact: Nitya Narasimhan ([@nitya](https://github.com/nitya)) · [LinkedIn](https://linkedin.com/in/nityan)
