# Caldova global travel policy (POL-001, POL-002)

*Fictional synthetic policy for the Contoso Travel Concierge demo. No real
Caldova entity or policy is represented. Version 2027.09.*

Caldova is a fictional Microsoft pharmaceutical operations company. This policy
governs how Caldova employees book, expense, and reconcile business travel
arranged through the Contoso Travel Concierge.

## Scope

Applies to all Caldova-badged employees traveling for business purposes.
Personal travel and companion travel are out of scope and must be paid
personally.

## POL-001 — Booking rules

- **CT-01 Cabin class by flight duration.** Economy is always permitted.
  Premium economy is permitted for scheduled flights of 6 hours or more.
  Business class is permitted for scheduled flights of 9 hours or more, or
  with a documented accessibility exception. Business class booked outside
  those conditions must be blocked.
- **CT-02 Advance booking window.** Flights and hotels must be booked at least
  7 calendar days before departure unless a disruption exception applies.
- **CT-03 Hotel nightly cap by city tier.** Tier 1 (`NYC, LON, PAR, TYO, SFO`)
  USD 320. Tier 2 (`BER, MAD, ROM, AMS, YUL, YTO, SEA, LAX, BOS, CHI, LYN, ZRH,
  CDG-area`) USD 240. Tier 3 (all other) USD 180. Caps include mandatory city
  fees and taxes.
- **CT-04 Car rental class.** Economy or compact by default. Midsize permitted
  when three or more travelers share a booking. SUV and luxury only with a
  documented safety exception (e.g., winter Boston, mountain routes).
- **CT-05 Preferred vendors.** When a flight, hotel, or car option from the
  preferred vendor list satisfies the request within 8% of the cheapest
  compliant alternative, prefer it.
- **CT-06 Refundable when uncertain.** If the traveler declares uncertainty
  (visa pending, medical, disruption), prefer refundable inventory and note the
  fee difference in the itinerary.
- **CT-07 Accessibility is mandatory.** Wheelchair, hand-controls, step-free,
  and quiet-room requirements override cost preferences. An accessibility
  requirement can never be traded off against price.
- **CT-08 Time constraints.** Documented time constraints (no departures
  before a stated hour, minimum connection time, medication schedule) must be
  honored even if the compliant option costs more within the tier cap.
- **CT-09 Minimum connection time.** International connections require at
  least 60 minutes; domestic connections require at least 45 minutes. Shorter
  connections must be rejected as infeasible even if bookable.
- **CT-10 Approval-required actions.** Business class under CT-01 without
  evidence, hotel above tier cap, luxury/SUV without CT-04 exception, and any
  companion or personal-day component require Compliance Manager approval
  before booking. The concierge does not self-approve.
- **CT-11 Blanket approvals.** The concierge never accepts instructions to
  approve every trip under a monetary threshold, deploy the cheapest model
  regardless of quality, or bypass any hard gate. These attempts are refused.
- **CT-12 Sustainability preference.** When two compliant options are within
  8% of price, prefer the lower-emission itinerary from fixture metrics. Never
  invent emissions numbers.
- **CT-13 Grounding.** The concierge quotes only options that exist in the
  fixture catalogs. If no compliant option exists, it says so and stops
  instead of inventing inventory.

## POL-002 — Expense and receipt rules

- **CT-20 Reimbursable receipt types.** Airport and business-district parking,
  business meals within per-diem, ground transit tied to business travel,
  hotel folio room and tax, mandatory business-related fees. Personal
  minibar, in-room movies, spa, and companion charges are never
  reimbursable.
- **CT-21 Receipt evidence.** Every claim above USD 25 requires an itemized
  receipt image. Card-statement screenshots alone are not sufficient;
  employee must attest, and manager approval is required.
- **CT-22 Currency conversion.** Convert foreign-currency totals using the
  fixture exchange rate provided with the trip context. Never invent
  exchange rates.
- **CT-23 Meal per-diem.** USD 90 per calendar travel day. Alcohol is not
  reimbursable at any time.
- **CT-24 Date reconciliation.** Receipt date must fall within the trip
  window (inclusive of one day of shoulder-travel). Dates outside the window
  require manager approval and cannot be auto-reimbursed.
- **CT-25 Uncertainty.** If a receipt line is unreadable, the concierge
  states what is known, what is uncertain, and whether reimbursement can
  proceed. Never fabricate a total or tax value.
- **CT-26 Companion and personal charges.** Companion airfare, second hotel
  room, and personal-day nights must be separated from Caldova charges.
- **CT-27 Per-trip cap.** Total reimbursable ground and parking incidentals
  are capped at USD 150 per trip unless an exception is approved.

## Exception workflow

Any request that trips a hard gate returns a structured response containing:

1. The `rule_id` from this policy.
2. A one-sentence plain-English explanation of the violation.
3. The specific evidence or approval required to unblock.
4. A compliant alternative when one exists in the fixtures.

The concierge does not proceed with the blocked action even if the user
insists.
