# BRK330 planning package

This folder is the implementation source of truth for the 45-minute breakout
**Optimize agents with Microsoft Foundry & GitHub Copilot**.

## Planning assets

| File | Purpose |
|---|---|
| [`spec.md`](spec.md) | Build-ready product and technical specification |
| [`decisions-and-risks.md`](decisions-and-risks.md) | Fixed decisions, validation gates, and contingency rules |
| [`outline.md`](outline.md) | Timing-accurate five-act session outline |
| [`demo-builder.md`](demo-builder.md) | Instructions for building the demo in a new GitHub Copilot App session |
| [`execution-map.md`](execution-map.md) | Exact split between implementation work and presenter recording actions |
| [`recording-prompts.md`](recording-prompts.md) | Ordered prompts the presenter pastes into Copilot App while recording |
| [`demo-1.md`](demo-1.md) | Act 2 recording runbook: Agent Loop |
| [`demo-2.md`](demo-2.md) | Act 3 recording runbook: Model Loop |
| [`demo-3.md`](demo-3.md) | Act 4 recording runbook: Agent Optimizer |
| [`test-prompts.md`](test-prompts.md) | Fifty test prompts and the balanced 20-prompt demo subset |
| [`inventory.md`](inventory.md) | Required source, data, infrastructure, documentation, and media assets |
| [`slides.md`](slides.md) | Supplied-slide catalog with keep, hide, and revision guidance |
| [`speaker-notes.md`](speaker-notes.md) | Speaker narrative and slide-specific changes |
| [`instructor-guide.md`](instructor-guide.md) | Reproduction, delivery, troubleshooting, and optional-depth guidance |
| [`dry-run-readiness.md`](dry-run-readiness.md) | Minimum viable route to the first dry run |
| [`assets/slides/`](assets/slides/) | Original supplied slide-reference images |

## Implementation boundary

These files specify the implementation; they are not the implementation.
After approval, copy this folder to the repository root as `.plan/`, then use
`demo-builder.md` from a fresh GitHub Copilot App session.

“Implement the plan” means building, deploying, and validating the real solution
and preparing reproducible recording checkpoints. It does not mean recording the
videos or editing the PowerPoint deck.
