# Optimize agents with Microsoft Foundry and GitHub Copilot

**Instructor guide, version 2**

This guide takes the Contoso Travel concierge from "it works" to "we know it's better, and we can keep making it better." Every step uses real Microsoft Foundry resources, so the results you see are your own.

> [!TIP]
> **Let GitHub Copilot walk you through it.** Ask: *"Walk me through instructions/README.md one step at a time. Explain each command before I run it and wait for my result."* You stay in control of anything that creates, changes, or deletes cloud resources.

> [!NOTE]
> **Want to see what a real run looked like?** [walkthrough.md](walkthrough.md) follows the same steps and shows the results, numbers, and talking points from a full run in East US 2.

## Four Foundry features take center stage

The whole session is built around four Microsoft Foundry features. Name them out loud when they appear.

| Feature | Act | What it does for us | Where you see it |
|---|---|---|---|
| 🔍 **Insights** | 2 | Reads many traces and groups repeated problems into plain-language findings. | Foundry → contoso-travel → **Insights** |
| 📏 **Rubric Evaluator** | 3 | Drafts a scorecard from v1's traces and the Insights findings, then grades every version the same way. | Foundry → **Evaluations** |
| 🔀 **Model Router** | 3 | One deployment that picks a suitable model per request. This is v2. | Foundry → **Models** → `model-router` |
| ⚙️ **Agent Optimizer** | 4 | Proposes instruction changes and tries them on practice questions. You review and decide. | Foundry → contoso-travel → **Optimize** |

They build on each other: **Insights** tells you *what* goes wrong, **Rubric Evaluator** turns that into *how to measure it*, **Model Router** is the first change you measure, and **Agent Optimizer** automates trying more changes. Fine-tuning (v2-alt) is a supporting comparison, not a hero.

## The story in one minute

Caldova's travel concierge has to be **right** (follow travel policy), **fast enough**, and **affordable**. Models and requirements keep changing, so "good" has to be measured, not assumed. We go through four acts:

| Act | The question | What you do |
|---|---|---|
| **1. Make it work** | Can we ship it? | Build and deploy the concierge on one strong model. This is **v1**. |
| **2. Understand where it struggles** | Where does it go wrong, and why? | Ask v1 lots of questions, read its traces, and let 🔍 **Insights** spot the patterns. |
| **3. Make it better** | Is a change actually better? | Turn what you learned into a scorecard with 📏 **Rubric Evaluator**, then try one change at a time (🔀 **Model Router**, then a fine-tuned model) and score each one the same way. |
| **4. Make it scale** | Can we keep improving without doing everything by hand? | Let ⚙️ **Agent Optimizer** suggest improvements. You review them, retest the best one, and decide what goes live. |

Behind all four acts is a simple loop: **look → understand → measure → change one thing → retest → decide → repeat.**

### The big idea: hill climbing

This is the thread that ties the whole session together. Come back to it in every act.

Imagine climbing a hill in fog. You can't see the top, so you can't plan the whole route. What you *can* do is:

1. **Know where you're standing.** That's v1's score.
2. **Take one step.** Change one thing: the model, the training, or the instructions.
3. **Check your altitude with the same instrument.** Same testing questions, same scorecard, same judge.
4. **Keep the step if you went up. Step back if you didn't.** Stepping back isn't failure; it tells you which way *not* to go.
5. **Repeat.**

```text
                                  v3 ?   (optimizer's suggestion, retested)
                                 /
               v2 ?  ----------+         (Model Router)
              /
   v1  -----+                            (where we start)
              \
               v2-alt ?                  (smaller trained model)
```

Every `?` is a question the scores answer, not something we know in advance. That's the point: **the winner isn't the takeaway, the climb is.** Models, prices, and requirements will change next month, and the same climb still works.

Map it to the acts:

