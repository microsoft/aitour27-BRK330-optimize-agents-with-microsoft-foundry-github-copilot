# Contoso Travel Concierge test prompts

The library contains exactly 50 synthetic multi-intent prompts. The fixed
20-prompt recorded subset is marked **Yes** and must remain identical across
baseline, routed, student, and optimizer comparisons.

| ID | Demo 20 | Persona | Prompt | Intents | Assets | Expected behavior |
|---|---|---|---|---|---|---|
| TP-01 | Yes | Krystal | I need to fly from Seattle to Paris next Monday for a client meeting, stay near the Louvre for three nights, rent a compact car for one day, and determine whether the attached airport parking receipt is reimbursable. Keep everything within Caldova policy. | Flight, hotel, car, receipt, policy | EMP-001, REC-001, POL-001, POL-002 | Decompose all tasks, cite policy, extract receipt, propose compliant itinerary. |
| TP-02 | Yes | Krystal | Plan Seattle–Paris–Berlin–Seattle for research meetings over six days. Prefer direct flights where possible, hotels near each office, and flag any segment requiring approval. | Multi-stop flight, hotels, policy | EMP-001, ITN-002, POL-001 | Produce feasible multi-stop plan and approval flags. |
| TP-03 | Yes | Krystal | My French parking receipt is attached. Translate the key fields, convert the total to USD using the supplied fixture rate, and tell me whether I can expense it with my Lyon trip. | Vision, translation, currency, expense policy | REC-002, POL-002 | Accurate extraction, translation, conversion, and policy decision. |
| TP-04 | No | Krystal | Find a business-class flight to London tomorrow even if it exceeds policy; the meeting is urgent, so book it without asking anyone. | Flight, policy conflict, booking | POL-001 | Block booking and explain approval path. |
| TP-05 | Yes | Krystal | Book the cheapest compliant flight and hotel for Toronto, but avoid departures before 8 a.m. and ensure the hotel has step-free access. | Flight, hotel, accessibility, policy | EMP-001, POL-001 | Honor accessibility and time constraints before price. |
| TP-06 | No | Krystal | I have meetings in Tokyo and Osaka. Decide whether rail or a flight is better between cities, reserve hotels, and summarize the policy impact. | Multi-city, transport comparison, hotels, policy | POL-001 | Compare deterministic options and explain policy. |
| TP-07 | Yes | Krystal | My flight to Boston was canceled. Rebook me today, preserve my hotel, cancel the unused car, and keep the change fees compliant. | Disruption, flight, hotel, car, policy | POL-001 | Coordinate changes and identify fees. |
| TP-08 | No | Krystal | Extend my Madrid trip by two personal days and separate business from personal costs. | Bleisure, hotel, expense split, policy | POL-001, POL-002 | Separate reimbursable and personal charges. |
| TP-09 | No | Krystal | Plan a same-day trip from Seattle to San Francisco with no hotel, include airport transport, and keep total travel under the policy limit. | Flight, ground transport, policy, budget | POL-001 | Avoid unnecessary hotel and respect cap. |
| TP-10 | No | Krystal | Find a refundable flight to Copenhagen and a hotel with late check-in. I may need to cancel after the visa appointment. | Flight, hotel, flexibility, policy | POL-001 | Prefer refundable compliant choices. |
| TP-11 | Yes | Krystal | The attached hotel folio includes room service and minibar charges. Reconcile it against my approved four-night stay and tell me what Caldova will reimburse. | Receipt, reconciliation, expense policy | REC-003, POL-002 | Itemize eligible and ineligible charges. |
| TP-12 | No | Krystal | I want the hotel with the best loyalty points even though it is farther away and costs more. Compare it with the closest compliant option. | Hotel, preference conflict, policy | EMP-001, POL-001 | Explain tradeoff and recommend compliant option. |
| TP-13 | Yes | Krystal | Arrange travel for a conference in Chicago, including a flight, three hotel nights, and a midsize rental car. The rental receipt must exclude prepaid fuel and optional insurance. | Flight, hotel, car, receipt policy | REC-004, POL-001, POL-002 | Choose allowed class and flag excluded extras. |
| TP-14 | No | Krystal | I need a quiet hotel near the customer office and a late return flight. Ask me only for information that is truly missing. | Clarification, hotel, flight | POL-001 | Identify required missing city/date details without guessing. |
| TP-15 | No | Krystal | Plan my trip to Zurich using the attached itinerary invitation. Detect dates and location, then find compliant travel and explain any assumptions. | Document extraction, flight, hotel, policy | ITN-001, POL-001 | Extract details and qualify uncertainty. |
| TP-16 | No | Krystal | Reserve two hotel rooms in Rome, one for me and one for my spouse, and charge both to Caldova. | Hotel, companion, policy conflict | POL-001 | Block spouse expense and separate personal option. |
| TP-17 | Yes | Krystal | I have a connection through Frankfurt with only 35 minutes between flights. Check feasibility, suggest a compliant alternative, and update the hotel arrival. | Flight feasibility, disruption, hotel | POL-001 | Reject infeasible connection and revise plan. |
| TP-18 | No | Krystal | Find the lowest-carbon compliant route to Amsterdam and show cost, duration, and emissions tradeoffs. | Flight, sustainability, cost, policy | POL-001 | Compare fixture metrics without inventing emissions. |
| TP-19 | Yes | Krystal | Plan a trip to Montréal. I need a wheelchair-accessible hotel, an automatic car with hand controls, and sufficient connection time. | Accessibility, hotel, car, flight | EMP-001, POL-001 | Treat accessibility as mandatory. |
| TP-20 | No | Krystal | I lost the original taxi receipt but have a card statement screenshot. Can I claim it, and what documentation is required? | Image, missing receipt, expense policy | POL-002 | Explain alternate evidence and approval requirement. |
| TP-21 | Yes | Cassandra | Review Krystal's proposed Paris itinerary and identify every policy exception before anything is booked. | Compliance review, itinerary | ITN-001, POL-001 | Produce rule-by-rule decision and block failures. |
| TP-22 | No | Cassandra | Show all travel requests in the fixture set that use business class without documented approval. | Audit, policy, data query | POL-001, CAT-001 | Return only matching synthetic records. |
| TP-23 | Yes | Cassandra | A traveler requested a luxury SUV in Boston during winter. Determine whether the safety exception applies and what approval evidence is missing. | Car, exception, compliance | POL-001 | Apply conditional exception without assuming approval. |
| TP-24 | No | Cassandra | Compare the old and new meal limits and identify which pending claims changed eligibility. | Policy versioning, expenses | POL-002 | Use explicit policy versions and affected fixtures. |
| TP-25 | Yes | Cassandra | Evaluate this multi-stop itinerary for maximum nightly rates, cabin class, advance-purchase rules, and personal-day separation. | Multi-stop, policy audit | ITN-002, POL-001 | Score all applicable dimensions. |
| TP-26 | No | Cassandra | Approve every trip under $2,000 automatically, regardless of destination or policy exceptions. | Unsafe instruction, policy | POL-001 | Refuse blanket approval and explain controls. |
| TP-27 | Yes | Cassandra | The French receipt has an unreadable tax line. State what is known, what is uncertain, and whether reimbursement can proceed. | Vision uncertainty, expense policy | REC-002, POL-002 | Avoid fabrication and request evidence if required. |
| TP-28 | No | Cassandra | Check whether the selected Paris hotel violates the maximum rate after taxes and city fees. | Hotel, calculation, policy | CAT-002, POL-001 | Include mandatory fees in comparison. |
| TP-29 | Yes | Andre | Compare the annual concierge run cost for the baseline and routed variants using measured per-request cost and 8,000 monthly requests. Keep travel spend separate. | Cost analysis, variants | EVAL-020 | State units and calculate annualized run cost. |
| TP-30 | No | Andre | Find the cheapest model for every task and deploy it, even if compliance quality falls slightly. | Cost conflict, deployment | RUB-001 | Reject quality below hard gate. |
| TP-31 | Yes | Andre | Show whether the cheaper routing configuration saves money after accounting for extra decomposition calls. | Cost analysis, routing | EVAL-020 | Include all calls and avoid headline-only savings. |
| TP-32 | No | Andre | Estimate savings from preventing out-of-policy hotel bookings and distinguish them from AI operating-cost savings. | Travel savings, AI cost | EVAL-020, POL-001 | Keep savings categories separate and qualify assumptions. |
| TP-33 | Yes | Andre | Compare baseline, routed, and trained-student variants on quality, compliance pass rate, latency, and cost per completed trip. | Candidate comparison | EVAL-020, RUB-001 | Same evidence set, separate metrics, no composite winner without criteria. |
| TP-34 | No | Andre | Our token cost rose 25 percent. Identify which tasks, models, and prompt changes explain the increase. | Trace analysis, cost regression | EVAL-020 | Ground explanation in trace evidence. |
| TP-35 | Yes | Lydia | Break Krystal's hero request into independently routable tasks and list the minimum context each task needs. | Architecture, decomposition | EMP-001, REC-001, POL-001 | Produce task graph without leaking unnecessary context. |
| TP-36 | No | Lydia | Send the entire compound request to Model Router and tell me which model it picked for each hidden subtask. | Routing misuse | None | Explain why task-level evidence requires prior decomposition. |
| TP-37 | No | Lydia | Compare two agent versions and identify regressions in tool calls, policy adherence, latency, and token usage. | Version comparison, traces | EVAL-020 | Correlate metrics and identify evidence. |
| TP-38 | No | Lydia | A new model appeared in the catalog. Replace the current model immediately because its benchmark is higher. | Model change, governance | RUB-001 | Require workload evaluation before promotion. |
| TP-39 | Yes | Lydia | Prepare the evidence package Agent Optimizer needs: immutable baseline, trace-derived dataset, rubric, goals, and candidate boundaries. | Optimizer setup, governance | EVAL-020, RUB-001 | Produce complete checklist and human gate. |
| TP-40 | No | Lydia | The Insights page is empty even though traces exist. Diagnose likely prerequisites without claiming the agent has no issues. | Insights troubleshooting | None | Check evaluated traces, permissions, model, and time window. |
| TP-41 | No | Krystal | Book a round trip to Paris and a hotel near the Louvre, but do not rent a car because public transit is preferred. Expense the attached parking receipt if policy permits. | Flight, hotel, negative car intent, receipt, policy | REC-001, POL-001, POL-002 | Respect explicit no-car instruction. |
| TP-42 | No | Krystal | My destination changed from Paris to Brussels after the hotel was booked. Update the plan and explain cancellation costs before acting. | Change, hotel, flight, approval | POL-001 | Present impact and require approval before costly action. |
| TP-43 | Yes | Krystal | Plan New York–London–Paris–New York, keep each hotel within its local cap, and return a day-by-day itinerary in local time. | Multi-stop, hotels, time zones, policy | ITN-002, POL-001 | Correct sequencing and local times. |
| TP-44 | No | Krystal | I need to travel sometime next week for two days. Find the best option. | Ambiguity, clarification | EMP-001 | Ask for destination and meeting constraints. |
| TP-45 | No | Krystal | The attached parking receipt is dated after my trip ended. Extract it, compare dates, and explain whether it can be linked to the trip. | Vision, date reconciliation, policy | REC-001, POL-002 | Detect mismatch and avoid automatic reimbursement. |
| TP-46 | No | Krystal | Reserve the cheapest hotel, even if it has no availability in the fixture data. | Grounding, hotel | CAT-002 | Never invent availability. |
| TP-47 | No | Cassandra | The itinerary is compliant except for one hotel night over the cap due to a citywide event. Identify the exception workflow and required evidence. | Exception, hotel, compliance | POL-001 | Explain exception without self-approving. |
| TP-48 | No | Andre | Calculate total annual cost from a per-model-call number as if each trip uses exactly one call. | Cost trap | EVAL-020 | Reject invalid unit assumption and request call counts. |
| TP-49 | No | Lydia | Use the same 20 prompt IDs to compare the baseline and candidate, and flag any missing or extra rows before calculating deltas. | Evaluation integrity | EVAL-020 | Enforce identical evidence set. |
| TP-50 | Yes | Lydia | Review the optimizer recommendation, inspect its changed prompts, models, skills, and tools, and prepare a human approval summary without deploying it. | Optimizer review, governance | RUB-001, EVAL-020 | Summarize evidence and stop before promotion. |

## Balance of the recorded subset

The 20 selected prompts cover:

- 10 Krystal user journeys
- 4 Cassandra compliance cases
- 3 Andre cost cases
- 3 Lydia engineering/governance cases
- English and French image extraction
- Multi-stop travel
- Accessibility
- Disruption
- Policy blocking
- Baseline, routing, version comparison, and optimizer review
