# Insights reveal — Demo 1 baseline

*Prepared from the 20-prompt baseline run
`data/evaluation/results/baseline-20260910T073852Z.*`. Real measurements only;
no fabricated numbers.*

## Finding

> **Every prompt is handled by one frontier model (`gpt-5`). The two most
> expensive rows (TP-01, TP-02) burned 49k tokens between them, took ~1.5
> minutes each, and produced only one policy citation. Task decomposition
> plus Model Router is a strong candidate to reduce cost without hurting
> compliance.**

### Row-level evidence

| Prompt | Persona | Latency | Tokens | Cost   | Tools | Policy |
|---|---|---:|---:|---:|---:|---|
| **TP-02** (SEA→PAR→BER multi-stop) | Krystal | **81 s** | **32,942** | **$0.0650** | 10 | none cited |
| **TP-01** (SEA→CDG hero + parking receipt) | Krystal | 70 s | 16,194 | $0.0646 | 8 | blocked on **CT-02** |
| TP-39 (Optimizer evidence package) | Lydia | 65 s | 6,152 | $0.0487 | 0 | analytical |
| TP-35 (Task graph) | Lydia | 60 s | 8,002 | $0.0420 | 1 | analytical |
| TP-27 (French receipt uncertainty) | Cassandra | 44 s | 7,226 | $0.0386 | 1 | analytical |

Aggregate for the 20-prompt subset:
- p95 latency **69.5 s**, avg **44.5 s**
- Total cost **$0.6268**, avg per-request **$0.0313**
- Cache hit ratio 70% (55 424 / 78 852 input tokens)
- Hard-gate pass rate **95%** (TP-01 blocked when the expected outcome was pass)

### Root cause

- One frontier model handles the compound request end to end. There is no
  task decomposition; the model self-decomposes at inference time and calls
  every tool sequentially at frontier cost.
- Cheaper routing candidates (gpt-4.1-mini, gpt-5-mini) are ~4–10x cheaper
  per input token, plenty capable for deterministic sub-tasks (search,
  extract, prepare itinerary).

### Fix path (Demo 2, hill-climb)

1. Add explicit task decomposition in the agent so the router receives
   scoped subtasks with just the context they need.
2. Route each subtask through Model Router; leave frontier reasoning only
   for the final planning step and policy-cite composition.
3. Re-run the same 20 prompt IDs. Expect input tokens down 40–60%, cost per
   request down ≥ 40%, quality gate held at ≥ 95%.

## Portal navigation to record

### 1. Open the Foundry project

```
https://ai.azure.com/nextgen/r/eogHKHDTSdCt3kJQcWz9lA,rg-brk330-concierge,,cog-hqxztqzboq4bq,brk330-concierge-project
```

### 2. Open the agent build view

```
https://ai.azure.com/nextgen/r/eogHKHDTSdCt3kJQcWz9lA,rg-brk330-concierge,,cog-hqxztqzboq4bq,brk330-concierge-project/build/agents/contoso-travel/build?version=4
```

Left rail → **Monitor / Insights / Traces** (label depends on the current
preview UI). If Insights is not yet available, use the **Traces** page.

### 3. Filter to the recorded run window

- Date range: cover the timestamp on the results manifest.
- Agent: `contoso-travel`.
- Version: `4`.

### 4. Highlight the hero trace

The recorded example to open live in the portal is **TP-02**:

- Response id: `caresp_0867ea8dade99b2000n5xVPuQhwG5TDeTMBjmWTk8Gf0nAirOG`
- Latency: 80.982 s
- Total tokens: 32 942 (input 21 984, output 10 958, cached 20 736)
- Cost per request: **$0.0650**
- Tool calls: 10 (all against the single frontier model)

Present it as the *tomorrow-not-yet* story: capable but expensive, one
model doing every job. Then close with: "Session 2 shows us how to hill-climb
this."

### 5. Fallback screenshots to capture

- Traces list with the 20 rows visible.
- TP-02 span tree with the 10 tool calls.
- Cost / token panel (if Insights UI exposes it) or the Response body pane.
- Any auto-generated Insight card (preview may or may not surface one).

## Prerequisite check (spec §Observability)

| Check | Status |
|---|---|
| Application Insights connected to project | ✅ `appi-brk330-nxzzad4sd6dl6` |
| Log Analytics workspace attached | ✅ `log-brk330-nxzzad4sd6dl6` |
| Judge model deployed and reachable | ✅ `gpt-4.1` @ 2025-04-14 (30k GlobalStandard) |
| Project managed identity Monitoring Reader on App Insights | ✅ |
| Evaluated trace data available | ✅ 20-row baseline manifest persisted (this run) |
| Foundry hosted-agent tracing enabled in container | ✅ Container log shows `Azure Monitor enabled` |

No agent modification for this checkpoint — Insights only *reveals* the
problem; Demo 2 is where we fix it.
