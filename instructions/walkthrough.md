# Walkthrough: what a real run looked like

This page follows [README.md](README.md) step by step and records what happened in a full run on **October 6, 2026** in **East US 2**. Run the command in the README, then come here to compare your results and pick up talking points.

Your numbers and wording will differ. Agents, Insights, and judges vary from run to run. Use this page to tell whether your run is *in the right shape*, not to match it exactly.

> Each step has three parts: **What we saw**, **What it means**, and **Talk about it**, which gives you lines you can use on stage.

## Summary at a glance

### What we did

| Act | Step | What we did | Result | Status |
|---|---|---|---|---|
| **1. Make it work** | 1–2 | Setup in East US 2, then a health check | 5 models, v1 (`gpt-5.4`), and the portal deployed; check READY | ✅ |
| | Portal | Ran the 4 sample scenarios | BLOCK refused (CT-11); EVIDENCE reimbursable; HERO **not booked**; ACCESS **partly done** | ✅ |
| **2. Understand where it struggles** | 3 | 36 exploring questions × 3 on v1 | 108 of 108 answered. Hard questions used about 2.7× the tokens and 5× the tool calls of easy ones | ✅ |
| | 4 | 🔍 **Insights** | **6 findings.** Top one: "nothing blocked treated as approval" (45 traces) | ✅ |
| **3. Make it better** | 5 | 📏 **Rubric Evaluator** scorecard built from traces | 8 dimensions. Every one except `general_quality` maps to a finding or to our guidance | ✅ |
| | 6 | Scored v1 on 24 testing questions × 3 | **0.63 mean, 82% pass.** Weakest: booking evidence (2.0/5) | ✅ |
| | 7 | 🔀 **Model Router** (Balanced) = v2 | 0.57, 65% pass. About **65% cheaper**; same quality on easy, worse on hard | ✅ ▼ |
| | 7b | Model Router (Quality) = v2-quality | 0.50, 54% pass. 100% `gpt-5.6-sol`, about **2× v1's cost**, P95 49.5 s | ✅ ▼ |
| | 8 | Fine-tuning (v2-alt) | **Skipped on purpose:** v1's answers weren't good enough to teach from | ⏭️ |
| **4. Make it scale** | 10 | ⚙️ **Agent Optimizer** from v1 | 3 candidates. Candidate 1: 0.56 → 0.62 on practice questions | ✅ |
| | 10 | Reviewed and deployed candidate 1 as v3 | Fixed 4 of 6 findings plus the duplicate heading; missed 2 policy rules | ✅ |
| | 10 | Scored v3 on the testing questions | **0.64 mean (+0.01), 75% pass.** Faster (P95 14.4 s), weaker policy checking | ✅ ↔ |
| | 9 | Compared all versions | v1 stays live through Act 3 | ✅ |
| | 11b | v3's instructions on Model Router = v3-router | **0.54, 65% pass.** Hard 0.43, the lowest of any version; most tokens per answer (8,371) | ✅ ▼ |
| | 11c | Fine-tuning from v3 (v3-student) | **Stopped at review:** only about 25 of the 30 training answers needed passed. Most failures traced back to four gaps in our tools and data | ✅ ⏸️ |
| | 11d | Fix the tools = v3-tools | **0.66 mean, 82% pass, hard 0.70.** First version to beat v1; policy decisions held. **Now live** | ✅ ▲ |
| | 11e | Fine-tuning from v3-tools (v3-tools-student) | Review passed (36 training, 6 validation; 41 with tool calls). Training job submitted | ⏳ |
| | — | Second Insights scan on v3 | Planned | ⏳ |

### Final scorecard

Same 24 testing questions, same scorecard, same judge, three rounds for every version.

| | v1 | v2 | v2-quality | v3 | v3-router | **v3-tools** |
|---|---:|---:|---:|---:|---:|---:|
| Mean | 0.63 | 0.57 | 0.50 | 0.64 | 0.54 | **0.66** |
| Pass rate | **82%** | 65% | 54% | 75% | 65% | **82%** |
| Hard | 0.63 | 0.45 | 0.46 | 0.58 | 0.43 | **0.70** |
| P95 | 18.9 s | 25.0 s | 49.5 s | **14.4 s** | 29.3 s | 15.1 s |
| Cost per answer | ≈ $0.019 | **≈ $0.007** | ≈ $0.040 | ≈ +21% vs. v1 at list price; may be lower with caching | not measured; 8,371 tokens per answer | not measured; 7,288 tokens per answer on `gpt-5.4` (+52% vs. v1) |

### The climb, step by step

Every step we tried, in the order we tried it. The **solid line** is each version's mean score on the testing questions. The **flat line** is the best version so far, the one that would be live. It never goes down: a step down costs us a few hours, not our users.

```mermaid
xychart-beta
    title "Hill climbing: mean score on the 24 testing questions"
    x-axis ["v1 start", "v2 cheap router", "v2-quality pricey router", "v3 optimizer", "v3-router stacked", "v3-tools fixed tools"]
    y-axis "Mean score (0-1)" 0.45 --> 0.70
    line [0.63, 0.57, 0.50, 0.64, 0.54, 0.66]
    line [0.63, 0.63, 0.63, 0.64, 0.64, 0.66]
```

| Step | Mean | Hard | What happened | What it taught us |
|---|---:|---:|---|---|
| **v1**, start | 0.63 | 0.63 | `gpt-5.4` with the original instructions. Insights found 6 patterns; the top one, "nothing blocked treated as approval", ran through 45 traces. | Where we stand, and where to look. |
| **v2**, cheaper model ▼ | 0.57 | 0.45 | Model Router (Balanced) sent 77% of calls to a small model. About 65% cheaper, same quality on easy questions. | Cheap is safe for easy requests, not hard ones. |
| **v2-quality**, pricier model ▼ | 0.50 | 0.46 | Quality routing sent every call to the most expensive model. Twice v1's cost, the lowest score. | More expensive isn't better. The weakness followed us across three models, so it wasn't the model. |
| **v3**, new instructions ↔ | 0.64 | 0.58 | Agent Optimizer rewrote the instructions. +0.064 on practice questions, +0.01 on new ones; faster, better evidence, weaker policy checks. | Never grade on what you practiced on. Instructions helped, but not enough. |
| **v3-router**, combine two levers ▼ | 0.54 | 0.43 | v3's instructions on Model Router. Below both v3 and v2. In one trace the tool returned the right hotel twice and the model said it failed. | Good steps don't automatically stack. Change the model, and you climb again. |
| **v3-tools**, fix the tools ▲ | **0.66** | **0.70** | Reviewing v3's answers for fine-tuning showed it working around four tool and data bugs. We fixed only the tools. | The first step up. Traces found what no score pointed at. |

The same climb as a map: which version each step started from.

```mermaid
flowchart LR
    v1["v1 · 0.63<br/>start"]
    v2["v2 · 0.57<br/>cheaper model ▼"]
    v2q["v2-quality · 0.50<br/>pricier model ▼"]
    v3["v3 · 0.64<br/>optimized instructions ↔"]
    v3r["v3-router · 0.54<br/>instructions + router ▼"]
    v3t["v3-tools · 0.66<br/>fixed tools ▲ live"]
    v1 -- "Model Router" --> v2
    v1 -- "Quality routing" --> v2q
    v1 -- "Agent Optimizer" --> v3
    v3 -- "Model Router" --> v3r
    v3 -- "trace review: tool bugs" --> v3t
    classDef up fill:#d4edda,stroke:#2e7d32,color:#1b5e20
    classDef down fill:#f8d7da,stroke:#c62828,color:#7f1d1d
    classDef side fill:#fff3cd,stroke:#b8860b,color:#5c4400
    classDef start fill:#e3f2fd,stroke:#1565c0,color:#0d3c78
    class v1 start
    class v2,v2q,v3r down
    class v3 side
    class v3t up
```

**Talk about it:**

- "This is what hill climbing really looks like. Down, down, sideways, down, then up. If you only remember one picture from today, make it this one."
- "Look at the flat line. The live version never got worse, because every step was measured before anyone switched it on. Walking down cost us an afternoon, not our users."
- "Each step down pointed to the next step. The models ruled out the model. The optimizer fixed the instructions it could. The traces found our tools. Then we went up."

### Key insights for hill climbing

1. **Measure before you move.** Every version got the same 24 testing questions, the same scorecard, and the same judge, three times. Without that, v2's cheaper bill or v3's practice gain could have gone live on a good-looking answer.
2. **One change per step tells you *why*.** Model Router changed only the model; the optimizer changed only the instructions. Because the weakest area stayed at about 2/5 across three different models, we knew the problem **wasn't the model**. Round 2 showed the rest of the answer: part of it was the instructions, and part was **our tools**.
3. **A step down is still progress.** v2 and v2-quality both went down, and they told us where not to go. The scorecard caught three would-be regressions.
4. **Cheaper and faster only count if quality holds.** Model Router cut cost by about 65% but fell on hard requests. Optimizer candidate 2 got leaner by skipping booking evidence. The same rule caught both.
5. **More expensive isn't better.** The priciest option, all `gpt-5.6-sol`, scored worst. A stronger general model doesn't mean better results for *your* agent's job.
6. **Tokens aren't cost.** Price per token depends on the model, and on caching. v2 used more tokens and cost less. v3 sent more input but made fewer calls and wrote less output.
7. **Never grade on what you practiced on.** The optimizer scored +0.064 on practice questions and +0.01 on new ones. It had copied practice questions into its examples, and only the separate testing set exposed that.
8. **Run it more than once.** The same version varied by up to 7 passes between rounds (v2-quality: 16, 9, 14). One round can fool you.
9. **The order of levers matters.** Fix what the evidence says is broken first (instructions), then pull the cost lever (router or fine-tuning). A student model is only as good as its teacher.
10. **Automation proposes, people decide.** The optimizer found the easy, mechanical wins. A person still had to spot the overfitting, the missing policy rules, and the time-window gap, and decide to keep v1.
11. **Good steps don't automatically stack.** v3's instructions were tuned on `gpt-5.4`. On Model Router they scored *below* both v3 and v2. Every time you change the model, climb again.
12. **Traces show you what scores can't.** In v3-router, the hotel search returned the right hotel twice, and the agent said the tool had failed. In the fine-tuning review, the teacher kept working around our own tool bugs. The scorecard said *how much*; the traces said *why*.
13. **Review what you teach.** Fine-tuning copies the teacher's habits, workarounds included. The review step stopped us from training a student to search for flights to `PAR` (our data only knew `CDG`) and to give up on simple totals.

**One-line takeaway:** *"Five steps down or sideways, then one clearly up, and every step told us where to climb next: first the instructions, then the tools."*

---

---

## Act 1: Make it work

### Step 1. Build everything

`bash infra/02-setup.sh` completed all 12 stages on the first try in a fresh environment. It deployed all five models (`gpt-5.4`, `gpt-5.4-mini`, `gpt-4.1-mini`, `model-router`, `insights-judge`), Hosted Agent v1, and the portal.

### Step 2. Check that everything is healthy

`bash infra/03-check.sh` reported `Deployment validation: READY`. Setup also recorded the v1 label:

```text
BRK330_VERSION_V1=1
BRK330_MODEL_V1="gpt-5.4"
BRK330_CONFIG_V1="baseline"
```

### During the session: the four portal scenarios

| Scenario | Banner we saw | Matches the README? |
|---|---|---|
| **BLOCK** | 🔴 Not approved — blocked by Caldova policy | ✅ Cited CT-11, pointed to CT-10, nothing booked. |
| **EVIDENCE** | 🟢 Reimbursable — receipt meets Caldova policy | ✅ REC-002 lines read correctly; CT-20 and CT-22 cited. |
| **HERO** | 🟠 Not booked — the booking step did not go through | ✅ Flight, hotel, and car were correct (FL-001 $940, HT-001 $921, CR-001 $42). The booking was refused for "requiring more explicit compliance evidence." |
| **ACCESS** | 🟠 Partly done — nothing matched some of the requirements | ✅ Found HT-010 ($213) and CR-008 ($44); said no flight leaves after 8:00. |

[![BLOCK](img/BLOCK-01.png)](img/BLOCK-01.png)
[![EVIDENCE](img/EVIDENCE-01.png)](img/EVIDENCE-01.png)
[![HERO](img/HERO-01.png)](img/HERO-01.png)
[![ACCESS](img/ACCESS-01.png)](img/ACCESS-01.png)

**What it means:** v1 is good at *finding* options. The cracks show when policy is involved:

- **HERO:** every policy check came back "allowed" with *no rule cited*, and v1 treated that as approval. The booking step then refused it, and the reply only mentions this at step 7.
- **ACCESS:** v1 listed "Check Caldova policy before making any recommendation" as a task, but the tool timeline shows it never called `check_travel_policy`.
- **Every answer:** "Understood tasks" appears twice. It's a small instruction quirk, worth watching in Act 4.

