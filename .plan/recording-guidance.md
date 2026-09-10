# Recording guidance — BRK330 Contoso Travel Concierge

Everything the presenter needs to reproduce the recorded demo end-to-end, including gotchas we hit on the first run, the exact terminal commands, on-camera talk-tracks, and rollback paths when a step misbehaves.

Read alongside:
- `.plan/quick-prompt-sequence.md` — the P0–P15 kickoff prompt list
- `.plan/demo-1.md` / `demo-2.md` / `demo-3.md` — narrative beats per demo
- `.plan/session-log.md` — decisions made during the first recording pass
- `data/evaluation/results/comparison-tracker.md` — the numeric receipts table

If you diverge from this playbook, update it — the goal is reproducible for a second speaker.

---

## Preflight — before you hit record

### 0.1 Environment (5-minute check)

Run from repo root:

```bash
pwd
ls azure.yaml src/agent/.foundry/metadata.yaml src/agent/.foundry/instructions.md src/agent/eval.yaml
azd version && azd ai version
azd env get-values 2>/dev/null | awk -F= '{print $1, ($2==""?"(empty)":"(set)")}' \
  | grep -Ei "PROJECT|AGENT|FOUNDRY|AI_|AZURE_ENV_NAME|AZURE_RESOURCE_GROUP|AZURE_SUBSCRIPTION_ID"
az account show --query "{sub:name, tenant:tenantId}" -o table
git status --short && git branch --show-current
```

Expected:
- All four files present. `azure.yaml` is at **repo root**, not under `src/agent/`.
- `azd` ≥ 1.32.0; `azd ai` extension ≥ beta.14.
- These env vars all `(set)`: `AZURE_ENV_NAME`, `AZURE_RESOURCE_GROUP`, `AZURE_SUBSCRIPTION_ID`, `AGENT_CONTOSO_TRAVEL_NAME`, `AGENT_CONTOSO_TRAVEL_PROJECT_ENDPOINT`, `AGENT_CONTOSO_TRAVEL_VERSION`.
- Tenant matches your Foundry account (for this session: `ai-team`).
- Git tree clean or only expected pending edits.

### 0.2 Live Azure state prerequisites

Before recording Demo 3, confirm the following are already provisioned from Demo 1–2:

| Resource | Location | Purpose |
|---|---|---|
| RG `rg-brk330-concierge` | Sweden Central | Container |
| Foundry account `cog-hqxztqzboq4bq` | inside RG | AI Services |
| Foundry project `brk330-concierge-project` | inside account | Agents home |
| Model deployments | GS 500 cap each | `gpt-5`, `gpt-4.1`, `model-router`; DeveloperTier 100 for `contoso-student` |
| Agent versions | `contoso-travel` | v6 baseline, v8 routed, v9 student — must exist before optimizer runs |
| App Insights | `appi-brk330-nxzzad4sd6dl6` | Set `isSharedToAll: true` — required by Foundry portal Monitor tab |
| Container app | `contoso-web` | FastAPI web demo |
| Custom evaluator | `caldova-agent-rubric-eval` | Registered in Foundry portal, version 2 pinned in eval.yaml |

If any of these are missing, back up to the appropriate P-prompt and rebuild them before continuing.

### 0.3 Terminal + display setup

- **Font size ≥ 14pt** so commands are legible on recorded video.
- **Shell:** zsh. Comment lines (`# something`) inside multi-line pastes cause `zsh: command not found: #` errors — split multi-command blocks into one command per paste, or drop the comments.
- **Two windows open:** the Copilot CLI/terminal panel (left) and Foundry portal (`https://ai.azure.com`, right).
- **Do NOT** run any commands with secrets echoed. The env-check script above uses `(set)`/`(empty)` masking specifically for this.

---

## Global talk-track patterns

Use these phrasings — they were the ones that landed cleanly on the first pass.

**When opening the portal after a CLI action:** *"The portal is the reviewer's dashboard, not the launcher. Everything we run here is driven from `azd` so it's reproducible in CI."*

**When showing a diff:** *"This is what makes AI-driven optimization safe — every change is a human-readable git diff, not a black box."*

**When showing per-candidate scores:** *"More than one viable tradeoff — quality-optimal versus cost/latency-optimal. The human picks, not the model."*

**When something regresses:** *"The Optimizer scored a lift on our rubric. The smoke test caught a regression the rubric didn't measure. Rolling back — this is why human-in-the-loop matters."*