| Act | Hill-climbing step |
|---|---|
| 1. Make it work | Get on the hill: a working v1. |
| 2. Understand where it struggles | Look around: which directions look promising? |
| 3. Make it better | Build the altimeter (the Rubric Evaluator scorecard), measure v1, take two single steps (v2, v2-alt), and keep the one that goes up. |
| 4. Make it scale | Let the optimizer take steps for you, then check each one with the same altimeter before you move.

## Words we use

| Word | What it means here |
|---|---|
| **Version** | Every change creates a new, unchangeable copy of the agent. Old versions stay available, so you can always switch back. |
| **Label** | A friendly name for a version: **v1**, **v2**, **v2-alt**, **v3**. The scripts remember which version number each label points to. |
| **Trace** | A step-by-step record of one answer: which tools the agent called, what came back, how long it took, how many tokens it used. |
| **Insights** | A Foundry feature that reads many traces and groups repeated problems into findings in plain language. |
| **Scorecard** | Our name for the **Rubric Evaluator** we build in Act 3: a checklist of weighted dimensions (for example, "right policy decision" and "numbers add up") used to grade every answer. Foundry drafts it from v1's traces; you review it. |
| **Judge** | The model the Rubric Evaluator uses to apply the scorecard to each answer (`gpt-5.4-mini`). |
| **Model Router** | One deployment that picks a suitable model for each request. |
| **Fine-tuning** | Teaching a smaller model by showing it good examples, here reviewed v1 answers. |
| **Agent Optimizer** | A Foundry feature that tries several instruction changes and reports how each did on practice questions. |

## Three sets of questions

If you study with the exam questions, your grade means nothing. So the questions are split by job and never overlap. See [`data/README.md`](../data/README.md) for details.

| Set | How many | Job | Used in |
|---|---:|---|---|
| **Exploring** | 36 (12 easy, 12 medium, 12 hard) | Learn how v1 behaves. The first 12 are **practice** questions, including the four portal scenarios. | Act 2, the scorecard draft, and the optimizer's practice |
| **Training** | 48 | Collect good v1 answers to teach the smaller model. | Act 3, fine-tuning |
| **Testing** | 24 (8 easy, 8 medium, 8 hard) | Grade every version. New cities and receipts that appear nowhere else. | Act 3 and Act 4 scoring only |

## The versions you'll build

| Label | What changed from v1 | Model | Built by |
|---|---|---|---|
| **v1** | Nothing; the starting point | `gpt-5.4` | `infra/02-setup.sh` |
| **v2** | The model: Model Router picks one per request (Balanced routing) | `model-router` | `infra/08-model-router.sh` |
| **v2-quality** | The model: Model Router in Quality routing mode | `model-router-quality` | `infra/08-model-router.sh --mode quality` |
| **v2-alt** | The model: a smaller model trained on v1's best answers | `contoso-student` | `infra/09-fine-tune.sh` |
| **v3** | The instructions, suggested by Agent Optimizer and reviewed by you | Same as the version you optimized | `infra/11-promote.sh` |
| **v3-router** (optional) | v3's instructions on Model Router: one change from v3 | `model-router` | `infra/11-promote.sh router` |
| **v3-student** (optional) | v3's instructions on a small model fine-tuned from v3's answers: one change from v3 | `contoso-student-v3` | `infra/09-fine-tune.sh --teacher-label v3` |
| **v3-tools** (optional) | v3's instructions and model with fixed tools and data: one change from v3 | Same as v3 | `infra/11-promote.sh tools` |
| **v3-tools-student** (optional) | v3-tools on a small model fine-tuned from v3-tools' answers: one change from v3-tools | `contoso-student-v3-tools` | `infra/09-fine-tune.sh --teacher-label v3-tools` |

v2 and v2-alt both start from v1 and change **one thing each**, so you can tell what made the difference. The portal keeps using v1 until **you** switch it.

### How versions and the endpoint fit together

It helps to picture three pieces in Foundry:

```text
contoso-travel (the agent)
 ├─ endpoint ── one stable URL; the "active version" setting decides who answers
 ├─ version 1  (v1, gpt-5.4)
 ├─ version 2  (v2, model-router)
 └─ version 3… (each deploy adds one; none are overwritten)
```

- **A deploy adds a new version, not a new endpoint.** Each version is an unchangeable snapshot (model, instructions, config). All versions live under the same agent and stay in the cloud until you delete them.
- **Version numbers aren't labels.** Foundry numbers versions in deploy order (1, 2, 3, …). Labels name what changed. If you build v2-quality before v3, Foundry calls v2-quality "version 3". The scripts always use labels.
- **The endpoint is one stable URL.** It's live from the moment the agent exists, and it doesn't change as you add versions. Its **active version** setting sends all default traffic to one version. Foundry doesn't split traffic between versions.
- **Going live means changing the active version.** `infra/11-promote.sh go-live --label v2` (or `--activate` on steps 08 and 09) points the endpoint at that version. The portal, and any app that calls the endpoint without naming a version, follows it. You can do the same in Foundry under **Details → Active version**. Out of the box, Foundry uses **Always use latest**, so right after setup a new deploy would go live immediately. Steps 08, 09, and 11 switch the portal back to the version that was live and pin it there, so from then on a new deploy never goes live by accident.
- **Other versions stay reachable from code.** Any active version can be called directly by number without changing what the portal uses. That's how every script here works: questions, scoring, and smoke tests all call `azd ai agent invoke --version N`, so you can test v2 while the portal keeps serving v1.
- **Switching back is instant.** Nothing is rebuilt; only the active-version setting changes. Start a new portal conversation after a switch.

## Before you start