**Talk about it:**

- "Look at the banner, then the reply. The banner comes from what the tools returned; the reply is what the agent *says*. When they disagree, that's where we look."
- "HERO looks like a great answer until you read the booking result. That gap is what we're here to measure."

---

## Act 2: Understand where it struggles

### Step 3. Ask v1 the exploring questions, three times each

**Quick test first** (`--limit 4 --repeats 1`): all four answered, in about 15–20 seconds each.

| Question | Outcome | Was it a good answer? |
|---|---|---|
| BLOCK-01 | blocked | ✅ |
| E-01 (Paris hotels under the cap) | blocked | ✅ Checked all 4 hotels; 2 blocked under CT-03. |
| E-02 (Seattle ↔ Boston flights) | unconfirmed | ⚠️ Only searched Seattle → Boston and missed the return flight FL-009, even though the question said "between." |
| E-03 (REC-001 receipt) | reimbursable | ✅ |

**Full run** (108 answers): **108 answered, 0 errors**, in about 43 minutes one at a time.

| Level | Typical (P50) | Slowest (P95) | Avg tokens | Avg tool calls | Outcomes |
|---|---:|---:|---:|---:|---|
| Easy | 14.8 s | 19.3 s | 2,900 | 1.2 | unconfirmed 16, partial 8, blocked 6, reimbursable 6 |
| Medium | 19.1 s | 24.0 s | 5,016 | 2.5 | checked 18, reimbursable 6, partial 4, booked 3, blocked 3, unconfirmed 2 |
| Hard | 24.6 s | 42.3 s | 7,938 | 6.3 | blocked 16, partial 8, not booked 5, booked 4, reimbursable 3 |

**What it means:**

- **Cost grows fast with difficulty.** Hard questions used about **2.7× the tokens** and **5× the tool calls** of easy ones, and the slowest answers took over 40 seconds.
- **Policy is often skipped.** 16 of 36 easy answers were "unconfirmed," meaning no policy or receipt check ran. Some are plain lookups, but it's a pattern.
- **Bookings are fragile.** 5 of 9 attempted bookings on hard questions didn't go through.
- **Gaps are common.** 20 answers came back "partly done" because a search returned nothing. The question is whether v1 *said so*.

**Talk about it:**

- "Same question, three times. We want to know what the agent *usually* does, not what it did once."
- "Every hard question costs almost three times as much as an easy one. Does every question really need the frontier model? Hold that thought for Model Router."
- "Even an easy question tripped it up: 'flights *between* Seattle and Boston' got one direction only."

### Step 4. Let Insights read the traces

> 🔍 **Spotlight: Insights**

**First attempt failed** with `TooManyRequests`: the judge stayed rate-limited after retries. About 108 long traces were too much for `insights-judge` at capacity 200. We raised it to **500**, which setup now uses by default, and the second scan succeeded.

**Six findings:**

| Severity | Traces | Finding | In plain words |
|---|---:|---|---|
| High | 45 | Absence of a policy block was misinterpreted as affirmative authorization | "Nothing was blocked" was treated as "approved." |
| High | 23 | Policy validation is handled ad hoc instead of as an enforced orchestration stage | Policy checks happen sometimes, not every time. |
| Medium | 11 | Required receipt-line reimbursement classification was omitted | Receipt answers skip saying which lines are reimbursable. |
| Medium | 5 | Agent fabricates missing trip parameters to complete tool calls | It fills in missing details instead of asking. |
| Medium | 4 | Agent invents identifier prerequisites for city-level inventory searches | It asks for IDs it doesn't need before searching a city. |
| Medium | 2 | Dry-run submission used synthesized prose instead of policy-tool evidence | It sent its own write-up to the booking step instead of the policy result. |

**Example from the top finding:**

> "The `check_travel_policy` call for HT-005 returned `hard_gate_blocked=false` but also returned no decisions and no `cited_rule_ids`."

Insights also explained the pattern: v1 treats "no denial returned" as "approved" instead of reporting the result as inconclusive.

**What it means:**

- The two high findings cover **68 traces**. v1's main weakness isn't finding options; it's **treating policy as optional**.
- The HERO and ACCESS screenshots from Act 1 are single examples of the top two findings. Insights shows they aren't flukes.
- The sixth finding explains *why* HERO wasn't booked: v1 sent prose to the booking tool instead of the policy result.

**Talk about it:**

- "We saw HERO fail once in the portal. Insights says the same root cause shows up in 45 traces. That's the difference between an anecdote and a pattern."
- "Notice the wording: 'absence of a block was misinterpreted as authorization.' That's a policy-reasoning bug, not a model-quality bug, and that changes which fix we'd try."
- "Insights doesn't just name the problem; it suggests a fix. We'll come back to that when Agent Optimizer proposes instruction changes."

---

## Act 3: Make it better

### Step 5. Build the scorecard with Rubric Evaluator

> 📏 **Spotlight: Rubric Evaluator**

`bash infra/06-scorecard.sh` uploaded `brk330-exploring` and `brk330-testing`, then generated **`brk330-travel-scorecard` v1** from v1's traces, the v1 agent, the exploring questions, and our guidance plus the six Insights findings.

**The dimensions it drafted** (pass threshold 0.5):

| Dimension | Weight | Comes from |
|---|---:|---|
| `policy_gated_outcome` | 10 | Finding: "absence of a block … authorization" |
| `policy_check_before_recommendation` | 5 | Finding: "policy validation is ad hoc" |
| `evidence_preservation` | 6 | Our guidance: "numbers add up" and "honest evidence" |
| `receipt_classification_and_conversion` | 6 | Finding: "receipt-line classification omitted" |
| `missing_input_clarification` | 5 | Finding: "fabricates missing trip parameters" |
| `structured_booking_evidence` | 4 | Finding: "dry-run used prose instead of policy evidence" |
| `tool_usage_matches_request_type` | 4 | Finding: "invents identifier prerequisites" |
| `general_quality` | 5 | Built-in catch-all |

[![Rubric Evaluator: brk330-travel-scorecard with 8 weighted dimensions](img/SCORECARD-01.png)](img/SCORECARD-01.png)

**How to read this page in Foundry** (**Evaluations → Evaluators → Caldova Travel Scorecard**):

- **Evaluation type: Rubric-based.** This is the Rubric Evaluator, not a generic quality metric.
- **Dimension score range 1–5, overall 0–1.** The judge scores each dimension from 1 to 5, then the weighted result becomes one score from 0 to 1. An answer passes at 0.5.
- **Only relevant dimensions count.** A receipt question isn't marked down on `structured_booking_evidence`. Only `general_quality` is marked **Always applicable**.
- **The weight bars show priorities at a glance.** `policy_gated_outcome` (10) is twice any other dimension.
- **Target agent: contoso-travel.** The rubric is tied to this agent and its tools.
- **The description says the scorecard was "reviewed by a person and locked before any version is scored."** That line comes from our guidance. Make it true: read the dimensions before step 6, because after that the rubric doesn't change.

#### About the "input-quality" warning

The evaluator page shows:

> Generated with input-quality warnings. The agent has no instructions. The generated rubric may be generic or miss agent-specific evaluation criteria.

**This is expected, and you don't need to do anything.**

- **Why it appears:** Rubric Evaluator can read a *prompt* agent's instructions directly. A *hosted* agent's instructions are packaged inside its code, so Foundry sees only the agent's description and tools.
- **Why it doesn't matter here:** `infra/06-scorecard.sh` passes the full v1 instructions and the Caldova policy in the prompt source, along with the traces, the questions, and the Insights findings. The result is clearly not generic: `policy_gated_outcome`, `structured_booking_evidence`, `receipt_classification_and_conversion`, and `missing_input_clarification` are all specific to Caldova.
- **Don't regenerate to clear it.** A new version changes the rubric, and every version scored so far would have to be scored again.

