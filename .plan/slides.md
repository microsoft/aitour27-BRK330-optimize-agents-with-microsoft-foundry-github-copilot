# Slide catalog and recommendations

The primary key is the visible slide title. Numbers are only cross-references to
the supplied image names. Original images and alternate versions are retained in
[`assets/slides/`](assets/slides/).

## Setup and framing

| Slide | Visible title | Status | Canonical image | Required change |
|---:|---|---|---|---|
| 5 | Build & optimize the Contoso travel concierge | Revise and keep | [`Slide5`](assets/slides/9628e21b-0e41-4961-b672-57cb85ae96d4-Slide5.jpeg) | Use five-act labels and revised demo names from `outline.md`. |
| 7 | Five challenges every AI team is hitting | Keep | [`Slide7`](assets/slides/1cfc8b7d-c16b-40d1-9400-412c82b29fa4-Slide7.jpeg) | Tie each challenge to Contoso engineers and Caldova. |
| 8 | What you want | Keep optional | [`Slide8`](assets/slides/7be4f2a9-5446-4eb1-80d5-2fd6d6ac5a52-Slide8.jpeg) | Make “compliant” explicit; avoid implying a strict sequence. |
| 9 | What you need | Keep optional | [`Slide9`](assets/slides/95fb54bc-f064-4beb-99e3-a9217ac646b6-Slide9.jpeg) | Emphasize continuous improvement; do not over-expand platform scope. |
| 10 | The Continuous Improvement Agent DevOps Loop | Keep | [`Slide10`](assets/slides/cd7525b9-9b1b-447b-a105-f7a87a791a0c-Slide10.jpeg) | Use as bridge into the three loops. |

## Act 2: Agent Loop

| Slide | Visible title | Status | Canonical image | Required change |
|---:|---|---|---|---|
| 11 | The Agent Loop | Keep | [`Slide11`](assets/slides/9c4a4be1-ade0-4dd5-b1d1-033c466644a8-Slide11.jpeg) | Subtitle: “Make it work — Let's build.” |
| 12 | Compliant trip planning app | Revise and keep | [`Slide12`](assets/slides/3f19967d-7bcf-4c4e-b96f-7c2d657d50ce-Slide12.jpeg) | Replace employee/Carmen with Krystal; include car rental; say Caldova policy. |
| 13 | Starting architecture — everything on gpt-5.4 | Revise and keep | [`Slide13`](assets/slides/35de1098-56ad-4302-8f54-cc4ba41e64e8-Slide13.jpeg) | Replace model name with verified baseline deployment; use hosted-agent API pattern. |
| 14 | The CFO math | Revise and keep | [`Slide14`](assets/slides/ccb89c2e-4d6e-4b12-afdf-271ce06ace29-Slide14.jpeg) | Distinguish cost per request/trip/call; replace figures with measured values; explain unknown quality and avoided policy spend. |
| 16 | Insights in Foundry | Revise and keep | [`Slide16`](assets/slides/b4f6b240-ea6a-4f2a-adaf-919a22689837-Slide16.jpeg) | State that evaluated traces and preview availability are required. |
| 17 | Demo: Build with GitHub Copilot | Revise and keep | [`Slide17`](assets/slides/b43fbb93-76dc-4df4-873e-9c650f5c156e-Slide17.jpeg) | “Build and baseline with GitHub Copilot: deploy · run representative traffic · reveal gaps with Insights.” |

## Act 3: Model Loop

