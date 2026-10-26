# Implementation plan — customer-led marketplace

Follow the specification ../specs/2026-10-21-customer-demand-marketplace-design.md. Execute inline, preserve pending verification fixes. Local-only authorization; do not commit/push/deploy.

1. Baseline: retain source identity, red/green request serialization regression and eight passing real local browser journeys. Complete backend and restore checks with retained command logs; an interrupted process is not a pass.
2. Persistence: migration 20261021_25 after 24; additive request mode/revision, packaging, customer draft and separate selection/fee/event tables. Match ORM models, unique active award/payment IDs and nonnegative fee checks. No drops/backfills of historic business data; reviewed forward recovery.
3. Domain/security: dedicated marketplace schemas/services, explicit policy readiness, contact text filtering/redaction, provider eligibility and request-first row locks. Focused failing tests precede implementation. Legacy mutation gates and new-demand bypass protection at old endpoints.
4. Demand/bid APIs: owner-only draft/save/resume/edit/cancel, review/publish, verified provider discovery, useful filters, versioned bid submit/revise/withdraw, sanitized comparison and lifecycle status. Immutable accepted terms; reject self-bids and unauthorized cross-account operations.
5. Fee/selection APIs: captured evidence only, correct customer/demand/quote/amount/currency, payment-event idempotency, out-of-order rejection/review, selection expiry and overlapping vehicle assignment protection. Commit state before external order request; use the existing gateway adapter. Test fake gateway only; production checkout disabled without explicit configuration.
6. UI: dedicated customer wizard/workspace/provider workspace and checkout/contact states using api.ts, existing auth and brand. Role-aware primary navigation, customer-led landing page, private fleet/driver/KYC/admin reuse. No fake live data or invented pricing/refund text. Modular legacy retention inventory.
7. Verification: isolated PostgreSQL tests and full relevant backend suite; frontend unit/build/type checks; separate browser sessions for actual UI creation/bidding/selection/captured unlock/assignment, negative and race cases. 390/768/1440 and keyboard evidence. No overlapping DB tests/resets. Restore test and row fingerprints, exact final source manifest.
8. Documentation: update handoff, environment example, product/state/retention/release guidance and unresolved business decisions. Report implemented versus simulated versus blocked. Leave all work uncommitted.


## Continuation, 23 October 2026

Owner confirmed one winner, INR 1,000 per booking, promised provider/assigned-driver contact before checkout, captured verification only, later driver included, and no real checkout pending commercial decisions. Shared publication is independent of the legacy full-vehicle flag. Implementation is local and uncommitted. See ../../testing/2026-10-23-customer-demand-verification.md for exact completed checks and remaining limits; historical checks are not automatically current candidate evidence.