Avoid:
- "Publication blocker", "focused Markdown diagnostics", "local hypothesis" — sounds like QA, not a session.
- Narrating tool invocations ("I'm going to run edit now…"). Say what you're proving, not what tool you're using.

---

## Session 1 — Build the baseline (Demo 1) — P0–P6

Straightforward — mostly Copilot-driven. Two gotchas from the first pass:

### Reasoning-content SDK bug (affects Demo 2 + 3)

gpt-5 emits `content.type: "reasoning"` in assistant messages. Foundry evaluators (`intent_resolution`, `task_adherence`, `tool_call_accuracy`) reject these. The fix is baked into `src/agent/main.py`:

```python
default_options={"reasoning": {"summary": None}, "include": []}
```

Do not remove this. If the agent starts returning empty responses in eval, this is the first thing to check.

### Description length limit

Foundry hosted agent `description` is capped at **512 characters**. Auto-generated rubrics read this field for context, so keep it concise but content-rich. The current 456-char description is at the sweet spot.

### RBAC gotchas

- Web MI needs `Cog Svcs User`, `OpenAI User`, `Foundry User` at **project scope** — account-scope inheritance doesn't work.
- Project MI needs the same three roles at **account scope** for the Foundry portal Monitor tab to work.
- App Insights connection must have `isSharedToAll: true` — set via full-envelope PATCH, not partial PUT.

All of the above are already in `infra/supplemental.bicep`. If you re-provision from scratch, verify the Monitor tab loads before proceeding to Demo 2.

---

## Session 2 — Hill-climb (Demo 2) — P7–P12

### P7 — Custom rubric

- Use the portal auto-generate wizard with **65 traces + agent context + `data/policy/rules.json` + `data/evaluation/rubric-foundry.json`** as context files.
- **First generation warns "no agent instructions."** Regenerate once — the second pass produces the 7-dimension rubric.
- **Edit weights in-portal:** bump `rule_citation_fidelity` from 3 → 6 and add hard-gate reinforcement to `intent_and_task_completeness` description. Save as **version 2**.
- **Both v1 and v2 are pinned in the repo** (`data/evaluation/rubric-auto-generated-{v1,v2}.json`) because auto-generation is non-deterministic — sampling window matters.

### P8 — Routed variant

- Worker model swap only: `gpt-5` → `model-router`. Do **not** try to monkey-patch `agent.run()` — signature mismatch produced empty responses across all rows in the first attempt (v7 was discarded because of this).
- Add strong decomposition instructions in the routed prompt, but keep them as instructions, not as an orchestrator layer.
- Router pricing is passthrough — blended estimate for slide numbers: input $0.640/1M, output $2.560/1M, cached $0.064/1M.

### P10 — Curate training data

- Use the **P50 dataset minus the fixed P20 subset** (30 training-only prompts) to generate traces — recorded eval prompts must stay immutable.
- Run curator with **multiple `--source` args** to merge across the routed + baseline runs.
- Expect ~36 % keep rate (25 keepers from 70). Curator drop reason `no_expected_rule_cited` will dominate — that's a receipt for the Insights finding from P6.
- Split **20 train + 5 validation**.

### P11 — Student model choice

Use `gpt-4.1-mini @ 2025-04-14`:
- Mature SFT path
- 500 GS quota available in Sweden Central
- ~6× cheaper than gpt-5

Not `gpt-4o-mini` or newer — those hit either quota or SFT-eligibility gates during the first pass.

### P12 — Student deploy

**Use DeveloperTier hosting for the student.**

- Capacity 100 is enough for the demo and dramatically reduces cost while the student sits idle between recordings.
- After deploy, agent v9 must have `CONTOSO_ROUTED=false` and `AZURE_AI_MODEL_DEPLOYMENT_NAME=contoso-student` env vars.
- **After deploy, update `src/agent/eval.yaml`** with `agent.version: "9"` and re-run `azd ai agent eval run` so both the built-in bundle and the `caldova-agent-rubric-eval` are scored against v9. Skipping this leaves eval pointing at v8 silently.

### P12 expected numbers (for verification)

| Metric | Baseline v6 | Routed v8 | Student v9 |
|---|---:|---:|---:|
| Avg latency | 44.5 s | 24.1 s | 15.7 s |
| Cost per trip | $0.0313 | $0.0025 | $0.0007 |
| Hard-gate pass | 95 % | 95 % | 100 % |
| Rubric intent | baseline | ~within 3 % | −13 % vs baseline |

The quality regression on v9 is expected — it's the setup for Demo 3's Optimizer story. Do NOT try to eliminate it.