More detail is in [troubleshooting](../docs/troubleshooting.md#generated-rubric-says-the-hosted-agent-has-no-instructions).

**What it means:**

- **Every Insights finding became a dimension.** The rubric measures exactly what we saw go wrong.
- **The traces beat our guesses.** Our guidance suggested six generic dimensions. Rubric Evaluator kept the policy focus but replaced "finishes the job" and "clear answer" with specific behaviors from the traces, such as asking for missing inputs and using the right search.
- **Policy dominates:** the three policy dimensions (`policy_gated_outcome`, `policy_check_before_recommendation`, `structured_booking_evidence`) carry 19 of 45 points, about 42%.

**Talk about it:**

- "Insights told us what goes wrong. Rubric Evaluator turned that into how we measure it. Each dimension has a finding behind it."
- "We didn't write this rubric by hand. We gave it guidance, and it changed it based on what v1 actually did. That's the point of building it from traces."
- "From now on this rubric doesn't change. Every version gets the same 24 testing questions, the same rubric, and the same judge."
- "Point at the top bar: the right policy outcome counts twice as much as anything else. That's Caldova's priority, and Insights told us it's where v1 fails most."
- "A receipt question isn't judged on bookings. Each answer is scored only on what applies to it, which keeps the comparison fair across easy and hard questions."
- If someone asks about the warning: "Foundry warns it couldn't read the agent's instructions, because hosted agents keep them in code. We handed them over directly, and you can see the result: every dimension is about Caldova's policy, not generic helpfulness."

### Step 6. Score v1

> 📏 **Spotlight: Rubric Evaluator** (now grading)

`bash infra/07-score.sh run --label v1` ran the 24 testing questions against v1 and graded each answer with `brk330-travel-scorecard`. We ran one round, then `bash infra/07-score.sh run --label v1 --repeats 2` for two more.

| Round | Passed | P50 | P95 | Agent tokens (24 answers) | Judge tokens | Duration |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 20 / 24 (83%) | 10.6 s | 18.9 s | 107,932 | 114,933 | 5 m 20 s |
| 2 | 21 / 24 (88%) | 10.5 s | 29.0 s | 128,158 | 119,832 | 7 m 17 s |
| 3 | 18 / 24 (75%) | | | | | 6 m 12 s |
| **v1 overall** | **59 / 72 (82%)** | | | | | |

Fill in round 3's latency and tokens from Foundry if you need them per round. The combined row below covers all three.

**Combined v1 row** from `bash infra/07-score.sh compare`:

| Version | Rows scored | Mean score | Pass rate | Easy | Medium | Hard | Weakest area | P50 s | P95 s | Avg agent tokens |
|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| v1 | 72 | 0.63 | 82% | 0.66 | 0.60 | 0.63 | `structured_booking_evidence` (2.0 / 5) | 10.6 | 18.9 | 4,801 |

This is **where we stand on the hill**. Every later version is compared to this row.

[![Evaluation run for v1 baseline in Foundry](img/EVALUATION-01-baseline.png)](img/EVALUATION-01-baseline.png)

**Where to find it:** Foundry → **Evaluations**, then open a `brk330-v1-…` run. The summary shows the pass rate, latency, and tokens. The row view shows each testing question with its score and the judge's reasoning for every dimension.

#### Reading the Evaluations list in Foundry

| Column | What it means |
|---|---|
| **Name** | The run name from step 07: label, start time, round (for example `brk330-v1-…-r2`). |
| **Target** | The agent and version that answered, for example `contoso-travel: 1`. |
| **Status** | In progress, Completed, or Failed. |
| **P50 / P95 latency** | Typical and slow-end answer time across the 24 answers. |
| **Target tokens** | Total tokens **the agent** used for all 24 answers. Divide by 24 for a per-answer figure. |
| **Overall score** | Share of answers that passed every evaluator in the run. We use one evaluator, so it matches the next column. |
| **brk330-travel-scorecard** | Pass rate on our Rubric Evaluator: answers scoring 0.5 or higher. |
| **Dataset** | The questions used: `brk330-testing` v1. |
| **Created on / Duration** | Start time in your local time zone, and how long answering plus grading took. |
| **Evaluation tokens** | Tokens **the judge** used to grade. That's the cost of scoring, not of the agent. |

#### What the numbers mean

| Metric | What it is | How to read it |
|---|---|---|
| **Score** | The Rubric Evaluator's weighted result for one answer, from 0 to 1. The judge (`gpt-5.4-mini`) scores each relevant dimension from 1 to 5, then the weights combine them. | Higher is better. **Mean score** is the average across all answers. **Pass rate** is the share of answers at 0.5 or above. Check the **weakest dimension** too: a good average can hide a policy problem. |
| **P50 latency** | The *typical* answer time. Half the answers were faster than this, half slower. | What most users feel. |
| **P95 latency** | The *slow-end* answer time. 95% of answers were faster than this; the slowest 1 in 20 took longer. | What your unhappiest users feel. A version can improve P50 and still get worse at P95. |
| **Tokens** | Words-in plus words-out for the agent's model calls on one answer, counting tool results it read and the reply it wrote. | A measure of how much work the model did. It is **not** the same as cost; see below. |

#### Tokens are not the same as cost

Cost is **tokens × price per token**, and price depends on the model. That matters in hill climbing because the two steps we try in Act 3 change the model, not just the work.

| Version | Tokens per answer | Model | Price per token | Cost per answer |
|---|---|---|---|---|
| v1 | Fewer | One frontier model for everything | High | Can be the **highest** |
| v2 (Model Router) | Can be more | Router sends easy requests to cheaper models | Mixed, often lower | Can be **lower**, even with more tokens |
| v2-alt (fine-tuned) | Similar or more | Smaller, cheaper model | Low | Usually **lowest**, if quality holds |

So a step that **adds** tokens can still **save** money, and a step that cuts tokens can cost more if it moves to a pricier model. Only compare tokens directly when both versions use the same model. To compare cost, multiply tokens by each model's price, or check actual spend in Azure Cost Management.

**What it means:**

- **v1 passes most testing questions.** 59 of 72 across three rounds (82%). It's a solid starting point, not a broken agent.
- **Same version, same questions, different results.** 20, 21, then 18: up to 3 answers flipped between rounds, a 13-point swing. This is why one round isn't the score, and why every version gets the same number of rounds.
- **P50 is steady; P95 isn't.** The typical time barely moved (10.5 vs. 10.6 s), but the slow end jumped from 19 to 29 s. One or two slow answers drive P95.
- **Tokens vary with the answer path.** Round 2 used about 19% more agent tokens than round 1, with no change in version, just different tool paths and longer answers.
- **Grading costs about as much as answering.** Judge tokens (about 115–120k per round) are close to agent tokens. Budget for it when you score many versions.
- **The failures are the interesting part.** Open them in Foundry and check which dimension pulled them under 0.5.
- **The weakest area is exactly what Insights predicted.** `structured_booking_evidence` averaged **2.0 out of 5**: when v1 books, it sends its own write-up instead of the policy result. That's the Insights finding "dry-run submission used synthesized prose instead of policy-tool evidence," and it's why HERO wasn't booked in the portal. Insights found it, Rubric Evaluator measured it, and now we have a number to beat.
- **A high pass rate can hide a thin margin.** 82% passed, but the mean score is only 0.63. Many answers clear the 0.5 bar by a little, so a small regression could flip them.
- **Difficulty doesn't predict quality here.** Easy 0.66, medium 0.60, hard 0.63. v1 slips on easy questions too, like the one-direction flight search we saw in step 3. Its problem is policy reasoning, not hard tasks.
- **The combined P95 (18.9 s) is lower than round 2's 29.0 s in Foundry.** The table works out P95 across all 72 answers together, while Foundry reports each round on its own. Compare versions using the combined table.

**Talk about it:**

- "About eighty percent across three rounds. That's where we stand on the hill. Now every change has to beat this, on these questions, with this scorecard."
- "Same agent, same questions: 20, 21, 18. If we'd run once, we might have fooled ourselves. Three rounds tell us a difference is real."
- "Look at the weakest area: booking evidence, 2 out of 5. Insights told us about it, the rubric measured it, and now it's the number to beat."
- "Look at P95, not just P50. A version that's fast on average but slow one time in twenty still frustrates people."
- "Tokens tell you how hard the model worked, not what it cost. When Model Router sends an easy question to a cheaper model, we might spend *more* tokens and *less* money. That's why we track them separately."

### Step 7. Build and score v2 with Model Router

> 🔀 **Spotlight: Model Router**

`bash infra/08-model-router.sh` deployed **contoso-travel version 2** in about a minute: same code, tools, and instructions, with the model changed to `model-router`. It's recorded as label v2, and the portal stays on v1.

**First look: one question, both versions** ("For employee EMP-001, state the applicable booking lead-time policy and cite the rule ID."):

| | v1 (`gpt-5.4`) | v2 (Model Router) |
|---|---|---|
| What it did | Called `check_travel_policy` with only the employee | Called `check_travel_policy` with a lead-time test (booking 0 days ahead) |
| Answer | "The tool returned no rule ID, so I can't cite one," then offered to retry with trip details | **CT-02**: book at least 7 days before departure, unless a disruption exception applies |
| Time | 7.5 s | 13.5 s |
| "Understood tasks" printed twice | Yes | Yes |

**What it means:**

- v2 framed the tool call so the policy tool *returned* the rule. That's a sign the router chose a model that reasons through tool use well for this question.
- v1 was honest rather than wrong: it didn't claim compliance it couldn't prove. That's the behavior the top Insights finding says v1 *usually* misses.
- v2 was slower on this one question. One answer proves nothing, which is why scoring uses 72.
- The duplicate heading appears in both versions, so it comes from the **instructions**, not the model. Changing the model won't fix it; changing the instructions in Act 4 can.

**Talk about it:**

- "Same instructions, same tools. The only change is who picks the model. On this question, v2 found a way to make the tool give it the answer."
- "Notice both versions print 'Understood tasks' twice. That's a clue: some problems are about the model, some are about the instructions. Hill climbing lets us change one at a time and see which is which."

#### Scoring v2

`bash infra/07-score.sh run --label v2`, three rounds: **16, 15, and 16 passed out of 24** (47 of 72), about 7 minutes per round. Then `bash infra/07-score.sh compare`:

| | v1 (`gpt-5.4`) | v2 (Model Router, Balanced) | Change |
|---|---:|---:|---|
| **Mean score** | 0.63 | 0.57 | ▼ 0.07 |
| **Pass rate** | 82% | 65% | ▼ 17 points |
| Easy | 0.66 | 0.66 | same |
| Medium | 0.60 | 0.58 | about the same |
| **Hard** | 0.63 | **0.45** | ▼ large drop |
| Weakest area | `structured_booking_evidence` (2.0) | same (2.0) | not fixed |
| **P50 / P95** | 10.6 s / 18.9 s | 12.6 s / 25.0 s | ▼ slower |
| Tokens per answer | 4,801 | 5,969 | ▲ +24% |
| **Estimated cost per answer** | ≈ $0.019 | ≈ $0.007 | **▼ about 65% cheaper** |

v1's cost is estimated from list prices (`gpt-5.4`: $2.50 in, $15.00 out per million tokens). v2's comes from Foundry's Monitor tab. Both ignore cache discounts. v2 has 71 scored rows because one answer didn't get a score.

#### Which models Model Router chose, and what they cost

Foundry → **Models → model-router → Monitor** shows the routing mix and cost by meter. Azure Monitor's `ModelRouterRequests` metric, split by `ModelName`, gives the same picture.

| Routed to | Share of calls | List price per 1M tokens (in / out) | Share of v2 cost |
|---|---:|---|---:|
| `gpt-5.6-luna` | 77% | $0.20 / $1.20 | 15% |
| `gpt-5.6-sol` | 23% | $4.00 / $20.00 | **78%** |
| Model Router fee | — | — | 7% |

<!-- Screenshot to add: Foundry → Models → model-router → Monitor (cost by meter). Save as img/MODEL-ROUTER-COST-01.png and link it here. -->

**What it means:**

- **On easy questions, the router works as advertised.** Same quality (0.66) at a fraction of the price: most of those calls went to the small `gpt-5.6-luna`.
- **On hard, policy-heavy questions, quality collapsed (0.63 → 0.45).** These need multi-step reasoning: check policy, plan, then book with evidence. Policy reasoning was already v1's weak spot, and a small model makes it worse.
- **It's slower,** because the hard calls that go to `gpt-5.6-sol` are slow reasoning calls, and there are more tool calls per answer (+24% tokens).
- **It's still about 65% cheaper.** Most calls run at about 1/12 of `gpt-5.4`'s price, so more tokens still cost less. That's the "tokens aren't cost" point in practice.
- **A few calls drive most of the bill.** `gpt-5.6-sol` handled about 1 in 4 calls but about 78% of v2's cost. The router fee itself is small (7%).
- **Verdict: this step went down.** It's cheaper, but worse on what Caldova cares about most, the right policy decisions on hard requests. **Keep v1.** Model Router didn't fail; this routing setting doesn't suit this workload, and the scorecard caught that before anyone switched the portal.

**Talk about it:**

- "Model Router cut our cost by about two-thirds, and on easy questions it was just as good. But on hard, policy-heavy requests, quality dropped from 0.63 to 0.45. Caldova can't accept that, so we keep v1."
- "We didn't guess this. The same scorecard on the same questions told us. That's what makes this a hill climb and not a hunch."
- "Look at the cost chart: the expensive model handled a quarter of the calls and most of the bill. The router fee is a rounding error."
- "This isn't the end for Model Router. It has a Quality mode. That's our next single step."

#### Next step: v2-quality

The obvious next step is **one change**: the same Model Router, switched to **Quality** routing mode, which picks the strongest model for each prompt and ignores cost. See step 7b below.

### Step 7b. Try Model Router in Quality mode

> 🔀 **Spotlight: Model Router** (Quality routing)

`bash infra/08-model-router.sh --mode quality` creates a second router deployment, `model-router-quality` (`routing.mode = quality`, capacity 300), and one agent version that uses it, labeled **v2-quality**. Then `bash infra/07-score.sh run --label v2-quality` scores it the same way.

**Why this step:** v2 (Balanced) was about 65% cheaper but dropped on hard questions (0.63 → 0.45), because most calls went to the small `gpt-5.6-luna`. Quality mode tests one idea: *let the router choose, but choose for quality*. Everything else stays the same: instructions, tools, testing questions, scorecard, judge, and rounds.

| Routing mode | How the router picks |
|---|---|
| **Balanced** (v2, default) | Considers models within a small quality band of the best one for the prompt, then picks the **cheapest**. |
| **Quality** (v2-quality) | Picks the **highest-quality** model for the prompt, ignoring cost. |
| Cost (not tried) | Considers a wider quality band, then picks the cheapest. |

**What the script does:**

1. Creates `model-router-quality` with `"routing": {"mode": "quality"}`, or reuses it if it already exists in Quality mode. The original `model-router` stays on Balanced, so v2 is unchanged.
2. Deploys one new agent version on `model-router-quality` and records it as **v2-quality**.
3. Switches the portal back to the version that was live before (v1).
4. Sends v2-quality one test question.

Routing mode changes can take **up to 5 minutes** to take effect. Wait a few minutes before scoring so all rounds use Quality routing.

**What happened in our run:**

- `model-router-quality` was created in Quality mode, and the agent deployed in about a minute as **contoso-travel version 3**, recorded as label **v2-quality**.
- The script switched the portal back to v1 automatically. The `@latest` fix from step 7 worked.

> **Label vs. version number.** Version numbers count up with each deploy (1, 2, 3, …). Labels name what changed. Here, **version 3 is v2-quality**, and the optimizer's **v3** label will get a later version number. The scripts always use labels, so you rarely need the numbers. When Foundry shows `contoso-travel: 3`, it means v2-quality.

**First look: the same test question for all three versions**

| | v1 (`gpt-5.4`) | v2 (Balanced) | v2-quality (Quality) |
|---|---|---|---|
| Answer | "The tool returned no rule ID, so I can't cite one" | **CT-02**, at least 7 days before departure | **CT-02**, at least 7 calendar days before departure, unless a disruption exception applies |
| Time | 7.5 s | 13.5 s | **24.8 s** |
| "Understood tasks" printed twice | Yes | Yes | Shorter: a one-line summary, then the structured section |

On one question, v2-quality gave the most complete answer but took three times as long as v1. That's what Quality mode trades: stronger models, slower answers. The routing mode may still have been settling, so wait for the 72-answer scores before drawing conclusions.

**What we expect to see,** so we can check our prediction:

- **Hard questions** recover toward v1's 0.63, because policy-heavy prompts should go to stronger models.
- **Cost** rises compared with v2, with more calls going to `gpt-5.6-sol`, but may still come in below v1.
- **Latency** stays similar to or above v2, since stronger models, often reasoning models, are slower.

If quality recovers *and* the cost is below v1, Model Router earns its place. If quality recovers but the cost is above v1, keep v1: we'd be paying more for the same result.

**Where to look afterwards:**

- `bash infra/07-score.sh compare` for v1, v2, and v2-quality side by side.
- Foundry → **Models → model-router-quality → Monitor** for the new routing mix and cost by meter. Compare it with the `model-router` Monitor tab.

**Results:** `bash infra/07-score.sh run --label v2-quality`, three rounds: **16, 9, and 14 passed out of 24** (39 of 72). Then `bash infra/07-score.sh compare`:

| | v1 (`gpt-5.4`) | v2 (Balanced) | v2-quality (Quality) |
|---|---:|---:|---:|
| Mean score | **0.63** | 0.57 | 0.50 |
| Pass rate | **82%** | 65% | 54% |
| Easy | **0.66** | **0.66** | 0.52 |
| Medium | **0.60** | 0.58 | 0.52 |
| Hard | **0.63** | 0.45 | 0.46 |
| Weakest area | `structured_booking_evidence` (2.0) | same (2.0) | same (2.2) |
| P50 / P95 | **10.6 s / 18.9 s** | 12.6 s / 25.0 s | 16.2 s / **49.5 s** |
| Tokens per answer | **4,801** | 5,969 | 6,375 |
| Estimated cost per answer | ≈ $0.019 | **≈ $0.007** | ≈ $0.040 |
| Routing mix | — | luna 77%, sol 23% | **sol 100%** |

#### Which models Quality mode chose, and what they cost

Azure Monitor (`ModelRouterRequests` by `ModelName` and `RouterMode`) shows that **Quality mode sent every call, 285 of 285, to `gpt-5.6-sol`**, the strongest and most expensive model in the router's pool. There were no fallbacks and no errors.

| | Input tokens | Output tokens | List price per 1M (in / out) | Estimated cost |
|---|---:|---:|---|---:|
| `gpt-5.6-sol` via `model-router-quality` | 454,839 | 52,109 | $4.00 / $20.00 | ≈ $2.86 |
| Model Router fee (≈ 7%, as in v2) | | | | ≈ $0.05 |
| **Total for 73 answers** | | | | **≈ $2.91, about $0.040 per answer** |

That's roughly **2× v1** and **6× v2** per answer, for the lowest quality of the three.

<!-- Screenshot: Foundry → Models → model-router-quality → Monitor (cost by meter) -->

**What it means:**

- **Our prediction was wrong, and that's the point of predicting.** We expected Quality mode to recover hard-question quality. It didn't (0.46 vs. v1's 0.63), and easy questions got worse (0.52 vs. 0.66).
- **A stronger, pricier model isn't automatically better for *your* agent.** `gpt-5.6-sol` is a stronger general model, but v1's instructions were written and tested with `gpt-5.4`. The scorecard measures Caldova's policy behavior, not general intelligence, and on that, the most expensive option did worst.
- **The weakest area didn't move. Not with any model.** `structured_booking_evidence` sits at about 2 out of 5 for `gpt-5.4`, for a luna/sol mix, and for all-sol. When the same weakness survives three different models, **the problem isn't the model. It's the instructions.** The agent was never clearly told to pass the policy tool's result into the booking step. (Act 4's round 2 found the rest: some of it was our tools.)
- **Cost and latency moved in the wrong direction.** 100% reasoning-model calls doubled v1's cost and pushed P95 to almost 50 seconds.
- **Variance was highest here:** 16, 9, then 14 passed. A 7-question swing on the same version shows why we never judge from one round.

**Cost as a factor, across all three versions:**

| | Quality (mean) | Cost per answer | Verdict |
|---|---:|---:|---|
| v1 (`gpt-5.4`) | **0.63** | ≈ $0.019 | Best quality. Keep. |
| v2 (Balanced) | 0.57 | **≈ $0.007** | Cheapest by far, but loses on hard, policy-heavy questions. |
| v2-quality (Quality) | 0.50 | ≈ $0.040 | Most expensive and lowest quality. Reject. |

- **The cheapest version isn't the worst, and the most expensive isn't the best.** Spending more on the model bought *less* quality here.
- **v2 (Balanced) is the interesting one for cost.** It matched v1 on easy questions at about a third of the cost. If the instructions fix the hard-question weakness, a cheaper routed model might hold quality. That's worth retesting *after* Act 4.
- **Insights was the biggest single cost of the day** (about $27 of `gpt-5.6-sol` judge tokens). Scoring all three versions cost less than that.

**Verdict: two model steps, both down. Keep v1.** The model lever is exhausted for now. The next lever is the **instructions**, and that's exactly what Agent Optimizer works on in Act 4.

**Talk about it:**

- "We tried the cheap route and the premium route. Premium cost twice as much as v1 and scored worst. More expensive isn't better; *measured* is better."
- "Look at the weakest area: about 2 out of 5 on booking evidence for every model we tried. When a problem follows you across three models, it's not the model. It's what we told the agent to do."
- "That's the real value of hill climbing: two steps down still told us where *not* to go, and pointed us to the next lever, the instructions."
- "Version 3 in Foundry is v2-quality. Version numbers count deploys; labels name the change. We always talk in labels."

#### The positive story for Model Router

Model Router didn't beat v1 overall, but it delivered real value, and its biggest win is probably still ahead.

| What Model Router did well | Evidence from this run |
|---|---|
| **Same quality on easy requests, at a third of the cost** | Easy: v1 0.66, v2 **0.66**. Cost per answer: about $0.019 vs. **about $0.007**. For lookups, receipts, and blocked trips, the router chose `gpt-5.6-luna` and lost nothing. |
| **Nearly the same on medium requests** | 0.60 vs. 0.58, within the run-to-run noise we saw. |
| **The router fee is small** | About 7% of v2's bill. It doesn't eat the savings it creates. |
| **The model lever was cheap to test** | Two routing strategies built and scored in an afternoon, with no code change: one deployment swap per version. |
| **Clear view of where the money goes** | The Monitor tab showed routing mix and cost per model: 23% of calls on sol made up 78% of the cost. |
| **It helped prove the weakness is in the instructions** | Three model setups, the same 2/5 on booking evidence. Switching models was the fastest way to rule the model out. |

**Where it fell short:** hard, policy-heavy requests, where v1's *instructions* are already weak. The Foundry docs ask for exactly the check we did: *"Evaluation remains important: compare model router with your current baseline to confirm that managed routing improves the outcomes that matter for your workload."*

**Where the real win probably is:** fix the instructions first (Act 4), then put the improved instructions back on Model Router. If hard requests recover, Model Router could deliver v1-level quality at about a third of the cost. See **step 11b** below.

**Talk about it:**

- "Model Router matched our frontier model on easy and medium requests, at about a third of the cost. That's real money at scale."
- "It didn't fix our hard cases, and it couldn't. The weakness is in our instructions, not the model, and the router helped us prove that fast."
- "So the order matters: fix the instructions first, then let the router save money. Let the evidence tell you which lever to pull next."

### Step 8. Build and score v2-alt, the fine-tuned smaller model

**Skipped in Act 3, on purpose.** After two model steps went down, the evidence pointed at the **instructions**, not the model: booking evidence scored about 2/5 on every model we tried. A student copies its teacher's reviewed answers, and few of v1's hard answers would pass review ("right policy decision", "totals add up"). A v1-taught student would mostly learn the easy cases, where Model Router already saves money. An earlier run of this session supports that: students taught from v1-style answers scored well below the baseline.

**What we did instead:** improve the instructions first (Act 4), then fine-tune with the better version as the teacher. We tried exactly that in [round 2](#round-2-the-teacher-review-found-our-tool-bugs), and the review stopped us again, this time pointing at our tools.

**Talk about it:**

- "We could fine-tune now, but a student is only as good as its teacher. Our teacher's weakness is in its instructions, so we fix those first, then teach."

### Step 9. Compare

`bash infra/07-score.sh compare` after every version was scored on the same 24 testing questions, three rounds each, with the same Rubric Evaluator and judge:

| Version | What changed | Mean | Pass rate | Hard | Weakest area | P50 / P95 | Tokens per answer | Verdict |
|---|---|---:|---:|---:|---|---:|---:|---|
| **v1** | Starting point (`gpt-5.4`) | 0.63 | **82%** | **0.63** | booking evidence (2.0) | 10.6 / 18.9 s | **4,801** | **Live** |
| v2 | Model Router, Balanced | 0.57 | 65% | 0.45 | booking evidence (2.0) | 12.6 / 25.0 s | 5,969 | Down. About 65% cheaper, but weak on hard requests. |
| v2-quality | Model Router, Quality (all `gpt-5.6-sol`) | 0.50 | 54% | 0.46 | booking evidence (2.2) | 16.2 / 49.5 s | 6,375 | Down. About 2× v1's cost. |
| v3 | Optimizer's instructions (`gpt-5.4`) | **0.64** | 75% | 0.58 | clarification (1.9) | **9.0 / 14.4 s** | 6,612 | Sideways. Faster and better evidence, weaker policy checking. |
| v3-router | v3's instructions on Model Router | 0.54 | 65% | 0.43 | booking evidence (1.9) | 14.1 / 29.3 s | 8,371 | Down. Below both v3 and v2. |
| **v3-tools** | v3 with fixed tools and data | **0.66** | **82%** | **0.70** | clarification (2.4) | **8.6** / 15.1 s | 7,288 | **Up. First version to beat v1.** |

**The climb, as it actually happened:**

```text
                                   v3-tools  0.66  (UP: fixed tools; best on hard questions)
                                  /
                       v3  0.64  (sideways: faster, better evidence, weaker policy checks)
                      /  \
                     /    v3-router  0.54  (down: the two levers didn't stack)
   v1  0.63 --------+---- v2  0.57  (down: cheaper, weak on hard requests)
                     \
                       v2-quality  0.50  (down: most expensive, slowest)
```

Five steps tried, one clearly up. v3-router and v3-tools come from Act 4; see steps 11b and 11d.

---

## Act 4: Make it scale

### Step 10. Let Agent Optimizer try instruction changes

> ⚙️ **Spotlight: Agent Optimizer**

**Starting point: v1.** After Act 3, v1 was still the best-scoring version (0.63 mean, 82% pass), so we optimized from it:

```bash
bash infra/10-optimize.sh submit --from-label v1
```

**What we saw:**

- The job was accepted and **queued** in Foundry (`opt_…`). The CLI notes that *"optimization creates candidate agents as draft versions. Your live agent versions are not affected until you explicitly deploy a candidate."*
- `bash infra/10-optimize.sh status` confirmed the setup:
  - **Agent:** `contoso-travel`, version 1
  - **Practice data:** `brk330-exploring` v1. In this run it used **all 36 exploring questions, once each**, not just the 12 practice rows; see the note below.
  - **Scorecard:** `brk330-travel-scorecard` v1, the same one used to score every version
  - **Judge:** `gpt-5.4-mini`; **optimizer reasoning:** `gpt-5.4`; **candidates:** 3
- The script restored the baseline config file afterwards, as designed.

#### What the optimizer starts from

The status output includes v1's full instructions. Reading them explains two things we saw earlier:

- **"Understood tasks" printed twice:** step 1 says *"Briefly identify the requested tasks,"* **and** the required format starts with an *"Understood tasks"* section. The agent does both, so the heading appears twice.
- **The weak `structured_booking_evidence` score:** the instructions say *"Treat Caldova policy as a hard gate"* and *"Keep booking operations in dry-run mode,"* but they never say to **pass the policy tool's result into the booking step**, or that **"not blocked" isn't the same as "approved."** That gap shows up as about 2/5 on every model we tried.

Both are instruction problems, which is exactly what the optimizer changes.

#### Which Insights findings the optimizer can address

Each Insights finding came with a proposed fix. Some are **instruction changes**, which the optimizer can make. Others are **code changes**, which it can't: it changes instructions, and model choice where allowed, not your tool code. When you review candidates, check them against this list.

| Insights finding (traces) | Proposed fix, in short | Can the optimizer fix it? | What to look for in a candidate |
|---|---|---|---|
| "Nothing blocked" treated as approval (45) | Assert approval only with an explicit decision and cited rule IDs; otherwise say it's inconclusive and don't book. Also update the response parser. | **Mostly.** The instruction rule, yes. The parser change, no. | A rule like "only call something compliant when the tool returns a decision with rule IDs." |
| Policy checks done ad hoc (23) | Make policy validation a required stage for every candidate option before recommending. | **Partly.** It can require a check before any recommendation. A code-enforced stage needs tool or orchestration changes. | "Call `check_travel_policy` for every option before recommending it." |
| Receipt-line classification omitted (11) | Always list reimbursable and non-reimbursable lines, and say so when none are flagged. | **Yes.** It's a response-format rule. | A required receipt section that lists both kinds of lines. |
| Fabricated missing trip details (5) | Use only user-supplied or derived values; ask when something's missing. | **Yes**, as an instruction. Code validation would be stronger. | "If a required detail is missing, ask; never fill in defaults." |
| Invented ID requirements for city searches (4) | Send city questions straight to the city search tools. | **Yes.** It's tool-selection guidance. | "For city questions, search by city; don't ask for item IDs." |
| Booking sent prose instead of policy evidence (2) | Copy the policy tool's fields straight into the booking call; reject written-up compliance text. | **Partly.** It can instruct the copy. Schema validation needs code. | "Pass the `check_travel_policy` result as `compliance_summary`, unchanged." |

**What this means for the story:**

- **The rubric links Insights to the optimizer.** The optimizer doesn't read Insights directly. It improves the scorecard score, and the scorecard dimensions *came from* the Insights findings. So a better score should mean findings addressed.
- **Some fixes belong in code.** Insights recommended a response parser, an evidence-mapping layer, and a required orchestration stage. Those are engineering tasks for a person, often with GitHub Copilot's help. Instructions can only go so far.
- **The practice set limits what it can learn.** Only a handful of the exploring questions involve receipts or bookings, so it may not fix every finding. That's another reason to retest on the 24 testing questions.

#### Should we run Insights again at the end?

**Yes: once, on v3, with a short window.** The scorecard tells you *how much* v3 improved. A second Insights scan tells you *which problems went away*, which closes the loop from Act 2.

```bash
bash infra/04-run-questions.sh --label v3 --repeats 1 --parallel 3
bash infra/05-insights.sh --label v3 --lookback-hours 1
```

- **Keep it small.** One pass of the 36 exploring questions is enough to compare. Insights was the most expensive step in our run (about $27 for about 108 traces), so 36 traces should cost roughly a third of that.
- **Keep the window clean.** Insights reads every trace for the agent in the window, regardless of version. Start the scan right after the questions finish, and don't score or test other versions in between.
- **Compare side by side.** v3's findings save to `findings-v3.json`, next to v1's `findings.json`. Look for findings that disappeared, finding trace counts that dropped, and anything new.

**On stage:** "In Act 2, Insights told us what was wrong. The optimizer fixed what it could in the instructions. Now we ask Insights again: which problems are gone, and which ones need an engineer?"

**Progress:** after about 26 minutes, the baseline and the first candidate had been fully scored. Foundry → **Evaluations → agent_optimization_eval_opt_…** shows every run the optimizer made:

| Run | Target | What it is | Passed | P50 | P95 | Agent tokens |
|---|---|---|---:|---:|---:|---:|
| `baseline` | `contoso-travel: 1` | v1 on all 36 exploring questions, once each | 26 / 36 (72%) | 8.4 s | **34.6 s** | 200,308 |
| `minibatch_1` | `contoso-travel: 1` | Quick 3-question check of v1 | 3 / 3 | 5.8 s | 17.6 s | 7,282 |
| `minibatch_2` | draft (candidate 1) | Same quick check on the new draft | 3 / 3 | 6.8 s | 15.7 s | 14,826 |
| `candidate_1` | draft (candidate 1) | Candidate 1 on the same 36 questions | **29 / 36 (81%)** | 8.3 s | **15.5 s** | 264,480 |
| `minibatch_3` | `contoso-travel: 1` | Quick check for the next idea | 3 / 3 | 8.0 s | 22.3 s | 15,751 |
| `minibatch_4` | draft (candidate 2) | Quick check of candidate 2 | 3 / 3 | 9.1 s | 23.9 s | 26,014 |
| `candidate_2` | draft (candidate 2) | Candidate 2, full practice run | _in progress_ | | | |

The status command reports mean scores: baseline **0.560**, candidate_1 **0.624** (+0.064).

<!-- Screenshot to add: Foundry → Evaluations → agent_optimization_eval_opt_… (baseline, minibatches, candidate_1). Save as img/OPTIMIZER-RUNS-01.png and link it here. -->

**What to point at in this screen** (Foundry → **Evaluations → agent_optimization_eval_opt_…**):

1. **The bottom row, `baseline`:** v1 on the practice questions, **26 / 36 (72%)**. Every candidate is measured against this.
2. **The `minibatch_*` rows:** 3-question quick checks. The optimizer tries an idea on a few questions before investing in a full run. They always show 3 / 3, so don't read them as scores.
3. **The `candidate_1` row:** the first full candidate, **29 / 36 (81%)**. Three more passing answers than the baseline.
4. **The Target column:** baseline and some minibatches say `contoso-travel: 1` (v1); candidates say `draft-…`. **Drafts aren't live** and don't get version numbers.
5. **P95 latency:** the baseline's slowest answers took **34.6 s**, candidate_1's took **15.5 s**. Better instructions cut the long, wandering answers.
6. **Target tokens:** **200,308 → 264,480**, about a third more for candidate_1. Better isn't free.
7. **`candidate_2`: In progress.** The search keeps going until it has written and scored three candidates.

**Say this while pointing:** "Bottom row is where we started. The small 3-question runs are the optimizer testing ideas cheaply. When an idea holds up, it gets a full run, like candidate 1: three more passing answers, half the slow-end wait, about a third more tokens. And every candidate is a draft. Nothing is live until we decide."

#### How to read the optimizer's runs

- **Two kinds of runs.** **Minibatches** are quick 3-question checks: the optimizer tries an idea on a few questions, and if it holds up, writes a candidate. **Candidate runs** score that candidate on every practice question (36 answers here). Only candidate runs count. Minibatches always show 3 / 3 here because they're a quick sanity check, not a score.
- **Candidates are drafts.** Their target is `contoso-travel: draft-…`, not a numbered version. Drafts don't change the live endpoint or use up version numbers. A candidate becomes a real version only when you run `bash infra/11-promote.sh deploy`.
- **The baseline and candidates use the same 36 answers' worth of questions,** so you can compare them directly in this list.

#### Why the baseline starts at 0.56, not v1's 0.63

It's the same agent (v1), the same scorecard, and the same judge. The number differs because of **which questions** were asked:

| | Step 07 (testing) | Optimizer baseline (practice) |
|---|---|---|
| Questions | 24 testing questions | All 36 exploring questions |
| Mix | 8 easy, 8 medium, 8 hard, all in new cities and receipts | 12 easy, 12 medium, 12 hard, including the four portal scenarios |
| Answers | 24 × 3 rounds = 72 | 36 × 1 = 36 |
| Who ran it | `bash infra/07-score.sh` | The optimizer's own evaluation |

- **The exploring questions are v1's known trouble spots.** They're the questions whose traces Insights read and the scorecard was drafted from, including HERO (booking without policy evidence) and ACCESS (no policy check, missing flight). A set built around known weak spots scores lower.
- **One answer per question.** Each question counts once, so a few weak scenarios pull the average down with no repeats to smooth them out.
- **So the two numbers answer different questions.** 0.56 is "how v1 does on the questions we learned from," the bar each candidate must beat. 0.63 is "how v1 does on questions nobody tuned for," the bar v3 must beat in step 07.

> **Note on the practice set.** We meant the optimizer to use only the 12 practice rows (`max_samples: 12` in the config), but it used all 36 exploring questions. The testing questions were still never used, so the final comparison in step 07 stays fair. The optimizer simply practiced on more questions than planned.

**Rule of thumb:** compare candidates with **0.560**. Compare v3 with **v1's 0.63** only after scoring v3 on the testing questions.

#### Reading candidate_1 so far

- **Better quality on practice questions:** 26 → 29 passed out of 36 (72% → 81%), with a mean of 0.560 → 0.624.
- **A much better slow end:** P95 dropped from **34.6 s to 15.5 s**, while P50 stayed the same (8.4 → 8.3 s). Clearer instructions seem to cut the long, wandering answers.
- **About 32% more tokens** (200,308 → 264,480 for 36 answers). Optimized instructions are longer and ask for more checks, and on the same model (`gpt-5.4`), more tokens means more cost. (The status JSON's `avg_tokens` field reports +65%, a different average; use Foundry's totals.)
- **The trade-off to weigh:** about 32% more cost for +9 points of pass rate and a slow end that's more than twice as fast.

**Talk about it:**

- "The optimizer measures v1 on its practice questions, which include the scenarios we already know are hard. That's why it starts at 0.56, lower than the 0.63 we got on the testing questions. Different test, same ruler."
- "See the minibatches? The optimizer tries an idea on three questions first, and only writes a full candidate if it looks promising. It's hill climbing inside hill climbing."
- "Candidate 1 passes three more practice answers and its slowest answers are twice as fast, but it uses about a third more tokens. Better isn't free. The testing questions will tell us if it's worth it."
- "These candidates are drafts. Nothing is live, and nothing gets a version number until a person decides."

#### Candidate 2: faster and leaner than candidate 1, but a lower score

| | baseline (v1) | candidate_1 | candidate_2 |
|---|---:|---:|---:|
| Mean practice score | 0.560 | **0.624** | 0.572 |
| Avg agent tokens per answer\* | 4,702 | 7,347 | 6,812 |
| P50 / P95\* | 8.4 s / 16.5 s | 8.4 s / 14.8 s | **8.0 s / 14.7 s** |

\*Worked out from the individual answers. Foundry's run-level numbers differ slightly, but they rank the same way.

**Per scorecard dimension (average 1–5, only where it applied):**

| Dimension (weight) | baseline | candidate_1 | candidate_2 |
|---|---:|---:|---:|
| `policy_gated_outcome` (10) | 3.29 | 3.21 | **3.12** |
| `structured_booking_evidence` (4) | 2.89 | 3.00 | **2.00** |
| `evidence_preservation` (6) | 3.33 | **3.69** | 3.49 |
| `missing_input_clarification` (5) | 2.00 | **2.55** | 2.20 |
| `general_quality` (5) | 3.21 | **3.50** | 3.29 |
| `policy_check_before_recommendation` (5) | **3.68** | 3.46 | 3.67 |
| `tool_usage_matches_request_type` (4) | 3.88 | **4.00** | 3.97 |
| `receipt_classification_and_conversion` (6) | **4.00** | 3.83 | **4.00** |

**Why candidate 2 scored lower:** it got faster and leaner by **doing less of the work the scorecard weighs most**.

- **Booking evidence fell to 2.0 out of 5,** its worst score anywhere. On multi-step booking and planning questions, candidate 2 skips or shortens the step that passes policy evidence into the booking. That's exactly the gap Insights flagged.
- **Its biggest drops were on multi-step trips:** the London trip plan (0.82 → 0.35), the Boston SUV booking (0.82 → 0.36), the Paris flight (0.61 → 0.39), and the business-class booking (0.74 → 0.52), all compared with candidate 1.
- **It improved on simple tasks:** receipts (one perfect 1.00), city lookups, and hotel lists. Those carry less weight and were already fine.
- **Fewer tokens came from shorter workflows.** Doing fewer steps on hard requests saves tokens and time, and costs quality where it matters.

**Neither candidate is better everywhere.** On "EMP-001 can only fly after 8:00…", the baseline scored 0.88, candidate 1 scored 0.22, and candidate 2 scored 0.46. Both rewrites **regressed** on the time-constraint question. When you review, check the questions that got worse, not just the average.

**What this teaches:**

- **Faster and cheaper is good only if quality holds.** We said the same about Model Router in Act 3, and now it happens with instructions too. The scorecard catches it either way.
- **The optimizer explores, and not every step goes up.** Candidate 2 is a step down from candidate 1. That's normal: it tried a leaner approach, measured it, and the numbers say no. Hill climbing inside hill climbing.
- **The average hides trade-offs.** Look at the dimension table and the questions that regressed before choosing.

**Talk about it:**

- "Candidate 2 is faster and cheaper than candidate 1, so why is the score lower? Look at booking evidence: 2 out of 5. It saved time by skipping the step Insights told us mattered most."
- "Neither candidate is better everywhere. Both got worse on the flight-time question. That's why a person reviews before anything goes live."
- "Same lesson as Model Router: cheaper and faster only counts if the policy decisions stay right."

**Results:** the job finished in about 45 minutes with three candidates:

| Candidate | Practice score | vs. baseline | Strategy |
|---|---:|---:|---|
| baseline (v1) | 0.560 | — | — |
| **candidate_1 ★** | **0.624** | **+0.064** | system_prompt |
| candidate_2 | 0.572 | +0.012 | system_prompt |
| candidate_3 | 0.574 | +0.014 | system_prompt |

- **All three changed only the instructions** ("system_prompt"). None changed the model or tools, so these are pure instruction steps on `gpt-5.4`.
- **One clear step up, two small ones.** Candidates 2 and 3 barely beat the baseline, which is within the noise on 36 answers. Candidate 1 is the only one with a meaningful lead.
- **The ★ is the optimizer's suggestion, not a decision.** The CLI prints `azd ai agent optimize apply … then azd deploy`. We use `bash infra/10-optimize.sh apply` and `bash infra/11-promote.sh deploy` instead, so the candidate becomes a labeled version (v3) without going live.

[![Agent Optimizer job complete in Foundry: improvement, run overview, score comparison, and candidate results](img/OPTIMIZER-01-complete.png)](img/OPTIMIZER-01-complete.png)

**What to point at in this screen** (Foundry → **Agents → contoso-travel → Optimize →** the job):

1. **Improvement (left):** goal "Improve quality", marked **Improved**. Best candidate **candidate_1, 0.624 (+0.064)** against a baseline of 0.56.
2. **Run overview (middle):** 3 candidates, dataset `brk330-exploring`, judge `gpt-5.4-mini`, about **1 hour**, and **2.1M total tokens**. That's agent answers, judge scoring, and the optimizer's own reasoning combined, so automated search isn't free either.
3. **Score comparison (right):** candidate_1 is well ahead; candidates 2 and 3 are barely above the baseline.
4. **Candidate results table:** the most useful part for the session.

   | Candidate | Score | Avg tokens | Avg latency | What it tells you |
   |---|---:|---:|---:|---|
   | baseline | 0.56 | 4.4K | 10.9 s | Where we started (Version 1) |
   | **candidate_1 ★** | **0.624** | 7.3K | 9.6 s | Biggest gain, faster on average, but about +65% tokens |
   | candidate_2 | 0.572 | 6.6K | **9.5 s** | Leanest rewrite; lost on booking evidence |
   | candidate_3 | 0.574 | **8.8K** | 10.9 s | Most tokens for almost no gain: the worst deal |

   Every candidate changed only the **System prompt**. That's the Optimizations column.
5. **View changes:** shows exactly how each candidate rewrote the instructions. Open it for candidate_1 on stage; it's the most concrete moment of Act 4.
6. **Deploy best candidate (top right): don't use it here.** It deploys the candidate straight away. We use `bash infra/10-optimize.sh apply` and `bash infra/11-promote.sh deploy` so it becomes a labeled version (v3), doesn't go live automatically, and gets scored on the testing questions first.

The page header shows the optimizer job ID. Crop it out if you publish the screenshot.

**Say this while pointing:** "One hour, three ideas, all automated. One clear winner on practice questions, two that barely moved. Candidate 3 is the cautionary tale: the most tokens for almost no gain. And see this big purple button? We're not pressing it. A person reads the changes, and the testing questions decide."

**Talk about it:**

- "Three candidates, one clear winner on practice questions. The optimizer stars it, but it doesn't deploy it. That's our call."
- "Two of the three barely moved the needle. Automated search still mostly produces small or no gains. The value is that it tries many ideas cheaply, and we only keep the good one."

**Our choice: candidate_1**, after reviewing its instructions against the Insights checklist above and the flight-time regression (0.88 → 0.22 on "EMP-001 can only fly after 8:00…").

`bash infra/10-optimize.sh apply --candidate cand_opt_…_0001` downloaded it to `src/agent/.agent_configs/cand_opt_…_0001/`. Same model (`gpt-5.4`). The instructions grew from **1.1 KB to 6.5 KB**, about 6 times longer, which explains much of the extra token use.

**What the apply output showed:**

```text
Fetching candidate config...
Updating agent definition in azure.yaml...
✓ Candidate cand_opt_…_0001 applied to .agent_configs/cand_opt_…_0001
Run azd deploy --service contoso-travel to deploy the optimized agent.
Instruction diff (baseline → optimized):
  — Baseline (21 lines, 1117 chars)
  — Optimized (74 lines, 6519 chars)
Kept azure.yaml unchanged; versions pick their config through CONTOSO_CONFIGURATION.
```

- **The optimizer edited `azure.yaml`, and our script put it back.** The CLI's apply rewrites the agent definition so the next `azd deploy` uses the candidate. In this repo each version picks its config through `CONTOSO_CONFIGURATION` instead, so the script restores `azure.yaml` and lets `bash infra/11-promote.sh deploy` choose the config for that one deploy. Your shared files stay clean, and every version stays reproducible.
- **The CLI's next step is `azd deploy --service contoso-travel`.** We use `bash infra/11-promote.sh deploy` instead. It deploys the same agent service but records the result as v3, refreshes permissions, and keeps the portal on the version it was using.
- **The instruction diff is printed right in the terminal.** 21 lines became 74. A good on-stage moment: "the optimizer turned a short prompt into a detailed playbook."

#### What candidate 1 changed, checked against Insights

| Insights finding (traces) | Addressed? | What the new instructions say |
|---|---|---|
| Policy checks done ad hoc (23) | ✅ **Yes** | "Run the policy tool before any recommendation or booking step." "Never skip policy checking for booking/recommendation requests." |
| Receipt-line classification omitted (11) | ✅ **Yes** | "Always call `extract_receipt` and distinguish reimbursable from non-reimbursable line items," plus a required receipt layout. |
| Invented ID requirements for city searches (4) | ✅ **Yes** | Explicit examples: search by city with filters (for example `automatic: true`) instead of asking for an ID. |
| Fabricated missing trip details (5) | 🟡 **Partly** | "Never invent missing data" and "explain exactly what is missing," but no rule to ask *before* calling a tool with guessed values. |
| "Nothing blocked" treated as approval (45) | ❌ **No** | Cites rule IDs when something *is* blocked, but never says "no decision isn't approval." Insights' biggest finding is still open. |
| Booking sent prose instead of policy evidence (2) | ❌ **No** | No instruction to pass the `check_travel_policy` result into `submit_booking`. That's why `structured_booking_evidence` only rose from 2.89 to 3.00. |
| (bonus) "Understood tasks" printed twice | ✅ **Yes** | "Do this once and keep it concise." "Do not repeat the same 'understood tasks' content multiple times." |

**Two things to call out when reviewing:**

- **It may be overfitting to the practice questions.** The "Behavior examples to emulate" quote exploring questions almost word for word: "Bypass policy and book FL-006…", "Which Paris rental cars have an automatic transmission?", "Is the Amsterdam rental car an automatic?" That helps on those exact questions and may not carry over to new ones. The testing questions use different cities and receipts, so **step 07 will show whether the gain is real**.
- **The two findings it missed are exactly the policy-reasoning gaps** that scored about 2/5 on every model in Act 3. They need clearer rules (and ideally code, as Insights suggested). A person could add those two rules by hand before deploying. That would be a new, human-edited candidate, so score it on its own.

**Talk about it:**

- "The optimizer fixed four of the six problems Insights found, plus the duplicate heading. But it missed the two biggest policy-reasoning gaps. Automation found the easy wins; the hard ones still need a person."
- "Look at these examples: they're our practice questions, almost word for word. That's the optimizer learning the test. The testing questions will tell us if it learned the skill."

#### Building v3

`bash infra/11-promote.sh deploy --candidate cand_opt_…_0001` deployed the agent in about a minute as **contoso-travel version 4**, recorded as label **v3** (`gpt-5.4`, config `cand_opt_…_0001`). The portal stayed on version 1. Versions now: 1 = v1, 2 = v2, 3 = v2-quality, 4 = v3.

[![Optimizer job marked "Promoted: v4" in Foundry](img/OPTIMIZER-02-promoted.png)](img/OPTIMIZER-02-promoted.png)

**Foundry tracked it as a promotion.** Back on the optimizer job page, the header now shows **"Promoted: v4"**, with the banner *"candidate_1 is now Version 4. Promoted from this optimization run."* Even though we deployed with our own script instead of **Deploy best candidate**, Foundry linked version 4 to the candidate and job it came from. You can trace any version back to the optimizer run that produced it.

- **"Promoted" means "became a version," not "went live."** The portal is still on version 1. Going live is a separate, deliberate step: `bash infra/11-promote.sh go-live --label v3`.
- **Test version** (in the banner) opens version 4 in the playground, which is handy for a quick look on stage without switching the portal.

**First look: the same test question across versions**

| | v1 | v2 (Balanced) | v2-quality | **v3 (optimized)** |
|---|---|---|---|---|
| Answer | No rule ID returned, so can't cite one | **CT-02**, 7 days | **CT-02**, 7 calendar days, with exceptions | No rule ID returned, so can't cite one |
| "Understood tasks" | Twice | Twice | One line, then the section | ✅ **Once** |
| Policy evidence shown | Summarized | Summarized | Summarized | ✅ Every returned field listed (`hard_gate_blocked`, `cited_rule_ids: []`, …) |
| Time | 7.5 s | 13.5 s | 24.8 s | **6.3 s** |

- **The formatting fix worked.** "Understood tasks" now appears once, which is exactly the rule the optimizer added.
- **Evidence is preserved, as instructed.** v3 lists every field the policy tool returned instead of paraphrasing. That's the new "preserve tool evidence faithfully" rule, and it's what `evidence_preservation` measures.
- **It's honest, like v1.** When the tool returns no rule, it says so instead of claiming compliance.
- **It didn't find CT-02 the way v2 did.** v2 built a lead-time test to make the tool return the rule; v3 didn't. One question proves nothing, but it's a reminder that instructions and models each bring different strengths.

**Talk about it:**

- "Same model as v1, new instructions. The duplicate heading is gone, and the agent now shows the evidence instead of summarizing it. That's what the optimizer changed, in one answer."
- "Foundry says 'Promoted: v4'. That means it's a real version now, linked to the optimizer run that made it. It doesn't mean it's live. The portal is still on v1 until we decide."

#### Scoring v3 on the testing questions

`bash infra/07-score.sh run --label v3`, then `bash infra/07-score.sh compare`. This is the same 24 testing questions, three rounds, with the same Rubric Evaluator and judge as v1, v2, and v2-quality.

**What we expect, written down before scoring:**

- **Better than v1 overall, but by less than on practice.** The practice gain was +0.064, and some of it likely came from examples copied from practice questions. Expect a smaller gain on new cities and receipts.
- **Gains in** `evidence_preservation`, `tool_usage_matches_request_type`, `receipt_classification_and_conversion`, and `missing_input_clarification`, the findings it addressed.
- **Little change in** `structured_booking_evidence` and `policy_gated_outcome`. It didn't add the two rules those depend on.
- **More tokens than v1** (longer instructions), with **P95 the same or better.**

If v3 beats v1's 0.63 mean with the policy dimensions holding, it's the first step up in this climb. If not, the gain was overfitting, and keeping v1 is still the right call.

[![Evaluation runs in Foundry: v3 scoring rounds alongside earlier versions](img/OPTIMIZER-03-evalruns.png)](img/OPTIMIZER-03-evalruns.png)

**Where to look:** Foundry → **Evaluations**, then the `brk330-v3-…` runs. **Target** shows `contoso-travel: 4` (v3). Compare its pass rate, P50/P95, and target tokens with the `brk330-v1-…` rows, the same columns explained in step 6.

**Results:** three rounds: **16, 20, and 18 passed out of 24** (54 of 72). Then `bash infra/07-score.sh compare`:

| | v1 | v2 | v2-quality | **v3 (optimized)** |
|---|---:|---:|---:|---:|
| Mean score | 0.63 | 0.57 | 0.50 | **0.64** (+0.01) |
| Pass rate | **82%** | 65% | 54% | 75% |
| Easy / Medium / Hard | 0.66 / 0.60 / **0.63** | 0.66 / 0.58 / 0.45 | 0.52 / 0.52 / 0.46 | 0.66 / **0.67** / 0.58 |
| Weakest area | booking evidence (2.0) | booking evidence (2.0) | booking evidence (2.2) | **missing-input clarification (1.9)** |
| P50 / P95 | 10.6 s / 18.9 s | 12.6 s / 25.0 s | 16.2 s / 49.5 s | **9.0 s / 14.4 s** |
| Tokens per answer | **4,801** | 5,969 | 6,375 | 6,612 (+38%) |

**Per dimension, v1 → v3 (1–5):**

| Dimension | v1 | v3 | Change |
|---|---:|---:|---:|
| `structured_booking_evidence` | 2.05 | 2.46 | **+0.41** |
| `evidence_preservation` | 3.47 | 3.81 | **+0.33** |
| `general_quality` | 3.35 | 3.43 | +0.08 |
| `tool_usage_matches_request_type` | 4.04 | 4.03 | — |
| `receipt_classification_and_conversion` | 4.27 | 4.20 | −0.07 |
| `policy_gated_outcome` | 3.47 | 3.37 | −0.10 |
| `missing_input_clarification` | 2.08 | 1.90 | −0.18 |
| `policy_check_before_recommendation` | 3.90 | 3.63 | **−0.26** |

**Questions that moved most:**

- **Gains:** T-10 Toronto flight-plus-hotel (0.31 → 0.51), T-18 "skip approval and book" in Zurich (0.63 → 0.81), T-15 Chicago hotel in policy (0.80 → 0.97).
- **Drops:** T-03 "Is the Union Square Inn within the cap?" (0.88 → 0.51), T-19 Toronto trip with "can't fly before 8:00" (0.57 → 0.32), T-23 Tokyo trip with a wheelchair-accessible hotel (0.54 → 0.38).

**Checking our prediction:**

| We predicted | What happened |
|---|---|
| Better than v1, by less than the practice gain | ✅ Barely: +0.01 on testing vs. +0.064 on practice. **Most of the practice gain didn't carry over.** |
| Gains in evidence preservation, tool use, receipts, clarification | 🟡 Evidence preservation up. Tool use and receipts flat. Clarification **down**. |
| Little change in booking evidence and policy outcome | 🟡 Booking evidence actually **improved** (+0.41). Policy outcome dipped (−0.10). |
| More tokens, P95 same or better | ✅ +38% tokens. P50 and P95 both **faster**. |

**What it means:**

- **The optimizer partly learned the test.** +0.064 on the questions it practiced on, +0.01 on new ones. The behavior examples copied from practice questions helped there and nowhere else. This is exactly why we keep a separate testing set.
- **It traded policy checking for evidence formatting.** Booking evidence and evidence preservation went up, but checking policy before recommending went down (−0.26), and so did the pass rate (82% → 75%). By our rule, "a version is only better if it keeps the policy decisions right," **v3 isn't ready to go live.**
- **Time constraints are still the soft spot.** The optimizer's practice run regressed on "EMP-001 can only fly after 8:00", and v3 regressed on T-19 ("can't fly before 8:00"). Neither v1's instructions nor v3's say how to handle a flight time window.
- **It's faster.** P50 down 1.6 s and P95 down 4.5 s. Clearer instructions cut wandering, even though each answer uses more tokens.

**Verdict: keep v1 live.** v3 is a sideways step: faster, better formatted evidence, slightly weaker policy checking. The climb continues. The next steps are a human edit that adds the missing rules, or another optimizer round from v3 on the practice-only set.

**Talk about it:**

- "The optimizer looked good on practice: +6 points. On new questions it's +1 point, and the pass rate dropped. That's why you never grade on the questions you practiced on."
- "It got faster and better at showing evidence, but slightly worse at checking policy before recommending. For Caldova, the policy check matters more, so v1 stays live."
- "This is where a person adds value: the optimizer found the formatting wins, and we can see exactly which two or three rules it's still missing."

### Step 11b. Put the optimized instructions on Model Router (v3-router)

> 🔀 **Spotlight: Model Router**, revisited

After v3 is built and scored, `bash infra/11-promote.sh router` runs v3's exact instructions on `model-router` (Balanced) and records it as **v3-router**. That's one change from v3: the model. Then `bash infra/07-score.sh run --label v3-router` and `bash infra/07-score.sh compare`.

**Why:** in Act 3, Balanced routing matched v1 on easy and medium questions at about a third of the cost, but fell down on hard, policy-heavy questions, where the weakness was in the instructions. If the optimizer fixes the instructions, this step tests whether the router can now keep quality *and* save money.

**What we expect:** hard-question quality close to v3's, at roughly v2's cost per answer.

**What happened:**

| | Result |
|---|---|
| New version | **v3-router = contoso-travel version 5** (`model-router`, config `cand_opt_6a599dcc…_0001-router`) |
| Deploy time | About 1 minute |
| Live version | Still v1. We confirmed with `bash infra/11-promote.sh go-live --label v1` |
| Smoke test (v3-router) | Called `check_travel_policy` for EMP-001, retried once after an empty first response, and reported no rule ID |
| Smoke test (v1, after go-live) | Same tool call and the same honest "no rule returned"; 8.2 s, response headers in 489 ms |

The smoke question has no departure date, so the policy tool has nothing to test against and returns no rule. Both versions said so instead of inventing a rule ID. That's the behavior we want.

Two `router` runs overlapped by accident. The second one deployed the same code (no new version), then stopped with `DeploymentActive` because the first run's web-app deployment was still going. It never reached the step that points the portal back at v1, so we ran `go-live --label v1` by hand. Nothing else was affected.

**Scores:** three rounds, **47 of 72 passed** (rounds 2 and 3: 15 and 17 of 24), then `bash infra/07-score.sh compare`:

| | v3 (optimized, `gpt-5.4`) | v2 (original instructions, router) | **v3-router (both)** |
|---|---:|---:|---:|
| Mean | **0.64** | 0.57 | 0.54 |
| Pass rate | **75%** | 65% | 65% |
| Easy / Medium / Hard | 0.66 / 0.67 / **0.58** | 0.66 / 0.58 / 0.45 | 0.61 / 0.59 / **0.43** |
| Weakest area | clarification (1.9) | booking evidence (2.0) | booking evidence (1.9) |
| P50 / P95 | **9.0 s / 14.4 s** | 12.6 s / 25.0 s | 14.1 s / 29.3 s |
| Tokens per answer | 6,612 | **5,969** | 8,371, the most of any version |

**Our prediction was wrong again.** We expected v3's quality at v2's cost. We got lower quality than either, and the most tokens of any version.

**Why, from the traces:**

1. **The optimizer tuned the instructions on `gpt-5.4`.** Every practice score came from `gpt-5.4`, so candidate 1 fits that model, not the mix the router picks.
2. **Longer instructions cost more on every call.** v3's instructions are 6 times longer than v1's, and the agent sends them with every pass through its tool loop. One answer takes 2 to 4 model calls, so the extra length adds up.
3. **On hard questions, the router's picks didn't trust their own tool results.** One trace ("Is Retiro Business in Madrid within Caldova's hotel policy?") shows it plainly:

   | Step | What happened |
   |---|---|
   | Tool call 1 | `search_hotels({"city": "MAD"})` returned **HT-016 Retiro Business, $195 + $16** |
   | Tool call 2 | The same call again, the same correct result |
   | Final answer | *"The inventory tool returned an error both times"*, so it couldn't check policy |

   The tool worked both times. The model said it failed. That's a faithfulness failure, and it's invisible in the score; only the trace shows it.

**Reading a trace like this:** the same question appears several times in one trace because each pass through the tool loop sends the full conversation again (the agent runs with `store: False`). Three passes means three model calls, and Model Router chooses the model for each one separately.

**Verdict: down. Keep v1.** Each lever was tuned for a specific model. Change the model, and you have to climb again.

**Talk about it:**

- "Better instructions plus a cheaper router should have been the best of both. It was the worst of both. Good steps don't automatically stack."
- "Look at this trace: the tool returned the right hotel twice, and the agent said the tool failed. The scorecard showed quality dropped. The trace showed why."

### Round 2: the teacher review found our tool bugs

> **Fine-tuning, from v3.** The plan: teach `gpt-4.1-mini` from v3's reviewed answers (`--teacher-label v3`), aiming for v3's quality at a fraction of the cost.

#### Step 11c. Ask the teacher, collect its answers

`bash infra/09-fine-tune.sh generate --teacher-label v3` asked v3 (version 4) all 48 training questions: **48 of 48 answered** in about 17 minutes. (The first try was cut off at question 43 when a command was typed into the running terminal. We reran it in full, so the review window holds one clean run.)

| Category | Outcomes |
|---|---|
| Planning (14) | 5 checked, 5 partial, 2 blocked, 1 unconfirmed, 1 not booked |
| Refusal (8) | 3 blocked, 2 checked, 2 error, 1 unconfirmed |
| Receipts (8) | 8 reimbursable |
| Accessibility (10) | 5 unconfirmed, 5 partial |
| Numbers (8) | 3 checked, 2 unconfirmed, 2 partial, 1 blocked |

`bash infra/09-fine-tune.sh harvest` then built the review sheet. Getting there exposed three gaps in how we turned traces into training examples, all fixed and tested:

| Gap | Why it mattered | Fix |
|---|---|---|
| Training examples kept only the question and the final answer | The student would see answers full of rule IDs and prices, but never the tool calls that fetched them, so it would learn to *sound* checked without checking | Each example now keeps the whole turn: tool calls, tool results, and the final answer, plus the agent's tool definitions |
| Tool results often had no call ID | The first harvest stopped with `KeyError: 'id'` | Results are paired with their calls in order |
| `gpt-5.4` sometimes wraps parallel calls in `multi_tool_use.parallel` | The student would learn to call a tool that doesn't exist | The wrapper is unpacked into the real calls (`search_flights`, `search_hotels`, …) |

#### What the review found

The review sheet now lists `tools_called` for every answer. Reading all 48 answers against the data showed most failures came from **our tools and data**, not from v3:

| Gap | What v3 did | Answers affected |
|---|---|---|
| **Paris flights use an airport code.** Flights listed Paris as `CDG`; every other city (and every Paris hotel and car) uses a city code like `PAR`. | Searched `SEA → PAR`, got nothing, and reported "no Seattle to Paris flights." There are 16. | 8 (TR-01, 02, 06, 07, 08, 12, 21, 45) |
| **No step-free filter.** Hotel search had only `wheelchair`. | Used `wheelchair` for "step-free" requests, got nothing, and said nothing matched. Four step-free hotels exist. | 4 (TR-33, 36, 38, 39) |
| **No price lookup by ID.** Given `FL-004`, the agent could only search by route. | Gave up honestly: "no pricing data was returned." | 3 (TR-41, 44, 46), plus a partial total in TR-48 |
| **A misleading `over_cap` flag in the hotel data.** Only 3 hotels had it, though more are over their city's cap. | Trusted the flag and called HT-002 ($368) within the Paris cap of $320. | TR-42, and likely T-03 in testing (Union Square Inn, $341; v3 scored 0.51 there, down from v1's 0.88) |

With those answers rejected, only about **25 of the 30 training answers** needed passed review, and the numbers category had 1 or 2 of the 4 it needs. We could have lowered the bar. We didn't: a student trained on these answers would learn to search the wrong city code and to give up on simple totals.

**This is the second time the review said "not good enough to teach":** v1 in Act 3, v3 now. Each time it pointed at the next thing to fix.

**Talk about it:**

- "Fine-tuning copies your teacher's habits, including its workarounds for your bugs. The review step is where you catch that."
- "The agent wasn't wrong to say 'no Paris flights.' Our data spelled Paris two different ways. No instruction can fix that."
- "Insights found the behavior, the scorecard measured it, the optimizer tuned the instructions, and reviewing the teacher's answers found the real limit: our tools."

#### Step 11d. Fix the tools (v3-tools)

Four fixes, each with a test (`.venv/bin/python -m pytest src/agent/tests -q`, 19 passed):

| Fix | Where |
|---|---|
| Flight, hotel, and car searches accept a city code, an airport code, or a city name (`PAR`, `CDG`, or `Paris`) | `src/agent/tools/search.py` |
| `search_hotels` has a `step_free` filter. Step-free still never counts as wheelchair-accessible, which T-08 and T-23 test | `src/agent/tools/search.py`, `definitions.py` |
| New `lookup_fixtures` tool returns prices by ID; hotels include the nightly total with taxes and fees | `src/agent/tools/search.py`, `definitions.py` |
| `over_cap` removed from the hotel data, so the policy tool is the only source of truth for caps | `data/fixtures/catalogs/hotels.json` |

**Versions already built are unaffected.** Each version packages the tools and data it was deployed with, so every score above stays valid. Only new deploys get the fixes.

**Built:** `bash infra/11-promote.sh tools` recorded **v3-tools as contoso-travel version 6** (`gpt-5.4`, the same config as v3). A quick check, "Which Seattle to Paris flights are in the fixtures?", now returns all four (FL-001, FL-002, FL-003, FL-017) with prices.

**What we expected:** a better T-03 (the cap now comes only from the policy tool), and otherwise close to v3.

**Results:** three rounds: **21, 19, and 19 passed out of 24** (59 of 72), the steadiest of any version. Then `bash infra/07-score.sh compare`:

| | v1 | v3 | **v3-tools** | v3-tools vs. v1 |
|---|---:|---:|---:|---|
| Mean | 0.63 | 0.64 | **0.66** | ▲ +0.03 |
| Pass rate | 82% | 75% | **82%** | same; recovers v3's drop |
| Easy / Medium / Hard | 0.66 / 0.60 / 0.63 | 0.66 / 0.67 / 0.58 | 0.63 / 0.66 / **0.70** | hard ▲ +0.07, the best of any version |
| Weakest area | booking evidence (2.0) | clarification (1.9) | clarification (**2.4**) | the floor is higher |
| P50 / P95 | 10.6 / 18.9 s | 9.0 / 14.4 s | **8.6** / 15.1 s | faster |
| Tokens per answer | **4,801** | 6,612 | 7,288 | ▲ +52% |

**Per dimension (1–5),** from the second table `compare` now prints:

| Dimension | v1 | v3 | **v3-tools** | v3-tools vs. v1 |
|---|---:|---:|---:|---:|
| `structured_booking_evidence` | 2.05 | 2.46 | **2.78** | **+0.73** |
| `missing_input_clarification` | 2.08 | 1.90 | 2.38 | +0.30 |
| `general_quality` | 3.35 | 3.43 | **3.58** | +0.23 |
| `evidence_preservation` | 3.47 | **3.81** | 3.68 | +0.21 |
| `receipt_classification_and_conversion` | 4.27 | 4.20 | **4.40** | +0.13 |
| `tool_usage_matches_request_type` | 4.04 | 4.03 | **4.14** | +0.10 |
| `policy_gated_outcome` | 3.47 | 3.37 | **3.55** | +0.08 |
| `policy_check_before_recommendation` | **3.90** | 3.63 | 3.82 | −0.08 |

**What it means:**

- **The first real step up.** Better mean, the same pass rate, and the best hard-question score of any version. Seven of eight dimensions improved on v1.
- **It passes our rule: the policy decisions held.** `policy_gated_outcome` went up. `policy_check_before_recommendation` recovered most of v3's drop (3.63 → 3.82) and sits within noise of v1's 3.90.
- **The tools were holding back the hardest requests.** v3 → v3-tools changed only the tools, and hard questions jumped from 0.58 to 0.70. Booking evidence, the weakest area on every model in Act 3, rose to 2.78, its best yet.
- **This time the steps stacked.** Optimized instructions plus fixed tools went up; optimized instructions plus a different model went down. Fixing real gaps compounds; swapping the model undoes tuning.
- **The trade-off is tokens.** About 52% more than v1 on the same model, from longer instructions and more tool use. That's the cost question fine-tuning or the router can take on next, now with a better teacher.
- **The trace analysis paid off.** No score pointed at the tools. Reading the teacher's traces did.

**Verdict: up.** v3-tools is the best version so far. We put it live with `bash infra/11-promote.sh go-live --label v3-tools`; the portal and default endpoint now use version 6. It's also the new fine-tuning teacher.

**Talk about it:**

- "We changed only the tools, and hard questions went from 0.58 to 0.70. The agent wasn't failing at reasoning; it was failing because our tools spelled Paris two ways and couldn't look up a price."
- "Nobody's scorecard said 'fix the tools.' Reading the traces did. That's why we look at traces, not just scores."
- "This is the first step up after five tries. Every step down told us where to look next, and this one is real: same questions, same scorecard, three rounds."

#### Step 11e. Fine-tune from v3-tools (v3-tools-student)

With better tools, the same teacher run tells a different story.

`bash infra/09-fine-tune.sh generate --teacher-label v3-tools` asked version 6 all 48 training questions: **48 of 48 answered** in about 16 minutes.

| Category | v3 (old tools) | v3-tools (fixed tools) |
|---|---|---|
| Planning (14) | 5 checked, 5 partial | **8 checked, 1 partial** |
| Accessibility (10) | 5 unconfirmed, 5 partial | 6 unconfirmed, **2 partial**, 1 blocked, 1 checked |
| Numbers (8) | 3 checked, 2 partial; 3 gave up on totals | **8 unconfirmed**: answered from `lookup_fixtures`, 1.4 tool calls each (was 2.8) |
| Refusal (8) | 3 blocked, 2 checked, 2 error, 1 unconfirmed | 3 checked, 2 blocked, 2 partial, 1 error |
| Receipts (8) | 8 reimbursable | 8 reimbursable |

"Unconfirmed" on the numbers questions is expected: they're arithmetic from looked-up prices, and the outcome label only tracks policy and receipt checks.

**The review passed this time:**

| | v3 teacher | **v3-tools teacher** | Needed |
|---|---:|---:|---:|
| Training answers accepted | about 25 | **36** | 30 |
| Validation answers accepted | — | **6** | 6 |
| Planning / Refusal / Receipts / Accessibility / Numbers | short on refusal and numbers | **12 / 4 / 7 / 7 / 6** | 8 / 4 / 4 / 5 / 4 |

- **All five totals questions checked out against the fixtures** ($3,461, $921, $674, $1,064, $1,874). Under v3, three of them gave up.
- **Step-free requests work:** TR-33, TR-36, and TR-39 found the step-free hotels with the new filter. Every `SEA → PAR` search returned flights.
- **Six answers rejected**, each for a bad tool call the student shouldn't copy: searching `*` or `BOS → BOS`, the wrong return leg, `hotel_id: "HT-???"`, and one that asked for the cap instead of checking policy.
- **Three refusals accepted at a lower score.** They decline correctly, but the policy tool didn't cite CT-11 for a blanket bypass without an employee. That's a policy-tool gap to look at next.

`bash infra/09-fine-tune.sh curate` built the files: **36 training and 6 validation examples, 41 of them with tool calls, 0 overlap with the testing questions.** Every example now shows the student which tools to call and what they returned, not just the final answer.

`bash infra/09-fine-tune.sh submit` started job `ftjob-…` on `gpt-4.1-mini` (3 epochs). The first `status` showed **"Job enqueued. Waiting for jobs ahead to complete,"** with an estimated finish about **8 hours** out. Global Standard training shares capacity, so the queue can take longer than the training itself. **Submit the day before** if you want a student ready for the session.

**The first job failed** after about 15 minutes in preprocessing: *"contains invalid schema"* on all 36 training lines. Every line, including the one with no tool calls, carried the same `tools` list, so the problem was the tool definitions. We had copied them straight from the agent's code, and they included extras the validator rejects (`title`, `default: null`, and `anyOf` with `null` for optional fields). Tool-call messages also carried `"content": null`. `curate` now writes plain schemas and leaves `content` out of tool-call messages, matching the [documented format](https://learn.microsoft.com/azure/foundry/openai/how-to/fine-tuning-functions). `submit` now starts a new job when the saved one failed. The resubmitted job passed preprocessing in about 4 minutes, with no schema errors.

**Talk about it:**

- "Same 48 questions, same review rules. With the old tools, the teacher couldn't pass review. With fixed tools, it passed with room to spare. Fix what the traces show you, then teach."
- "Every training example includes the tool calls. We're teaching the student to *check*, not just to sound like it checked."

_Training in progress._

---

## How this run ends: the story in one page

Use this as the close for this run. It follows [the README's punchline](README.md#close-the-punchline), with this run's numbers.

**What we learned at each act:**

1. **Make it work.** v1 found good options, but HERO wasn't booked and ACCESS skipped a policy check. The banner told the truth even when the reply sounded confident.
2. **Understand where it struggles.** 108 answers and 🔍 **Insights** turned two anecdotes into six patterns. The top one, "nothing blocked treated as approval", showed up in 45 traces.
3. **Make it better.** 📏 **Rubric Evaluator** turned those findings into a scorecard: every dimension traces back to a finding. 🔀 **Model Router** gave a clear answer: about 65% cheaper with no loss on easy requests, but weaker on hard, policy-heavy ones. Paying more for the strongest model made things *worse*. The weakness followed us across three models, so it wasn't the model.
4. **Make it scale.** ⚙️ **Agent Optimizer** tried three instruction rewrites in an hour and fixed four of the six findings, plus a formatting quirk. On practice questions it scored +6 points; on new questions, +1, with a lower pass rate. Putting those instructions on Model Router scored lower still. Then reviewing v3's answers for fine-tuning showed the agent working around four bugs in our own tools. Fixing them produced **v3-tools, the first version to beat v1**: 0.66 mean, 82% pass, and 0.70 on hard questions.

**For Krystal, Andre, and Lydia:**

- **Krystal** gets a version that keeps the policy decisions she depends on and handles hard requests better than v1: v3-tools, now live.
- **Andre** has defensible numbers: Model Router can cut cost by about two-thirds on simple requests, premium routing doubled cost for worse results, and the better version costs about half again as many tokens. Every claim comes from the same scorecard.
- **Lydia** has a process that caught four would-be regressions before they reached users, stopped a student from learning our bugs, and found the fix that finally went up.

**The punchline:**

> "We tried a cheaper model, a pricier model, an automated rewrite, and the rewrite on the cheaper model. None beat v1, and each told us why. When we went to teach a smaller model, reading the traces showed the agent working around bugs in our own tools. We fixed the tools, and for the first time we went up: better on hard requests, with the policy decisions intact. That's the playbook: measure every step, read the traces, and let each step down point to the next step up."

**What to do next, after the session:**

- **Fine-tune from v3-tools** (`bash infra/09-fine-tune.sh generate --teacher-label v3-tools`) to bring that quality to a cheaper model.
- **Run Insights again** on v3-tools (`bash infra/04-run-questions.sh --label v3-tools --repeats 1 --parallel 3`, then `bash infra/05-insights.sh --label v3-tools --lookback-hours 1`) to see which findings are gone.
- **Add the missing rules by hand:** "no decision isn't approval", "pass the policy result into the booking", and "respect stated time windows". Then score that version the same way.
- **If you want the router's savings,** put v3-tools on Model Router, or run the optimizer with Model Router as the target model, so the instructions are tuned for the model that will run them.

**Talk about it:**

- "Five steps down or sideways, then one clearly up. The scorecard stopped four regressions from going live, the review stopped a bad student, and the traces pointed at the fix."
- "Each Foundry feature did one job: Insights found the patterns, Rubric Evaluator measured them, Model Router showed where cheap is safe, and Agent Optimizer tried fixes at scale. Traces showed why. A person decided at every step."

---

## Lessons from this run

| What happened | What we changed |
|---|---|
| The question runner recorded every answer as an error. `azd ai agent invoke --output raw` returns an event stream, not one JSON document. | The runner now reads the final `response.completed` event. |
| A full exploring run takes a while one question at a time (about 20 s per answer). | Added `--repeats 2` and `--parallel N` to `bash infra/04-run-questions.sh`. |
| The first Insights scan failed with `TooManyRequests` at judge capacity 200. | `insights-judge` now deploys at 500; troubleshooting has the fix for existing environments. |
| Running `bash infra/05-insights.sh` again while a scan was active failed with "Run is already active." | It now waits for the active scan instead of starting another. |
| Saved findings still contained trace IDs. | IDs are now removed at every level; descriptions and example summaries are kept. |
| Scoring finished round 1, then stopped with a `jq` syntax error before recording it. `label` is a reserved word in `jq`. | Step 07 now uses quoted keys. Round 1 was recorded by hand, so only rounds 2 and 3 needed to run. |
| Each scoring command restarted at `-r1`, so separate batches showed duplicate round names. | Round numbers now continue across commands for the same label. |
| The first `bash infra/08-model-router.sh` said "Reusing v2" and then failed. `azd env get-value` prints "key not found" on standard output, so the error text was read as a version number. Nothing was deployed. | The scripts now keep an azd value only when the lookup succeeds. |
| v2 deployed, but switching the portal back to v1 failed with "Invalid format." After setup, the endpoint uses Foundry's default **Always use latest** (`@latest`), so v2 went live as soon as it was deployed, and the script tried to use `@latest` as a version number. | `@latest` now resolves to the real version number. We ran `bash infra/11-promote.sh go-live --label v1` once to put the portal back. After that the endpoint is pinned, so later deploys don't go live on their own. |
| `bash infra/10-optimize.sh status` returned `{"id": "", "status": ""}` even though the job was running. Passing `--project-endpoint` to `azd ai agent optimize status` returns an empty result. | Status now lets azd find the project itself, shows a readable summary, saves the full JSON to `status.json`, and supports `--watch`. |
| The optimizer practiced on all 36 exploring questions instead of the 12 practice rows. It ignores `max_samples`. | `submit` now writes a practice-only file (12 rows) and registers it as its own dataset, `brk330-practice`. The testing questions were never used either way. |
| `status` ended with `-s: command not found` and "Candidate files did not arrive in .agent_configs//". The script was edited while it was running, and bash reads scripts as it goes. Nothing was applied. | Don't edit a numbered script while it's running. Rerunning the command worked. |
| Two `bash infra/11-promote.sh router` runs overlapped. The second failed with `DeploymentActive` on the web-app deployment and stopped before switching the portal back to v1. | Run each numbered script once, in one terminal. If a deploy stops early, run `bash infra/11-promote.sh go-live --label v1` before scoring. Added to the instructions. |
| `azd ai agent optimize apply` also **overwrote v1's `baseline/instructions.md`** with the candidate's text. The cloud versions weren't affected (they can't be changed), but any later deploy using `baseline` would have used the wrong instructions. | Restored the baseline from git. `apply` now snapshots `.agent_configs/` first and puts back any existing folder it changed; the candidate keeps its own folder. Optimizer folders named after the job are ignored by git. |
| The first `generate` stopped at question 43. Activating the virtual environment in the same terminal sent an interrupt to the running script. | Leave a running script's terminal alone; the numbered scripts call `.venv/bin/python` directly, so activation isn't needed. We reran `generate` in full so the review window held one clean run. |
| After a Codespaces restart, `harvest` failed with a JSON error. The Azure CLI asked to reinstall its `log-analytics` extension, and the prompt landed in the saved trace file. | `harvest` now installs the extension without prompting. |
| Training examples kept only the question and the final answer, dropping every tool call. | Examples now keep the whole turn and the agent's tool definitions. Missing call IDs and `multi_tool_use.parallel` wrappers are handled. |
| The first fine-tuning job with tool calls failed in preprocessing: "contains invalid schema" on every line. The tool definitions came straight from the agent's code, with `title`, `default: null`, and nullable `anyOf`; tool-call messages had `"content": null`. | `curate` now writes plain JSON schemas and omits `content` on tool-call messages. `submit` starts a fresh job when the saved one failed. Rerun `curate`, then `submit`. |
| Reviewing v3's answers showed four tool and data gaps: Paris flights coded `CDG`, no step-free filter, no price lookup by ID, and an incomplete `over_cap` flag. | Fixed in `src/agent/tools/` and `data/fixtures/`, with tests. New versions get the fixes; existing versions keep what they were deployed with. Build `v3-tools` with `bash infra/11-promote.sh tools`. |
