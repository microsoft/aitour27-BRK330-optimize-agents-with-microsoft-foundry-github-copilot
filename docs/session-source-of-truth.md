# BRK330 session source of truth

This is the working source of truth for delivering BRK330. It is based on:

- `AITour27-BRK330.pdf`, especially the outline, demo transitions after slides 15, 29, and 35, and the closing principles.
- [Ship agents faster with expanded model choice, voice agents, and continuous optimization](https://azure.microsoft.com/en-us/blog/ship-agents-faster-with-expanded-model-choice-voice-agents-and-continuous-optimization/), especially "Turn production evidence into continuous improvement."

## The story

Caldova has one travel concierge and three people who define success:

- **Krystal, the traveler:** useful, policy-compliant travel help.
- **Andre, the CFO:** quality he can defend, at a cost and speed he can live with.
- **Lydia, the architect:** an improvement process that keeps up as models and requirements change.

The session follows four acts:

| Act | Question | What we do | Product moments |
|---|---|---|---|
| 1. Make it work | Can we ship it? | Build and deploy the concierge on one frontier model (`gpt-5.4`). This is **v1**. | GitHub Copilot, Foundry skills, Hosted Agents |
| 2. Understand where it struggles | Where does it go wrong, and why? | Ask v1 the exploring questions several times, read the traces, and let Insights group the patterns. | Traces, Agent Insights |
| 3. Make it better | Is a change actually better? | Turn the traces into a scorecard. Score v1 on testing questions it has never seen. Change one thing at a time: Model Router (**v2**) or a fine-tuned smaller model (**v2-alt**). Keep what helps. | Evaluations, Model Router, fine-tuning |
| 4. Make it scale | Can we keep improving without doing it all by hand? | Let Agent Optimizer propose instruction changes from the best version. A person reviews them, retests the one they trust (**v3**) on the testing questions, and decides whether it goes live. | Agent Optimizer |

"Scale" means scaling the improvement process, not traffic.

Underneath all four acts is one loop: **observe → understand → measure → change one thing → retest → decide → repeat**. Production is where improvement starts, not where it ends.

## Rules that keep the comparison fair

1. **Separate the questions.** Exploring questions are for learning, training questions are for teaching, and testing questions are for grading. They never share a question, and the testing set uses scenarios (cities, receipts) that appear nowhere else. [`src/scripts/questions.py`](../src/scripts/questions.py) enforces this.
2. **Build the scorecard from evidence.** The scorecard is drafted from v1's own traces, the agent, the exploring questions, and the Insights findings, then reviewed by a person. It is not hand-written in advance.
3. **Use the same test for every version.** Same 24 testing questions, same scorecard version, same judge (`gpt-5.4-mini`), same pass threshold (0.5). If any of these change, rescore every version.
4. **Ask more than once.** Questions run three times in steps 04 and 07, so one noisy answer does not decide anything.
5. **Change one thing per version.** v2 changes only the model. v2-alt changes only the model, to a smaller one trained on reviewed v1 answers. v3 changes only the instructions.
6. **Report quality, speed, and cost separately.** A faster or cheaper version is only better if it keeps the policy decisions right.
7. **A person decides.** Nothing goes live without a human choosing it with `bash infra/11-promote.sh go-live`.

## Demo 1: Make it work, and see where it struggles

**After slide 15.**

- GitHub Copilot, with Foundry skills and the Microsoft Learn MCP server, builds, deploys, and tests the hosted concierge.
- One frontier model serves every job.
- The four portal scenarios show what v1 does well and where it falls short:
  - **BLOCK** is refused with a CT-11 citation.
  - **EVIDENCE** converts the receipt correctly.
  - **HERO** plans a good trip but may not book it, and the portal honestly says "Not booked."
  - **ACCESS** finds the accessible hotel and car but no flight fits the time window.
- Steps 04 and 05 turn many runs into traces and Insights findings. In earlier runs, Insights found two patterns: v1 treated "nothing was blocked" as proof of compliance, and it presented incomplete results as facts. Exact wording varies between runs, so report what your run shows.

## Demo 2: Make it better

**After slide 29.**

- Show the scorecard drafted from v1's traces (step 06). Read the dimensions aloud; they should sound like Caldova's needs, not generic quality.
- Show v1's score on the testing questions (step 07).
- Live lever: **v2, Model Router**. Same instructions; the router picks a model per request.
- Reference lever: **v2-alt, fine-tuned student**. A smaller model trained on reviewed v1 answers to the training questions. Run it before the session; show the result.
- Compare with `bash infra/07-score.sh compare`. Keep the version that keeps policy decisions right at an acceptable speed and cost. Keeping v1 is a valid outcome.

## Demo 3: Make it scale

**After slide 35.**

- Run Agent Optimizer from the chosen version. It practices on the 12 practice questions only, never the testing set.
- Show the three candidates and what each one changed.
- A person reads the candidates, picks one, and turns it into v3 (step 11 `deploy`).
- Retest v3 on the testing questions (step 07). Only then decide whether it goes live.

The optimizer's own practice scores are hints for review, not results. The only comparable numbers come from step 07.

## Delivery

- All three demos have prerecorded voice-over videos. Presenters can play them or mute them and narrate live.
- Each runbook includes a transcript, timecoded beats, expected duration, and transition cues.
- Insights wording, routing choices, scores, training results, and optimizer candidates vary between runs. Report what you measured; never force a canonical outcome.
- Edit out idle cloud time, but never fake continuity or results.
- Target edited lengths: Demo 1 four minutes, Demo 2 six minutes, Demo 3 five minutes.

## Copilot recording prompt

Use GitHub Copilot Agent mode in VS Code from a clean checkpoint, with the Microsoft Learn MCP server enabled. Copilot must pause before creating, deploying, or deleting cloud resources.

```text
Build the "Make it work" checkpoint for BRK330.

Read the repository's Demo 1 brief, architecture guidance, fixture
documentation, and acceptance criteria before changing files. Use the
Microsoft Learn MCP server to verify all Microsoft Foundry SDK, CLI,
hosting, tracing, and deployment choices against current official
documentation.

Follow the current Microsoft Foundry hosted-agent golden path:
- Python 3.13
- Responses protocol
- Agent Framework
- Azure Developer CLI with the microsoft.foundry extension
- Microsoft Foundry hosted agent named contoso-travel
- a FastAPI web experience that calls the hosted agent
- built-in trace instrumentation connected to Application Insights

Build only the baseline "Make it work" experience:
- one verified frontier model for all tasks
- deterministic Caldova travel fixtures and tools
- travel policy enforced as a hard gate
- the Krystal hero request and one noncompliant request
- one external, version-controlled agent instruction source
- reproducible setup and teardown using a new randomly named resource
   group: rg-aitour-brk330-<number>

Never access or modify rg-brk330-concierge.

First inspect the repository, verify the applicable Foundry quickstarts,
propose the implementation plan and expected files, and stop for review.
Do not provision, deploy, delete, or modify Azure resources until I
explicitly approve that checkpoint.
```

## Session objectives

By the end of the breakout, attendees can:

- Build, deploy, and observe a Microsoft Foundry hosted agent using GitHub Copilot.
- Define what good looks like from real traces and measure versions fairly across quality, speed, and cost.
- Run and automate an improvement loop across models and instructions, with a person deciding what goes live.

## Attendee path

The self-paced path needs Microsoft Foundry in an Azure subscription. There is no local mock.

- **Core:** steps 01–07 and 12. Build v1, study it, score it, clean up.
- **Further:** steps 08–11. Model Router, fine-tuning, and Agent Optimizer, when your subscription, quota, time, and budget allow.

### Prerequisites

- Azure subscription with billing, and permission to create a resource group, deploy resources, and assign roles.
- `eastus2`, or another region that has every model in [`infra/README.md`](../infra/README.md#models-and-capacity) with enough quota. Preflight checks this.
- The dev container (it includes `az`, `azd`, the Foundry extensions, and Python).
- GitHub Copilot and the Microsoft Learn MCP server, to rebuild the recorded Copilot workflow.
- Agent Optimizer preview access in the target project.
- A commitment to run step 12 when finished.

### Safety

- Setup creates a new `rg-aitour-brk330-<number>` resource group; teardown deletes only that group, after two confirmations.
- No script touches `rg-brk330-concierge`.
- Private outputs (answers, traces, review sheets, job IDs, scores) stay under the ignored `.azure/<environment>/` folder. Do not commit them.

## Repository principles

- `data/` holds `fixtures/`, `questions/`, and two small guidance files.
- The numbered scripts in `infra/` are the single workflow. Everything they call lives in `src/`.
- `src/agent/fixtures/` is generated during packaging and never tracked.
- Attendee guidance lives in `instructions/`, reference material in `docs/`, presenter material in `delivery-resources/`.
- Follow the latest Microsoft Foundry quickstarts for SDKs, tooling, deployment, evaluation, optimization, tracing, and cleanup.

## Remaining delivery work

- Run the full flow end to end in `eastus2` and record the three demo segments.
- Review every screenshot for personal information before committing it.
- Add the public deck and recording URLs when available.
- Run the final publication checklist and remove template-only tooling last.