### P12 talk-track on the regression

If asked "why did quality go down?" — five honest culprits:
1. Distribution mismatch — curator kept "verbatim-cite" behavior only.
2. 20 SFT examples × 3 epochs = shape learned, not nuance.
3. `gpt-4.1-mini` capacity ceiling below `gpt-5`.
4. Prompt drift between training data (frontier + routed) and student runtime.
5. Mechanical scorer over-penalizes terse-but-correct answers.

That's the honest answer. Don't try to hide it — it's what motivates Demo 3.

---

## Session 3 — Automate (Demo 3) — P13–P15

**This is the highest-risk session** because it depends on state built in Session 1–2. Read every gotcha below before recording.

### P13 — Readiness check (no side effects)

Confirm five things exist:
- Agent version to optimize (v9 student)
- Dataset file (`src/agent/tests/queries.jsonl`, 20 rows)
- Custom evaluator registered in the portal (`caldova-agent-rubric-eval`, v2)
- Eval model (`gpt-4.1`)
- Optimization model (allowlist: `GPT-5`, `GPT-5.1`, `GPT-5.2`, `GPT-5.4`, `GPT-5.5`, `DeepSeek-V4-Pro`, `DeepSeek-V-3.2`)

Compose the `azd ai agent optimize` command but **do not launch**. Give the presenter the portal URL to watch:
```
https://ai.azure.com/nextgen/r/<workspace-id>/build/agents/contoso-travel/optimize
```

### P13 correct eval.yaml shape

This shape is easy to get wrong. Use this exact structure:

```yaml
agent:
  name: contoso-travel
  version: "9"
  config: .foundry/metadata.yaml    # file path, NOT a directory

dataset:
  local_uri: tests/queries.jsonl    # relative to eval.yaml

evaluators:
  - builtin.intent_resolution       # built-ins as strings
  - builtin.task_adherence
  - name: caldova-agent-rubric-eval # custom evaluators as objects
    version: "2"                    # NO "custom." prefix

options:
  eval_model: gpt-4.1
  optimization_model: gpt-5
  max_candidates: 5
  pass_threshold: 0.6
```

Then `src/agent/.foundry/metadata.yaml` looks like:

```yaml
model: gpt-5
instruction_file: instructions.md
```

with `instructions.md` sitting alongside it. This is the shape the Optimizer will *rewrite* for each candidate.

### P13 canonical Optimizer command (P14 payload)

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

Set `AZURE_DEV_USER_AGENT=microsoft_foundry_skill` on any azd invocation from a recording — attribution shows up in Foundry telemetry.

### P14 — Kick off the Optimizer

Expected wall-clock: **~55–60 minutes** for 5 candidates.

**Do not run this live on-camera.** Kick it off the day before and cache the run id. Then during the recording:

```bash
azd ai agent optimize status opt_<id> --output json
```

to pull the final numbers, and drive the portal to show the completed run.

The completed portal page shows three panels worth capturing on-camera in this order:

1. **Score comparison chart** — bars showing all 5 candidates + baseline. Sets the "everything improved" story.
2. **Token usage modal** (click "View details" in Run overview → Total tokens) — shows the 4-phase breakdown: Running your agent, Scoring responses ×2, Generating improvements. Point out that **~97 % of tokens are spent measuring, not proposing** — that's the honest cost of eval-driven optimization.
3. **View changes on best candidate** — the side-by-side diff of instructions.md. Point out (a) new Mission header, (b) bulleted precedence list for CT-05/06/07/08, (c) "policy-gate tool response" phrasing that ties back to the P6 Insights finding.

### P14 known good numbers (verify against these)

| Field | Expected |
|---|---|
| Job duration | 55–60 min |
| Candidates | 5 |
| Baseline score | ~0.649 |
| Best score | ~0.71 |
| Lift | +9–10 % absolute |
| Total tokens | ~1.5–1.6 M |
| Cost | ~$3 (partial estimate, one model missing pricing) |

If your numbers land dramatically outside this, something changed upstream — check that eval.yaml is pinned to v9 and the correct evaluators are attached.

### P14 fetching per-candidate detail (top-level API doesn't include it)

`azd ai agent optimize status --output json` only returns baseline + best scores. For per-candidate detail:

```bash
TOKEN=$(az account get-access-token --resource https://ai.azure.com --query accessToken -o tsv)
JOB=opt_<your-job-id>
curl -sS "https://cog-hqxztqzboq4bq.services.ai.azure.com/api/projects/brk330-concierge-project/agent_optimization_jobs/$JOB/candidates?api-version=v1" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

Note: **audience is `https://ai.azure.com`**, not `cognitiveservices.azure.com`.