| Slide | Visible title | Status | Canonical image | Required change |
|---:|---|---|---|---|
| 18 | The Model Loop | Keep | [`Slide18`](assets/slides/adccbb37-d17f-4555-9dfb-c632c402dc79-Slide18.jpeg) | Subtitle: “Make it better — Let's climb.” |
| 19 | Evaluation is the starting point | Revise and keep | [`Slide19`](assets/slides/a428cace-df78-4db8-9cb6-4eeafbe2fbef-Slide19.jpeg) | Show rejected steps and separate quality/cost/latency. |
| 21 | From agent response to quality score | Revise and keep | [`Slide21`](assets/slides/0ff88fe8-06f2-4b3e-8174-31bb64781212-Slide21.jpeg) | Replace restaurant example with Krystal's travel request. |
| 22 | How it works | Hide; instructor guide | [`Slide22`](assets/slides/597d611c-32ad-40d1-aec7-35386b0a29b4-Slide22.jpeg) | Useful evaluator mechanics but redundant on stage. |
| 23 | Where Rubric fits in the Foundry lifecycle | Revise and keep | [`Slide23`](assets/slides/913e2c3c-9847-41e2-bea9-3b2ccc18e7da-Slide23.jpeg) | Use sentence case; connect directly to trace → evaluate → understand → optimize. |
| 24 | Subjective judgment becomes measurable quality | Hide; instructor guide | [`Slide24`](assets/slides/0be1083c-9822-4565-8d62-e503aa98d2bd-Slide24.jpeg) | Redundant with Slides 21 and 25. |
| 25 | More than pass or fail | Revise and keep | [`Slide25`](assets/slides/cd0514f9-0cb6-4620-bf6e-af07f2b0e808-Slide25.jpeg) | Use Caldova travel pass/fail cases and policy hard gate. |
| 26 | What to know about Rubric today | Hide; validate before guide | [`Slide26`](assets/slides/551ce738-ec77-418c-a63b-be659b898143-Slide26.jpeg) | Revalidate preview claims, versions, metrics, and regional support. |
| 27 | Getting started in Foundry | Hide; instructor guide | [`Slide27`](assets/slides/da58212c-fbcb-479d-87c6-dddbc7046c31-Slide27.jpeg) | Keep as setup reference. |
| 28 | Rubric evaluator | Hide; duplicate/depth | [`Slide28`](assets/slides/190dbfdf-0da7-44b7-8ba3-ab0dedc75f7b-Slide28.jpeg) | Fold the key idea into Slide 21. |
| 30 | ASSERT: open evaluation for any agent | Hide | [`Slide30`](assets/slides/2a97f7d7-0df3-4d57-93bc-4a95604060c3-Slide30.jpeg) | Out of focused demo scope unless explicitly restored. |
| 31 | Five jobs hiding in one sentence | Keep | [`Slide31`](assets/slides/197edffa-4ec4-4c11-a239-104a7c8ba1e2-Slide31.jpeg) | Replace “Contoso policy” with Caldova policy; align jobs to hero request. |
| 33 | When to fine-tune | Keep optional | [`Slide33`](assets/slides/99d23abc-2955-4c7e-8875-87cc1de2ba02-Slide33.jpeg) | Replace Contoso policy QA with Caldova; validate training thresholds. |
| 34 | Cost optimization levers | Hide or simplify | [`Slide34`](assets/slides/71fcb9cb-8e4c-49da-b4f1-9a81dfaa744c-Slide34.jpeg) | Highlight only decomposition, Model Router, and student model. |
| 35 | Quality optimization levers | Hide or simplify | [`Slide35`](assets/slides/68396b7e-217b-499e-b5b9-d16b7d7c6b69-Slide35.jpeg) | Highlight rubric, trace-derived data, and training. |
| 36 | Quality improves at every stage | Replace | [`Slide36`](assets/slides/15352764-01a0-423c-a49e-cf50ca65357f-Slide36.jpeg) | New title: “Measure every step; improve the system overall.” Show quality dip after routing and recovery after training. |
| 37 | Demo: Hill climb with GitHub Copilot | Revise and keep | [`Slide37`](assets/slides/cc351565-cfa3-477a-a966-c93130ad5a1b-Slide37.jpeg) | “Define the rubric · change one lever · compare on the same evidence.” |

## Act 4: Agent Optimizer

