# Quick prompt sequence

A simplified, copy-pasteable ordering of `.plan/recording-prompts.md` for use
during live build + recording. Send one prompt at a time. Wait for verification
before sending the next.

Canonical source of truth remains `.plan/recording-prompts.md` (Prompts 0–15).

## Phase 0 — Feasibility

**P0.** Run Prompt 0 from `.plan/recording-prompts.md`: verify Azure identity,
quota, models, Router, Optimizer, Insights, and RBAC using the Microsoft Foundry
skill. Don't create resources or edit files. Write me a feasibility report and
stop.

## Session 1 — Build the baseline (Demo 1)

**P1.** Load the spec: read `.plan/spec.md`, `decisions-and-risks.md`,
`inventory.md`, `test-prompts.md`, `demo-1.md`. Restate the checkpoints for
Demo 1 and stop.

**P2.** Build the baseline Contoso Travel Concierge: Python Foundry hosted agent
+ synthetic tools + FastAPI web. Use Foundry Canvas visibly. Enforce Caldova
policy as a hard gate. Stop before Azure deploy.

**P3.** Provision `rg-brk330-concierge` and deploy the hosted agent + web app to
Azure. Use Foundry Canvas **Deploy & test**. Report URLs and operation IDs after
real success.

**P4.** Run the hero prompt TP-01 with its receipt, then run the noncompliant
booking case. Show both live results.

**P5.** Run the fixed 20-prompt subset against the deployed baseline. Persist
quality/compliance/latency/tokens/cost. Give me the portal URLs.

**P6.** Prepare the Foundry Insights reveal: pick one evidence-backed finding
and give me the exact portal navigation and linked trace.

## Session 2 — Hill-climb (Demo 2)

**P7.** Read `demo-2.md`. Create/register the Caldova rubric, run it on the
20-prompt baseline, and show one representative failure with the portal URL.

**P8.** Add task decomposition + Model Router (never send the compound request
as one route). Use Foundry Canvas **Build current hosted agent**. Show the
focused diff and stop before deploy.

**P9.** Deploy the routed candidate, re-run the same 20 prompts, and give me a
baseline-vs-router comparison with separate quality, compliance, latency, and
per-call/per-request/per-trip costs.

**P10.** Curate trace-derived teacher/student training data with provenance.
Report counts and stop before training.

**P11.** Find a live-catalog training-eligible smaller model. Show eligibility
evidence. If found, start the real training job and stop.

**P12.** Check the existing training job. If done, deploy the student, re-run
the 20 prompts, and give me the three-way comparison.

## Session 3 — Automate (Demo 3)

Foundry Optimizer runs from `azd ai agent optimize` and visualizes in the
portal Optimize tab. The portal is the viewer, not a launcher.

**P13.** Read `demo-3.md` + `data/evaluation/results/comparison-tracker.md`.
Confirm Agent Optimizer readiness (agent version, dataset, custom rubric
`caldova-agent-rubric-eval`, evaluation model, trace evidence, immutable
baseline reference). Compose the exact `azd ai agent optimize` command
for P14 and give me the portal Optimize URL to watch. Don't launch.

**P14.** Kick off the real Optimizer run:

```bash
AZURE_DEV_USER_AGENT=microsoft_foundry_skill azd ai agent optimize contoso-travel \
    --dataset src/agent/tests/queries.jsonl \
    --evaluator custom.caldova-agent-rubric-eval \
    --evaluator builtin.intent_resolution \
    --evaluator builtin.task_adherence \
    --eval-model gpt-4.1 \
    --optimize-model gpt-5 \
    --max-candidates 5
```

Watch progress via `azd ai agent optimize status <id> --watch`. Do not
promote. Report run id, portal URL, candidate ids, and metric summary
when it finishes. Portal is the reviewer's dashboard; promotion happens
in P15 via `azd ai agent optimize apply` + `azd deploy` so the winning
instructions land in git before the new agent version ships.

*Portal step:* review candidates in the Foundry portal Optimize tab
(`/build/agents/contoso-travel/optimize`) and record human review.
The portal shows the score comparison chart, per-candidate `View
changes` diffs, and a `Deploy best candidate` button. Use the portal
as the **review surface only** — promote via azd so the winning
instructions round-trip back into git before the new version ships.

**P15.** After the presenter picks a candidate in the portal, promote
via the **two-step azd flow** — not `optimize deploy` directly, and
not the portal Deploy button:

```bash
# 1. Pull the candidate's optimized instructions into the local repo
azd ai agent optimize apply --candidate <candidate-id>

# 2. Review the diff on-camera — this is the demo's "human in the loop" beat
git diff src/agent/.foundry/instructions.md

# 3. Ship it as v10 through the normal azd deploy path
cd src/agent && azd deploy contoso-travel

# 4. Commit so the promoted prompt is durable alongside v6/v8/v9 history
git add src/agent/.foundry/instructions.md
git commit -m "P15: promote optimizer candidate as agent v<n>"
```

Why `apply` + `azd deploy` and **not** `optimize deploy` or the
portal button:

- `optimize deploy` and portal Deploy both create the new agent
  version **server-side from the Foundry-held draft**. The winning
  prompt never lands in git — the repo silently drifts behind
  production.
- `apply` downloads the candidate's instructions into
  `src/agent/.foundry/instructions.md` first, so the change goes
  through **normal code review** (git diff, commit, PR if you want
  one) before deploy. Then `azd deploy` publishes what's in git.
- Net effect is the same live v10 in either path, but only the
  `apply` path leaves a permanent trail: v6 baseline, v8 routed, v9
  student, v10 optimized — all reconstructible from the repo alone.

Then re-run the smoke cases and 20-prompt eval against v10. Confirm
policy blocking, quality threshold, and hard-gate pass rate still
hold. Persist the final result manifest and update
`comparison-tracker.md` with the v10 row.

## Recovery prompt

Inspect existing operation IDs from the latest checkpoint. Report which ops
succeeded/failed/in-progress. Continue only from the first incomplete
checkpoint.
