# BRK330 delivery resources

> **How do I want to deliver this session?** Choose the recorded path for the most predictable delivery, or reproduce the demos live when you have rehearsed the environment and measured your own results.

## Core materials

| Item | Link | Notes |
|---|---|---|
| Delivery deck | Avail 10.12.26  | Required before final publication |
| Session recording | Coming soon | Add the reviewed hosted recording URL after production |
| Attendee landing page | [README](../README.md) | Public starting point |
| Attendee instructions | [Instructions](../instructions/README.md) | Step-by-step guide for the four acts, from setup to cleanup |

## Choose a delivery path

| Path | Best for | Start here |
|---|---|---|
| **A — Reviewed recordings** | Predictable delivery with no cloud wait time. Available after recordings are published. | Open the deck, review each recording, and rehearse the transitions. |
| **B — Live reproduction** | Experienced presenters with Azure access and rehearsal time. | Follow [`instructions/README.md`](../instructions/README.md), which walks through the numbered [`infra/`](../infra/README.md) steps. |

Until Path A is published, rehearse with your own measured results. Do not invent a live result to match a slide.

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
| Opening and challenge | 5 min | Why quality, speed, and cost have to be measured separately. |
| Make it work | 7 min | Build and deploy v1 with GitHub Copilot and Foundry skills; run the four portal scenarios. |
| Understand where it struggles | 6 min | Show traces from repeated questions and the Insights findings. |
| Make it better | 14 min | Show the scorecard drafted from traces, v1's score on testing questions, then v2 (Model Router) and v2-alt (fine-tuned) side by side. |
| Make it scale | 9 min | Run Agent Optimizer from the chosen version, review candidates, retest v3, decide. |
| Playbook and close | 4 min | One change at a time, the same test every time, a person decides. |

## Presenter notes

- Use the root README as the attendee entry point.
- Keep the session centered on the cost and quality challenge, the travel
  concierge, and the four acts: make it work, understand where it struggles,
  make it better, make it scale.
- Use the same test for every version: the same 24 testing questions, the same
  scorecard, the same judge. Change one thing per version, then report quality,
  speed, and tokens separately.
- Fine-tuning (v2-alt) runs before the session. Show the result, not the job.
- The optimizer practices on practice questions only. Its scores are hints; the
  real comparison is step 07 on the testing questions.
- Nothing goes live until a person runs `bash infra/11-promote.sh go-live`. Keeping v1 is a
  valid outcome.
- Add the public central delivery deck URL when it becomes available.

## Demo reproducibility

**Implementation status:** The refreshed flow (three question sets, trace-based scorecard, v2 and v2-alt, optimizer from the chosen version) is ready for its first full run in `eastus2`. Screenshots, deck, and recordings will be refreshed from that run.

The three edited demo targets remain 4 minutes for make it work and Insights,
6 minutes for the scorecard and the two levers, and 5 minutes for Agent
Optimizer. Cut cloud wait time; never fabricate results or force a winner.

For a demo reset, switch the portal back to the version you want and start a new conversation:

```bash
bash infra/11-promote.sh go-live --label v1
```

For a clean rebuild, run [step 12](../infra/README.md) (it asks twice), then [step 02](../infra/README.md). Review the proposed subscription and `eastus2` before confirming.

After recordings are published, use the reviewed recording when preview access, quota, or cloud latency prevents a live segment. Do not delete or recreate versions on stage.

## Setup notes

- Run steps 01 to 09 the day before. They create v1, v2, v2-alt, traces, Insights findings, the scorecard, and scores.
- Submit the optimizer (step 10) before the session so candidates are ready to review on stage.
- Start a new portal conversation after switching versions.
- Complete the readiness checklist before recording and publication.

## Support

Content owner or contact: Nitya Narasimhan ([@nitya](https://github.com/nitya)) · [LinkedIn](https://linkedin.com/in/nityan)