| Slide | Visible title | Status | Canonical image | Required change |
|---:|---|---|---|---|
| 38 | The Agent Optimizer | Keep | [`Slide38`](assets/slides/a1a3334f-aedc-4269-894c-2bbb7cd164b5-Slide38.jpeg) | Subtitle: “Make it easier — Let's automate.” |
| 39 | The optimization loop | Keep | [`Slide39`](assets/slides/ec4e993b-86a9-4453-a755-41f08e0091be-Slide39.jpeg) | Preserve human approval message. |
| 40 | Agent Optimizer | Hide; duplicate | [`Slide40`](assets/slides/0ce0b0fa-1602-4da7-a1a2-2353036a7be1-Slide40.jpeg) | Repeats 39 and 41. |
| 41 | What it optimizes, what you provide | Keep | [`Slide41`](assets/slides/82903195-9bda-408a-b0f1-5dd611064cb9-Slide41.jpeg) | Verify supported targets against current product. |
| 42 | Inside an optimization run | Keep optional | [`Slide42`](assets/slides/45962d5f-d432-4ea8-9cad-c97c14d6a7b8-Slide42.jpeg) | Validate Pareto and two-model claims before use. |
| 43 | Getting started with Agent Optimizer | Hide; instructor guide | [`Slide43`](assets/slides/56b205dc-e0a3-4756-8d11-9b002c21ad3f-Slide43.jpeg) | Setup reference only. |
| 44 | Promote the winner, then govern it with ACS | Hide | [`Slide44`](assets/slides/2151ad90-7e99-4be2-9cf3-a2408854cefb-Slide44.jpeg) | ACS is out of scope; “optimizer decides” conflicts with human review. |
| 45 | Agent optimizer portal results | Revise and keep | [`Slide45`](assets/slides/30048068-512f-4029-bb62-22858d095623-Slide45.jpeg) | Replace private-preview label and figures with current measured run. |
| 46 | Demo: Automate with Agent Optimizer | Revise and keep | [`Slide46`](assets/slides/a8c7d70c-f7b2-4560-95a1-865b83258ab9-Slide46.jpeg) | “Generate candidates · compare evidence · review and promote the winner.” |

## Summary

| Slide | Visible title | Status | Canonical image | Required change |
|---:|---|---|---|---|
| 47 | Summary & next steps | Optional divider | [`Slide47`](assets/slides/499be209-e996-464e-a661-e5019a5778f8-Slide47.jpeg) | Hide if timing is tight. |
| 48 | Our Agent Optimization Journey today | Revise and keep | [`Slide48`](assets/slides/fb0393a3-3ebe-4ccd-aa4d-36a30acde70b-Slide48.jpeg) | Use final loop labels and abstract-aligned takeaways. |
| 49 | Build with Microsoft Agent Platform | Hide; instructor guide | [`Slide49`](assets/slides/33ba7cb4-c08f-4845-a7d7-817ed8512ee6-Slide49.jpeg) | Broadens scope; validate “11K models.” |
| 50 | Build the system, not just the prompt | Revise and keep | [`Slide50`](assets/slides/eddd4e05-ff67-4d85-b307-9571ab3181f1-Slide50.jpeg) | Use the five-step playbook in `outline.md`. |
| 51 | Build the system, not just the prompt | Hide duplicate | [`Slide51`](assets/slides/a5112ecd-bb8d-4deb-9a83-0b4395699168-Slide51.jpeg) | Duplicate of Slide 50 with out-of-scope ASSERT/ACS. |
| 52 | Build, evaluate, govern in Foundry | Revise and keep | [`Slide52`](assets/slides/257c59e6-afd0-4d20-8d93-08a94b7ab34b-Slide52.jpeg) | Simplify to repo, current Foundry docs, and community links. |
| 53 | Original session outline | Replace | [`Slide53`](assets/slides/9e321061-71dd-4eb4-bc3d-dcd498f46c9e-Slide53.jpeg) | Replace with `outline.md`; preserve abstract verbatim. |

## Foundry Insights portal references

- [`Insights landing`](assets/slides/9b1f9b96-6feb-4466-9b68-76af8eb14af3-f0b4ef9c-3761-4ae4-a738-b92195fa2b86-clipboard.png)
- [`Incomplete monitoring role`](assets/slides/88702f7b-d136-4fde-8135-04031d0bb2fe-a9eaf6aa-aba8-446b-8da4-c55c15e7a789-clipboard.png)
- [`Scheduled analysis enabled`](assets/slides/7b080645-32d8-495d-9e70-70b063f39275-1e0072aa-bad5-4102-a3c9-3243d662d521-clipboard.png)

These are reference screenshots, not main-deck slides.
