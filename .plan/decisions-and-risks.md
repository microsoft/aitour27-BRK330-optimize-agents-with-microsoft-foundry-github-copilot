# Decisions and risks

| Topic | Decision or mitigation |
|---|---|
| Naming | Caldova is the customer company; Contoso Travel is the contractor; the display product is Contoso Travel Concierge; the hosted-agent/service slug is `contoso-travel`. |
| Resource group | Use the fixed Azure resource-group name `rg-brk330-concierge`. |
| Runtime | Python hosted agent with FastAPI and lightweight HTML/CSS/JavaScript. |
| Hosting | Live Azure only; no simulated local demo path. |
| Recording stability | Record the action that starts each long cloud operation, remove the waiting period during editing, and resume from a prepared, verified checkpoint. Keep fallback clips/screenshots for preview UI changes. |
| Evaluation size | Retain 50 prompts; record comparative runs with a fixed balanced subset of 20. |
| Student model | Discover and verify a supported smaller model during implementation; never hard-code an assumed model. |
| Preview features | Validate availability, region, roles, labels, and current UI before recording. |
| Insights | Requires evaluated trace data; raw traces alone are insufficient for the intended story. |
| RBAC | Provision least privilege and verify the exact current built-in role required by the portal. Current screenshots request Monitoring Reader for the project managed identity. |
| Model Router | Route decomposed tasks, not the original compound request. |
| Compliance | Treat policy compliance as a blocking gate. |
| Cost reporting | Distinguish per-call, per-request, and per-trip costs. |
| Agent Optimizer | Portal-first and human-approved; never claim automatic production promotion. |
| Fine-tuning | If training cannot complete before recording, do not invent results. Use the validated baseline and routing comparison while retaining the training path as the next checkpoint. |
| Slides | Use measured results only; mark outstanding values as `<measured after dry run>`. |
| Deck URL | Keep pending until the public link is supplied. |
| Attendee self-run | Remains deferred; do not populate `instructions/` until explicitly approved. |
| Timing | The five acts consume all 45 minutes. Recording edits, not live delivery, absorb overruns. |

## Highest-risk dependencies

1. Azure subscription access, quota, and regional availability.
2. Current Model Router support and route telemetry.
3. Availability of a training-eligible student model.
4. Training-job completion and result quality.
5. Preview Insights and Agent Optimizer availability and UI stability.
6. RBAC propagation and Application Insights ingestion delay.

## Required stop conditions

Stop rather than fabricate when:

- A requested model or capability is absent from the live catalog.
- The evaluation dataset changes between candidate comparisons.
- Policy compliance is not enforced as a hard gate.
- A result cannot be traced to a measured run.
- The optimizer result has not been human-reviewed.
