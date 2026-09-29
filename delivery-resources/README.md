# BRK330 delivery resources

Presenter, re-delivery, and train-the-trainer materials for this session.

## Core materials

| Item | Link | Notes |
|---|---|---|
| Delivery deck | Pending public URL | Required before final publication |
| Session recording | Forthcoming | Add the reviewed hosted recording URL after production |
| Attendee landing page | [Session README](../README.md) | Public starting point |
| Attendee instructions | [Instructions](../instructions/README.md) | Complete cloud rebuild, optimization, validation, and cleanup path |

## Delivery checklist

- Review the session README
- Review the attendee instructions
- Open the deck
- Review the presenter guidance below
- Review live demo reproducibility guidance
- Validate any required environment or setup

## Session preparation

- Review the attendee entry point from the root README.
- Review the delivery deck.
- Validate the required environment and setup.

## Run of show

| Segment | Purpose |
|---|---|
| Opening and challenge — 5 min | Establish why agent quality, latency, and cost must be measured separately. |
| Make it work — 10 min | Run the travel concierge and use Insights to turn production-like traces into actionable findings. |
| Make it better — 12 min | Freeze the evaluation contract and change only the model strategy with Model Router. |
| Fine-tuning lesson — 3 min | Reference retained v3/v4 regressions to show why good data and human oversight matter. |
| Make it scale — 10 min | Run Agent Optimizer, inspect its prompt-only candidate, and stop at the administrative promotion boundary. |
| Playbook and close — 5 min | Reinforce one-lever experiments and human promote/reject/revise decisions. |

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

**Implementation status:** Complete; recordings and final PII review remain.

The canonical live path uses the scripts and measured artifacts linked from the
attendee instructions. The three edited demo targets remain 4 minutes for
Insights, 6 minutes for evaluation and Model Router, and 5 minutes for Agent
Optimizer. Cut cloud wait time; never fabricate results or force a winner.

For reset, reroute to retained v2 with `infra/switch-agent-version.py`, start a
new conversation, and verify the runtime banner before recording. For a clean
rebuild, export `BRK330_SUBSCRIPTION` and `BRK330_LOCATION`, run
`infra/teardown.sh` only with both confirmations, then run `infra/setup.sh`.

If preview access, quota, or cloud latency prevents a live segment, use the
canonical reviewed recording and narrate the measured outcome. Preserve v1-v4
and optimizer provenance; do not delete or recreate versions on stage.

## Setup notes

- Run `infra/preflight.sh` in the learner-selected subscription and region.
- Keep Model Router v2 as the Agent Optimizer baseline.
- Open a new session after endpoint routing changes.
- Review screenshots for PII before committing or publishing them.
- Complete the readiness checklist before recording and publication.

## Support

Content owner or contact: Nitya Narasimhan ([@nitya](https://github.com/nitya)) · [LinkedIn](https://linkedin.com/in/nityan)
