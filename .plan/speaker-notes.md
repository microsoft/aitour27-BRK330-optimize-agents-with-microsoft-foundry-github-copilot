# Speaker notes

## Slide 5 — Build and optimize the Contoso Travel Concierge

Open with the five-act journey. Replace the old three-row language with:
Agent Loop—build and baseline; Model Loop—measure and hill-climb; Agent
Optimizer—automate repeatable experiments. Promise a reusable playbook.

## Slide 7 — Five challenges every AI team is hitting

Speak as Contoso engineers: catalog choice is growing, public benchmarks do not
represent Caldova, cost is a system concern, production needs controls, and the
landscape keeps changing. Do not dwell on generic industry commentary.

## Slide 8 — What you want

Add “compliant” to simpler, better, cheaper, and scalable. Explain that these
goals compete and require measured tradeoffs.

## Slide 9 — What you need

Emphasize continuous improvement rather than platform breadth. Build, ground,
run, govern, and improve are one lifecycle.

## Slide 10 — Continuous Improvement Agent DevOps Loop

Use this as the bridge: release is the midpoint, not the finish. The right-hand
loop produces the evidence that drives the next development change.

## Slide 11 — The Agent Loop

Set the act goal: make it work and establish what it actually does. Avoid calling
this optimization before a baseline exists.

## Slide 12 — Compliant trip planning app

Use Krystal by name. Add car rental so the task list matches the demo. Replace
Carmen and generic company language with Caldova. State that policy violations
block booking.

## Slide 13 — Starting architecture

Use the verified baseline deployment name, not an assumed model. Explain the
“Ferrari for every job” tradeoff: fast to build, expensive at scale, and not yet
measured.

## Slide 14 — The CFO math

State the unit explicitly. Separate AI operating cost from travel-policy savings.
Andre knows what Caldova spends, but not whether the concierge is economical or
preventing out-of-policy travel. Replace every figure after the dry run.

## Slide 16 — Insights in Foundry

Explain that Insights analyzes evaluated traces and links anomalies to evidence.
It identifies the opportunity; it does not perform the later optimization.
Mark preview status accurately.

## Slide 17 — Act 2 demo

Use the label “Build and baseline with GitHub Copilot.” Describe the cuts:
Copilot plan, deployed checkpoint, hero request, batch result, then Insights.

## Slide 18 — The Model Loop

Transition from “it works” to “prove it is better.” Introduce hill climbing as
controlled experiments against the same evidence.

## Slide 19 — Evaluation is the starting point

Make clear that some steps fail and are rejected. Do not depict optimization as
guaranteed monotonic quality improvement.

## Slide 21 — From response to quality score

Replace the restaurant example with Krystal's hero request. Use dimensions:
intent completeness, policy compliance, tool accuracy, itinerary correctness,
receipt accuracy, and clarity.

## Slide 22 — How it works

Hidden. Use in the instructor guide to explain rubric generation, review,
weighting, offline evaluation, production evaluation, and CI gates.

## Slide 23 — Where rubric fits

Trace answers “what happened,” evaluation answers “was it good,” analysis
answers “why,” and optimization asks “what change should we test next.”

## Slide 24 — Subjective judgment becomes measurable quality

Hidden. If used in an extended delivery, replace “looks good to me” with
Andre/Cassandra's unverified assumptions.

## Slide 25 — More than pass or fail

Show one compliant and one noncompliant travel response. Policy failure must
override a high overall average.

## Slide 26 — What to know about Rubric

Hidden. Revalidate all preview, model, regional, version, and benchmark claims
before using as a field-reference slide.

## Slide 27 — Getting started in Foundry

Hidden. Use for reproduction instructions: agent, judge model, test dataset,
roles, rubric review, evaluation, and continuous monitoring.

## Slide 28 — Rubric evaluator

Hidden as duplicate depth. Keep the useful point that domain context can seed a
rubric, but a human must review it.

## Slide 30 — ASSERT

Hidden. It is outside the focused Foundry/Copilot optimization story.

## Slide 31 — Five jobs hiding in one sentence

Replace Contoso policy with Caldova policy. Align the five jobs to the hero
request and explain why decomposition enables task-level routing.

## Slide 33 — When to fine-tune

Optional. Explain that training is justified only after prompt, context, and
routing experiments expose a stable gap. Validate any numeric threshold.

## Slides 34 and 35 — Optimization levers

Hide or simplify. Highlight only levers used in the demo; the full lists belong
in the instructor guide.

## Slide 36 — Quality improves at every stage

Replace the title with “Measure every step; improve the system overall.” Show a
strong baseline, a cheaper routed candidate with possible quality loss, improved
measurement, and a trained student that either recovers the target or is
rejected.

## Slide 37 — Act 3 demo

Use: “Define the rubric · change one lever · compare on the same evidence.”
Alternate Copilot engineering actions with stable portal outcomes.

## Slide 38 — The Agent Optimizer

Transition: the team understands hill climbing, but Lydia cannot repeat it
manually whenever the landscape changes.

## Slide 39 — The optimization loop

Walk through baseline, candidates, evaluation, ranking, recommendation, and
human review. Emphasize the final human gate.

## Slide 40 — Agent Optimizer overview

Hidden because Slides 39 and 41 cover the same message.

## Slide 41 — What it optimizes, what you provide

Use the current supported-target list. Contoso provides configuration, production
evidence, and Caldova's success criteria.

## Slide 42 — Inside an optimization run

Optional. Use only if the live portal demonstrates comparable multi-objective
results. Otherwise avoid unsupported Pareto and two-model claims.

## Slide 43 — Getting started with Agent Optimizer

Hidden. Use in instructor preparation and current-product prerequisite checks.

## Slide 44 — Promote and govern with ACS

Hidden. ACS is out of scope, and “Optimizer decides” must become “Optimizer
recommends; a human decides.”

## Slide 45 — Agent Optimizer results

Use the actual portal run and current preview label. Replace all example scores,
model names, and savings with measured results.

## Slide 46 — Act 4 demo

Use: “Generate candidates · compare evidence · review and promote the winner.”
This demo is portal-first.

## Slide 47 — Summary divider

Optional. Remove if timing is tight.

## Slide 48 — Optimization journey

Recap the three loops with final language. Tie every line to cost, quality,
changing models, GitHub Copilot, and repeatability.

## Slide 49 — Microsoft Agent Platform

Hidden. It broadens the session and includes claims that require current
validation. Retain for instructor context only.

## Slide 50 — Agent Optimization Playbook

Keep. Replace steps with: representative workload; explicit targets; measured
baseline; controlled one-lever comparison; automate and repeat.

## Slide 51 — Duplicate playbook

Hide. It duplicates Slide 50 and reintroduces ASSERT and ACS.

## Slide 52 — Next steps

Keep but simplify. Point to the session repository, current Foundry docs, and
Foundry community. Remove unverified workshops, dates, and out-of-scope projects.

## Slide 53 — Original outline

Replace with the five-act outline in `outline.md`. Preserve the abstract
verbatim. Replace broad objectives with the three measurable session outcomes.

