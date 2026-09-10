# Instructor guide

## Session promise

This is an optimization session, not a travel-application architecture session.
The concierge exists to make cost, quality, compliance, drift, and iteration
concrete.

## Story ownership

- Contoso Travel builds and operates the Contoso Travel Concierge.
- Caldova uses it, pays for it, and owns the travel policy.
- Krystal represents user value.
- Andre represents cost and business value.
- Cassandra represents policy as a hard gate.
- Lydia represents integration, observability, and iteration speed.

## Delivery principles

1. Keep platform explanation subordinate to the optimization story.
2. Use one hero request across the acts so the audience can compare behavior.
3. Name the evidence set and metric units every time results are compared.
4. Never imply that evaluation improves behavior.
5. Never present a cheaper candidate as better if compliance or required quality
   falls.
6. Make human review visible before candidate promotion.

## Act 2 teaching depth

The baseline uses one strong model because it is easy to ship. The point is not
that this architecture is wrong; it is that Contoso has not measured whether it
is economically or behaviorally fit for Caldova.

Insights needs evaluated traces for the intended quality-change story. Verify:

- Application Insights is connected.
- The project managed identity has the portal-required monitoring role.
- A supported judge model is selected.
- The agent has sufficient evaluated traffic.
- The analysis window includes the prepared runs.

## Act 3 teaching depth

Hill climbing means:

1. Hold the evidence and success criteria constant.
2. Change one lever.
3. Measure quality, compliance, latency, and cost separately.
4. Keep the candidate only if it advances the stated objective without violating
   hard constraints.

Task decomposition precedes Model Router because each job has different
capability needs. A compound request routed as one unit cannot prove per-task
right-sizing.

Training is not automatically the next step. It is justified only when:

- The quality gap is stable and well measured.
- Prompt/context/tool changes have been considered.
- A supported smaller model is available.
- Teacher examples are high quality and traceable.
- The measured student result meets the gate.

## Act 4 teaching depth

Agent Optimizer applies the same discipline at scale: baseline, candidate
generation, evaluation, ranking, recommendation, and human review. It does not
remove accountability from Contoso.

## Hidden-slide guidance

- Evaluator mechanics: Slides 22, 24, 26, 27, and 28.
- Broad optimization levers: Slides 34 and 35.
- ASSERT: Slide 30, out of scope unless deliberately restored.
- Agent Optimizer details: Slides 40, 42, and 43.
- ACS governance: Slide 44, out of scope.
- Platform breadth: Slide 49.
- Duplicate playbook: Slide 51.

Use these for Q&A or extended delivery, not the 45-minute main path.

## Anticipated questions

### Why not always use the cheapest model?

Because policy compliance and task completion are hard constraints. Cost is
optimized only among candidates that meet them.

### Why not trust public benchmarks?

They do not represent Caldova's compound prompts, policy, tools, receipts, and
business priorities.

### Does the rubric replace human review?

No. Humans define and calibrate the rubric, inspect failures, and approve
promotion.

### Does Insights fix the issue?

No. It surfaces changes and supporting traces. The engineering or optimizer loop
tests fixes.

### Does Model Router decompose the request?

The demo does not assume that. The application decomposes the request and routes
each task.

### Is the trained student guaranteed to win?

No. The student is accepted only if measured results satisfy the quality and
compliance gates at the desired cost.

### Does Agent Optimizer deploy automatically?

No. The session explicitly shows human review before promotion.

## Reproduction checklist

- Azure access, quota, region, and preview availability verified.
- All model IDs and prices captured from current sources.
- RBAC applied before recording.
- Synthetic assets contain no sensitive or real customer data.
- Baseline is immutable.
- Recorded comparisons use the same 20 prompt IDs.
- Portal checkpoints and fallback media are captured.
- Slide claims match measured results.
- Full run fits the 45-minute outline.