- An Azure subscription with billing, and permission to create resources and assign roles.
- Quota in **East US 2** for the five models setup deploys (preflight checks this for you; see [`infra/README.md`](../infra/README.md#models-and-capacity)).
- Agent Optimizer preview access for Act 4.
- This repo open in GitHub Codespaces or the dev container.

Run every command from the repository root. Everything these scripts make (answers, traces, review sheets, scores, job IDs) is saved under `.azure/<environment>/`, which is never committed.

> [!IMPORTANT]
> These steps create resources that cost money until you delete them. Step 12 cleans everything up.

## What to do ahead of time

Most steps involve waiting on the cloud. Do them the day before so the session is all about the story.

| When | Steps | Result |
|---|---|---|
| **The day before** | 01 → 09 | v1, v2, and v2-alt built; traces, Insights findings, scorecard, and scores ready |
| **A few hours before** | 10 `submit` | Optimizer candidates waiting for review |
| **On stage** | Portal, Foundry, `bash infra/07-score.sh compare`, `bash infra/10-optimize.sh status`, `bash infra/11-promote.sh` | You show and explain; nothing long-running |
| **After** | 12 | Everything deleted |

---

## Act 1: Make it work

### Before the session

**Step 1. Build everything.**

```bash
bash infra/02-setup.sh
```

Setup checks the repo first (it runs `infra/01-validate.sh` for you), signs you in only if you aren't already, and suggests your current subscription and `eastus2`. Press Enter to accept, then confirm. It then:

- checks that every model and enough quota are available before creating anything;
- creates a fresh resource group named `rg-aitour-brk330-NNNNNN`;
- deploys all five models, so nothing needs deploying by hand later;
- deploys the concierge as **v1** and the portal.

When it finishes, it prints the portal URL and the environment name (`brk330-NNNNNN`). If it stops partway, it prints a resume command that reuses the same environment.

**Step 2. Check that everything is healthy.**

```bash
bash infra/03-check.sh
```

You want `Deployment validation: READY`. Add `--verbose` to see the details: models, agent, portal health, permissions, and recent traces.

### During the session

Open the portal and run the four sample scenarios. The banner at the top of each answer is worked out from what the tools actually returned, not from what the agent says, so it can disagree with an upbeat reply. That's useful: it's the first hint about where v1 struggles.

| Scenario | What a good answer does | What you'll likely see from v1 |
|---|---|---|
| **BLOCK** | Refuses a "just approve everything" request, cites CT-11, and points to the normal approval path. | **Not approved — blocked by Caldova policy.** |
| **EVIDENCE** | Reads a French parking receipt and converts EUR 117.00 to USD 126.36 at 1.08. | **Reimbursable — receipt meets Caldova policy.** |
| **HERO** | Plans a full Paris trip within policy and passes the policy result to the dry-run booking. | Often **Not booked — the booking step did not go through.** The plan looks great, but the booking was missing its policy proof. |
| **ACCESS** | Finds the wheelchair-accessible hotel and hand-control car, and says no flight leaves after 8:00. | Often **Partly done — nothing matched some of the requirements.** Check whether the reply says that clearly or glosses over it. |

> **Say this:** "It works. We're on the hill. But does it work *every* time, and do we know *why* when it doesn't? One run can't tell us. Let's ask it a lot of questions."

---

## Act 2: Understand where it struggles

> 🔍 **Spotlight: Insights.** One answer tells you little. Insights reads a hundred and tells you which problems keep coming back.

### Before the session

**Step 3. Ask v1 the exploring questions, three times each.**

```bash
bash infra/04-run-questions.sh
```

By default this asks **v1** all 36 exploring questions **3 times each**, each in a fresh conversation pinned to v1, so the portal is never switched. Asking more than once matters: a single run might be lucky or unlucky, while three runs show what v1 *usually* does. The script saves every answer, timing, and outcome, and prints a short summary by level (easy, medium, hard).

Want a quick try first? Add `--limit 4 --repeats 1`.

Short on prep time? Use `--repeats 2`. Each question still gets more than one answer, which is enough for Insights and the scorecard, and the run is a third shorter. You can also add `--parallel 3` to ask three questions at once; it finishes much sooner, and timings get a little noisier because answers share model capacity. Expect roughly 20 seconds per answer one at a time, so the default 108 answers (36 × 3) take a while; start it and come back.

**Step 4. Let Insights read the traces.**

Wait a few minutes for the traces to arrive, then run:

```bash
bash infra/05-insights.sh
```

This starts one Insights run over the last 3 hours of traces, using the `insights-judge` model that setup already deployed. It prints the findings and saves them (without any IDs) so the next step can use them. If your questions ran longer ago, add `--lookback-hours 6`.

### During the session

1. In Foundry, open **contoso-travel → Traces**. Pick one HERO trace and walk through it: the tool calls, the policy check, the booking attempt, and what came back.
2. Open **Insights**. Read the findings aloud and point out how many traces each one covers. The [walkthrough](walkthrough.md#step-4-let-insights-read-the-traces) shows six findings from a full run, led by "absence of a policy block was misinterpreted as affirmative authorization" across 45 traces.

   Your wording may differ. Report what *your* run found.
3. Show the summary from step 3 (`.azure/<env>/questions/exploring-v1-*.md`): how speed and tokens grow from easy to hard questions.

> **Say this:** "Now we know *where* it struggles, so we know which directions might be uphill. But before we take a step, we need an altimeter: a way to tell whether a change actually helped."

---

## Act 3: Make it better

> 📏 **Spotlight: Rubric Evaluator.** Turns what Insights found into a scorecard that grades every version the same way.
>
> 🔀 **Spotlight: Model Router.** The first change we measure: let Foundry pick the model per request.

### Before the session

**Step 5. Build the scorecard with Rubric Evaluator.**

```bash
bash infra/06-scorecard.sh
```

This uploads the exploring and testing questions to Foundry, then asks **Rubric Evaluator** to generate the scorecard (`brk330-travel-scorecard`) from four sources together:

- v1's actual traces from step 3;
- the v1 agent itself;
- the exploring questions and what a good answer to each looks like;
- our guidance ([`data/scorecard-guidance.json`](../data/scorecard-guidance.json)) plus the Insights findings from step 4.

The draft is saved under `.azure/<env>/scorecard/`. **Read it.** Each line should sound like something Caldova cares about (the right policy decision, checking before recommending, honest about gaps, numbers that add up), not generic "helpfulness." If a scorecard already exists, the script reuses it, so every version is graded exactly the same way.

In Foundry you'll see **"Generated with input-quality warnings: The agent has no instructions."** That's expected. Rubric Evaluator can't read a hosted agent's instructions because they're packaged with its code, so the script passes the instructions and policy in the prompt source instead. If the dimensions are Caldova-specific, the warning is cosmetic; don't regenerate to get rid of it.

**Step 6. Score v1.**

```bash
bash infra/07-score.sh run --label v1
```

This grades v1 on the **24 testing questions**, three times, with the Rubric Evaluator scorecard and the `gpt-5.4-mini` judge. v1 has never seen these questions; they use cities and receipts that appear nowhere else.

**Step 7. Build and score v2 with Model Router.**

```bash
bash infra/08-model-router.sh
bash infra/07-score.sh run --label v2
```

Same instructions, same tools. The only change is that Model Router picks the model for each request. The portal stays on v1.

**Step 7b (optional). Try Model Router in Quality mode.**

The default **Balanced** mode picks the cheapest model that's close in quality. If v2 is cheaper but scores worse on hard questions, try **Quality** mode, which picks the strongest model for each prompt:

```bash
bash infra/08-model-router.sh --mode quality
bash infra/07-score.sh run --label v2-quality
```

This creates a second router deployment, `model-router-quality` (capacity 300), and one agent version that uses it, labeled **v2-quality**. It's still one change from v1: only the model choice. See [walkthrough step 7](walkthrough.md#step-7-build-and-score-v2-with-model-router) for why we tried it.

**Step 8. Build and score v2-alt, the fine-tuned smaller model.**

This one has a few steps because a person has to approve what the model learns from.

> **Pick the teacher first.** A student can only be as good as the answers it learns from. If v1's main weakness is in its instructions (as in our run, where booking evidence scored about 2/5 on every model), few of v1's hard answers will pass review, and the student learns mostly easy cases. In that case, do Act 4 first and use the improved **v3** as the teacher: add `--teacher-label v3` to `generate`, and the student becomes **v3-student** instead of v2-alt. Later phases remember the teacher.
>
> **Then check how the teacher used its tools.** The review sheet lists `tools_called` for every answer. If many answers fail for the same tool reason (an empty search that shouldn't be empty, a price the agent couldn't look up), fix the tools first, build **v3-tools** (Act 4, step 7), and teach from that: `--teacher-label v3-tools`. A student copies its teacher's workarounds along with its answers.

```bash
bash infra/09-fine-tune.sh generate   # ask the teacher (v1 by default) the 48 training questions
```

Wait a few minutes for traces, then:

```bash
bash infra/09-fine-tune.sh harvest    # collect the teacher's answers into a review sheet
```

Now **review**. Open `.azure/<env>/fine-tune/<teacher>/traces.review.jsonl`. Category and split are already filled in. For each answer you'd be happy to teach:

- set `accepted` to `true`;
- give it a `rubric_score` of 0.5 or higher;
- tick all five checks in `hard_gates` (right policy decision, checked before recommending, no made-up rule citations, totals add up, everything came from the tools);
- write a short `review_reason`.

You need at least 30 training and 6 validation answers, spread across all five categories. If the teacher got a question wrong, leave it out; teaching a mistake makes the student worse. Then:

```bash
bash infra/09-fine-tune.sh curate     # check your review and build the files
bash infra/09-fine-tune.sh submit     # start the training job
bash infra/09-fine-tune.sh status     # check on it later
bash infra/09-fine-tune.sh deploy     # once it says succeeded
bash infra/09-fine-tune.sh agent      # create v2-alt (or v3-student)
bash infra/07-score.sh run --label v2-alt    # or: --label v3-student
```

The testing questions are never used for training; the curate step refuses to continue if one slips in. The student keeps its teacher's instructions and changes only the model, so it's one step from the teacher.

> **Good to know: teaching a tool-using agent from its traces.** A student only learns to *use* tools if its training examples include the tool calls and their results, not just the final answers. `curate` builds every example that way, in the format Azure fine-tuning accepts for tool calling: the tool definitions on every row, `"parallel_tool_calls": true`, plain JSON schemas where every object has `properties` and `required` (even if empty), no `content` on tool-call messages, and tool results placed right after the call that asked for them. If a job fails in preprocessing with **"contains invalid schema"** on every line, the problem is the shared parts of each row (the `tools` list and its schemas), not your examples. Compare your file with the Foundry team's [fine-tuning repo](https://github.com/microsoft-foundry/fine-tuning), which has a trace-to-SFT transform script and a working tool-calling sample. Preprocessing takes a few minutes once the job starts, so check `status` soon after `submit`, not hours later.

**Step 9. Compare.**

```bash
bash infra/07-score.sh compare
```

You get one table with each version's average score, its change from v1, the pass rate, scores for easy, medium, and hard questions, its weakest area, speed (typical and slowest), and average tokens.

### During the session

1. Show the **Rubric Evaluator** in Foundry (**Evaluations → Evaluators → `brk330-travel-scorecard`**). Walk through its dimensions and point out that each one traces back to an Insights finding, not a generic template.
2. Show v1's score on the testing questions. Explain that the testing questions are new to every version.
3. Show the **Model Router** deployment in Foundry (**Models → `model-router`**) and explain v2 (one change: the model). Then v2-alt (one change: a smaller, trained model).
4. Show the comparison table and talk through it:
   - **Better quality** is only better if the policy decisions stay right. Check the weakest area.
   - **Faster or cheaper** is a win only when quality holds.
   - **Keeping v1** is a perfectly good outcome.

   Then **tell it as a climb**: put v1's score on the board as "where we stand," then show v2 and v2-alt as two possible steps. Say which one went up, which one went down, and what that teaches you. A step that went down is still useful: you now know not to go that way for this workload.
5. When you've picked a version, switch the portal to it:

   ```bash
   bash infra/11-promote.sh go-live --label v2
   ```

   Start a new conversation in the portal to see it.

> **Say this:** "We just did one step of hill climbing by hand. We knew where we stood, took one step at a time, measured with the same instrument, and kept only what went up. It works, but every step took us a lot of effort. What if we could take more steps, faster, without giving up control?"

---

## Act 4: Make it scale

> ⚙️ **Spotlight: Agent Optimizer.** Tries instruction changes for you, measured with the same Rubric Evaluator. You stay the decision maker.

### Before the session

**Step 10. Let Agent Optimizer try instruction changes.**

Start from the best-scoring version in Act 3. In our run that was v1 (see the [walkthrough](walkthrough.md#step-10-let-agent-optimizer-try-instruction-changes)):

```bash
bash infra/10-optimize.sh submit --from-label v1
```

The optimizer proposes three instruction changes and tries each on the **12 practice questions**, never on the testing questions. That keeps the testing questions a fair final check. It grades each candidate with the same Rubric Evaluator scorecard, so its suggestions aim at the same dimensions Insights pointed to. The script records the job; check it with:

```bash
bash infra/10-optimize.sh status            # one look
bash infra/10-optimize.sh status --watch    # keep checking until it finishes
```

The job runs in Foundry, so you can close the terminal and come back. You'll also find it in Foundry under **contoso-travel → Optimize**.

### During the session

1. Show the optimizer job in Foundry, or the `status` output: three candidates, each with a practice score.

   > **The optimizer will recommend a shortcut, and we take a different path on purpose.** It stars its best candidate and suggests `azd ai agent optimize apply --candidate <ID>` followed by `azd deploy`. Foundry also shows a **Deploy best candidate** button. Both put the candidate straight into a new version. We don't use them, for three reasons:
   >
   > - **A practice score isn't proof.** The star is based on the practice questions. We want the candidate scored on the 24 testing questions, alongside v1 and v2, before anyone decides.
   > - **Nothing should go live by accident.** Our scripts deploy the candidate as a labeled version (v3) and keep the portal on whatever version it was using.
   > - **A plain `azd deploy` would run the old instructions.** In this repo, each version picks its config folder from `CONTOSO_CONFIGURATION`, which is still `baseline`. A plain `azd deploy` would create a new version with v1's instructions and rebuild the portal too. `bash infra/11-promote.sh deploy` sets the right config just for that deploy, then sets it back.
   >
   > We still use the same `optimize apply` command to download the candidate's files. Only the deploy step is different. Foundry still tracks it: the optimizer job page shows **"Promoted: v<N>"** and links the new version back to the run. In Foundry, "promoted" means *became a version*, not *went live*.

2. Pick the candidate you trust and download it:

   ```bash
   bash infra/10-optimize.sh apply --candidate <candidate-id>
   ```

   Open `src/agent/.agent_configs/<candidate-id>/instructions.md` next to `src/agent/.agent_configs/baseline/instructions.md` and talk through what changed. Ask out loud: does this make sense for Caldova? Would I sign off on this? A good check: **which Insights findings does this change address?** (The walkthrough has a [checklist](walkthrough.md#which-insights-findings-the-optimizer-can-address).)
3. Turn it into **v3** and retest it on the testing questions:

   ```bash
   bash infra/11-promote.sh deploy --candidate <candidate-id>
   bash infra/07-score.sh run --label v3
   bash infra/07-score.sh compare
   ```

4. Decide. If v3 is better on the testing questions *and* keeps the policy decisions right, put it live:

   ```bash
   bash infra/11-promote.sh go-live --label v3
   ```

   If not, keep what you have. That's the system working, not failing.

5. **Optional: put the improved instructions back on Model Router (v3-router).** If Model Router was cheaper but weaker in Act 3, the weakness may have been the instructions, not the router. Now that v3 has better instructions, try them on Model Router. It's one change from v3, the model:

   ```bash
   bash infra/11-promote.sh router
   bash infra/07-score.sh run --label v3-router
   bash infra/07-score.sh compare
   ```

   If v3-router keeps v3's quality at a lower cost, that's the best of both levers: better instructions *and* a cheaper model mix.

   The `router` command finishes by pointing the portal back at the live version. Run it once, in one terminal. If it stops early (for example, `DeploymentActive` because another deploy is still going), put the live version back before scoring:

   ```bash
   bash infra/11-promote.sh go-live --label v1
   ```

   The smoke test question doesn't give a departure date, so "no lead-time rule returned" is a normal answer there, not a failure.

6. **Optional: check with Insights again.** The scorecard tells you *how much* better v3 is. Insights tells you *which problems went away*. Ask v3 the exploring questions once, then run a short Insights scan over just those traces:

   ```bash
   bash infra/04-run-questions.sh --label v3 --repeats 1 --parallel 3
   bash infra/05-insights.sh --label v3 --lookback-hours 1
   ```

   Start the scan right after the questions finish, so the 1-hour window holds only v3's traces. Findings save to `findings-v3.json`, next to v1's. Compare the two lists: which findings disappeared, which shrank, which remain. One pass is enough here; Insights was the most expensive step in our run.

7. **Optional: fix the tools, then teach (v3-tools).** Instructions can only do so much. If traces or the fine-tuning review show the agent working around a tool (an empty search for a city that has inventory, a total it can't compute because it can't look up a price), fix the tool or the data in `src/agent/tools/` or `data/fixtures/`, run the tests, then build v3 again with only the tools changed:

   ```bash
   .venv/bin/python -m pytest src/agent/tests -q
   bash infra/11-promote.sh tools
   bash infra/07-score.sh run --label v3-tools
   bash infra/07-score.sh compare
   ```

   Versions already built keep the tools they were deployed with, so earlier scores stay valid. If v3-tools holds up, use it as the fine-tuning teacher (step 8 with `--teacher-label v3-tools`). The [walkthrough](walkthrough.md#round-2-the-teacher-review-found-our-tool-bugs) shows the four tool gaps our run found this way.

> **Say this:** "This is the same climb, automated. The optimizer proposes the steps and tests them on practice questions. We check each one with the same altimeter, the testing questions, before we move. The optimizer does the trying. A person does the deciding."

---

## Close: the punchline

Wrap up by bringing it back to the three people from the start:

- **Krystal** gets a concierge that keeps the policy decisions right, because no version goes live unless those decisions hold.
- **Andre** gets numbers he can defend: quality, speed, and cost, measured the same way for every version.
- **Lydia** gets a process, not a one-off fix. When a new model ships next month, she takes one more step up the same hill.

Then deliver the line:

> **Say this:** "You didn't come here to learn which model won today. That will change. You came to learn the climb: know where you stand, take one step, measure it the same way, keep it only if it goes up, and let automation take more steps while a person decides. That's the playbook."

Your results will differ from run to run. Here's how to tell the story whatever happens:

| What your scores show | How to tell it |
|---|---|
| v2 (Model Router) went up | "Letting the router pick the model helped on this workload. One step, kept." |
| v2-alt went up, or held quality at lower cost | "A smaller model taught from our best answers kept up. Andre likes this one." |
| Both went down | "Two steps, both down. We stay on v1 and we *know* why. That's the fog clearing." |
| v3 went up | "The optimizer found a better step, and we checked it before trusting it." |
| v3 didn't beat what we had | "A higher practice score didn't hold on new questions. That's exactly why a person retests before going live." |
| v3-router went down | "Two good ideas don't automatically stack. Instructions tuned for one model need retesting on another." |
| v3-tools went up | "The traces showed the agent working around our tools. We fixed the tools, changed nothing else, and went up." |
| The teacher's answers failed review | "Fine-tuning would have copied the teacher's workarounds. The review showed us the tools to fix first." |

Every row is a good ending. The only bad ending is skipping the measurement.

---

## Clean up

```bash
bash infra/12-teardown.sh
```

It shows the resource group and asks you to type its full name, then asks once more before it deletes and purges everything.

## If something goes wrong

| What you see | What to do |
|---|---|
| Setup stops partway | Rerun the resume command it prints (`bash infra/02-setup.sh --suffix NNNNNN`). |
| `infra/03-check.sh` says a model is missing | Rerun setup with the same suffix; it fills in what's missing. |
| Insights can't start | Rerun `bash infra/03-check.sh`, make sure step 3 ran recently, then try `bash infra/05-insights.sh --lookback-hours 6`. |
| A step says a label "has not been built yet" | Run the step that builds it (see [The versions you'll build](#the-versions-youll-build)). |
| Rate-limit errors while asking questions | Wait a minute and rerun; each run saves its own time window, so partial runs don't get mixed in. |
| The portal shows the wrong version | `bash infra/11-promote.sh go-live --label <label>`, then start a new conversation. |

More detail is in [`docs/troubleshooting.md`](../docs/troubleshooting.md).

## Where things live

| Folder | What's there |
|---|---|
| [`infra/`](../infra/README.md) | The numbered scripts, in order. |
| [`data/`](../data/README.md) | Fixtures, the three question sets, scorecard guidance, and fine-tuning review rules. |
| [`src/agent/`](../src/agent/README.md) | The concierge and its per-version configs. |
| [`src/web/`](../src/web/README.md) | The portal. |
| [`docs/`](../docs/README.md) | The full story, technology status, and troubleshooting. |