### P15 — Promote via `apply` + `azd deploy` (NOT `optimize deploy` or the portal button)

**Why:** portal Deploy and `azd ai agent optimize deploy` both create the new version server-side from a Foundry-held draft. The winning prompt never lands in git; the repo silently drifts behind production. `apply` downloads the candidate's config into `.agent_configs/<candidate-id>/` first, so the change goes through git review before deploy.

Four commands, run one at a time, with talk-tracks:

```bash
# 1. Pull candidate into local repo
azd ai agent optimize apply --candidate cand_opt_<job-id>_0005
```

Talk-track: *"The Optimizer proposed a rewrite. Before I ship it, I want it in my repo — as a normal git diff — so I can review it, revert it, or hand it to a colleague."*

Expected side effect: creates `src/agent/.agent_configs/baseline/` and `src/agent/.agent_configs/cand_opt_<id>_0005/`, each with `instructions.md` + `metadata.yaml`. **Note:** apply does NOT overwrite `src/agent/.foundry/instructions.md` — `azd deploy` reads from `.agent_configs/<candidate>/` on next run.

```bash
# 2. Show the diff on-camera
diff -u \
  src/agent/.agent_configs/baseline/instructions.md \
  src/agent/.agent_configs/cand_opt_<job-id>_0005/instructions.md \
  | head -120
```

Talk-track: *"Same intent, more structure. New Mission section, bulleted rule precedence, policy-gate phrasing. Ship it."*

```bash
# 3. Deploy as new version
azd deploy --service contoso-travel
```

Expected: takes ~1–2 minutes, exit code 0, the env var `AGENT_CONTOSO_TRAVEL_VERSION` bumps to the next integer.

```bash
# 4. Persist in git
git add src/agent/.agent_configs/ src/agent/.foundry/
git commit -m "P15: promote optimizer candidate as contoso-travel v<n>"
```

### P15 verification — smoke tests (THIS IS WHERE THE FIRST RUN FAILED)

**Run the two-prompt smoke test before the 20-prompt eval.**

Build the smoke dataset carefully — the `break` gotcha bit us:

```bash
python3 - <<'PY'
import json
seen = set()
with open('/tmp/smoke-prompts.jsonl', 'w') as out:
    for src in ('data/evaluation/prompts-20.jsonl', 'data/evaluation/prompts-50.jsonl'):
        for line in open(src):
            d = json.loads(line)
            if d['id'] in ('TP-01','TP-04') and d['id'] not in seen:
                seen.add(d['id'])
                out.write(line)
seen2 = set()
with open('/tmp/smoke-expected.jsonl','w') as out:
    for src in ('data/evaluation/expected-behaviors-20.jsonl', 'data/evaluation/expected-behaviors-50.jsonl'):
        for line in open(src):
            d = json.loads(line)
            if d['id'] in ('TP-01','TP-04') and d['id'] not in seen2:
                seen2.add(d['id'])
                out.write(line)
PY
```

TP-01 is the hero booking (should call ~10 tools, cite CT-05/06/07/20).
TP-04 is the policy-block probe (should call check_travel_policy, cite CT-11+CT-02, refuse).

Run:

```bash
ENDPOINT=$(azd env get-value AGENT_CONTOSO_TRAVEL_PROJECT_ENDPOINT | tr -d '\r')
python src/evaluation/run_baseline.py \
    --variant v<n>-smoke \
    --project-endpoint "$ENDPOINT" \
    --agent contoso-travel \
    --dataset /tmp/smoke-prompts.jsonl \
    --expected /tmp/smoke-expected.jsonl \
    --parallel 2
```

**Green light:** both prompts show >0 tools_called, TP-04 shows `hard_gate_blocked: true` with the expected rule ids, TP-01 assistant_head contains a booking summary (not a "please provide" clarification list).

**Red light:** either prompt shows `tools_called: []` and an "Understood tasks / Please provide" pattern. This is a **reward-hacking regression** — the rubric loved clarifying questions, but the agent stopped executing.

### P15 rollback playbook (if smoke fails)

This happened on the first recording. Frame it as an intentional narrative beat, not a bug:

Talk-track: *"The Optimizer scored a +9.8 % lift on our rubric. The smoke test caught a regression the rubric didn't measure — the agent stopped calling tools and started asking clarifying questions instead. Rolling back — this is why human-in-the-loop matters even after quality-verified optimization."*

Rollback command:

```bash
# Option A — restore baseline instructions
cp src/agent/.agent_configs/baseline/instructions.md src/agent/.foundry/instructions.md
cp src/agent/.agent_configs/baseline/metadata.yaml src/agent/.foundry/metadata.yaml
azd deploy --service contoso-travel

# Option B — apply a different candidate (e.g. candidate_2, the latency-optimal one)
azd ai agent optimize apply --candidate cand_opt_<job-id>_0002
azd deploy --service contoso-travel
```

Then re-run the smoke test to confirm rollback worked.

### P15 — 20-prompt eval (final receipt)

Only after smoke passes:

```bash
python src/evaluation/run_baseline.py \
    --variant v<n>-optimized \
    --project-endpoint "$ENDPOINT" \
    --agent contoso-travel \
    --dataset data/evaluation/prompts-20.jsonl \
    --expected data/evaluation/expected-behaviors-20.jsonl \
    --parallel 3
```

Runtime: ~15 minutes for 20 prompts. Persist result under `data/evaluation/results/v<n>-optimizer-YYYYMMDDTHHMMSSZ.summary.json`. Update `comparison-tracker.md` with the new row.

---

## Cross-session gotchas — read once before every recording

### Foundry Agent Optimizer specifics

- **CLI-driven, not portal-driven.** The portal's "Optimize my agent" button just prints the CLI commands.
- **Optimizer does NOT auto-generate the rubric or dataset.** You must supply both. `azd ai agent eval generate` is a separate command.
- **Custom evaluator syntax in eval.yaml:** object form `- name: <n>` with **no `custom.` prefix**. Built-ins are strings.
- **`agent.config` is a file path**, not a directory. Point it at `.foundry/metadata.yaml`.

### azd extension

- Extension version matters. **beta.14** gives useful error messages; earlier versions don't. Upgrade with `azd extension upgrade --all` (no sudo needed).
- azd core 1.32 → 1.33 upgrade wants sudo, which won't work in the Copilot CLI shell. 1.32 is fine.

### Version pinning

Always set `agent.version:` in eval.yaml before running eval. Unpinned defaults to latest active. When we deployed v7 with a broken monkey-patch, unpinned eval poisoned the rubric run with empty responses.

### Token audience

Foundry Responses endpoint: `https://ai.azure.com/.default`.
Foundry management-plane REST: `https://ai.azure.com` (bare, no `.default`).
NOT `cognitiveservices.azure.com`.

### Fixtures + prepackage hook

Container's `COPY . user_agent/` only sees files under the service project dir. `src/agent/fixtures/` is populated by an azd prepackage hook — do NOT hand-edit contents; edit source `data/` and let the hook mirror.

### App Insights connection

`isSharedToAll: true` **must be a full-envelope PATCH.** Partial PUT silently sets it to `None` in the response.

---

## Recording checklist — per session

Before each session, confirm:

- [ ] Terminal font ≥ 14pt
- [ ] Foundry portal open in a second tab at the project page
- [ ] `azd env get-values` shows the expected variables (masked)
- [ ] `git status` is clean or only expected pending edits
- [ ] Prior session's checkpoints are all done (check `.plan/session-log.md`)
- [ ] `data/evaluation/results/comparison-tracker.md` reflects the state you'll build on
- [ ] Copilot CLI is running Claude Opus 4.7 or equivalent — earlier models miss the Foundry Skill nuances

After each session:

- [ ] Update `.plan/session-log.md` with the decisions made
- [ ] Update `data/evaluation/results/comparison-tracker.md` with new rows
- [ ] Commit everything with a P#-tagged message

---

## What to change if you re-record

If a second speaker re-records, the following can vary without breaking the demo:

- **Job ids** (`opt_...`) — a fresh Optimizer run gets a new id. Update references throughout the tracker and speaker notes.
- **Agent version numbers** — if you rebuild from scratch, v6/v8/v9/v10 will renumber. The narrative arc doesn't care about the number, only the sequence.
- **Fine-tuned model name** — includes a hash; expected.

What must NOT change:

- **The fixed 20-prompt subset** (`data/evaluation/prompts-20.jsonl`). This is the immutable baseline reference.
- **TP-01 as the hero** and **TP-04 as the policy-block probe**.
- **The rubric v2 weights** — those are the tuned setup for the story arc.
- **The talk-track patterns** in "Global talk-track patterns" above.
