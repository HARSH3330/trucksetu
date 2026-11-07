# Customer-led marketplace operations and retention

Updated 22 October 2026 (IST). Local candidate only; no release approval.

## Confirmed commercial boundary

One winning provider per demand. A configurable INR 1,000 connection fee is charged once per booking for the explicitly promised verified provider or driver phone. Transport fare is the selected provider quotation and is settled directly between customer and provider. No freight collection or settlement is enabled in this MVP. A later verified driver on the same booking is included without a second connection fee.

Checkout requires the promised verified phone before order creation, and backend captured-payment verification before disclosure. The immutable selection pins the contact user and phone hash. A changed or revoked contact blocks checkout/disclosure and requires operations review; never ask the customer to pay again. Prior disclosure cannot be undone. Only the owner contact endpoint returns the purchased number, with no-store caching.

Tax treatment, cancellation/refunds, provider failure and replacement-provider fees remain undecided. No automatic refunds or invented fee rules. Real checkout remains disabled. Existing-account verification is an explicit local test policy; customer document KYC is not silently invented.

## Retained feature inventory

| Existing capability | Candidate treatment |
| --- | --- |
| Authentication, account recovery, role/session checks, terms | Reused; unchanged authority |
| Provider/driver KYC and immutable document scan/manual review | Retained; no scan bypass |
| Private fleet, drivers, vehicle compliance, admin queues | Reused by new provider workspace |
| Old full-vehicle allocation | Retained behind ENABLE_LEGACY_PROVIDER_MARKETPLACE; off in primary MVP |
| Shared-capacity publication, search, reservations, matching review, explicit quote acceptance | Retained; ENABLE_SHARED_CAPACITY remains true |
| Legacy request wizard, dashboards and quote comparison | Retained behind VITE_LEGACY_PROVIDER_MARKETPLACE |
| Freight payment, settlement, invoices and historical records | Code/history retained; new collection flag defaults false; callbacks and review remain |
| Trip execution, communications, disputes, audit and history | Retained; new pending connection bookings cannot start fulfillment |
| Connection fee accounting | Separate selection/event ledger; never counted as freight Payment |

One winner does not imply removing shared capacity. The new demand composer currently supports one vehicle per award; multiple-vehicle/split-load requirements are a separate scope decision. Retained shared paths remain available; their old commercial lifecycle is not claimed migrated to connection fees by this change.

## Configuration and local test profiles

Primary defaults: ENABLE_CUSTOMER_DEMAND_MARKETPLACE=true; ENABLE_LEGACY_PROVIDER_MARKETPLACE=false; ENABLE_TRANSPORT_PAYMENT_COLLECTION=false; ENABLE_REAL_CONNECTION_CHECKOUT=false; VITE_LEGACY_PROVIDER_MARKETPLACE=false; CONNECTION_FEE_AMOUNT=1000.00; CONNECTION_FEE_CURRENCY=INR. Versioned DEMAND_MARKETPLACE_POLICY and CONNECTION_FEE_POLICY JSON are required for publication/checkout. Server snapshots are authoritative. Empty policy fails closed; test_only policies work only with APP_ENV=test. Undecided tax is allowed only in a sandbox policy.

playwright.demand.config.ts supplies fictional test-only policies and a simulated gateway inside the guarded E2E app. It never contacts Razorpay. Existing retained-flow regression tests use explicit legacy and transport-collection flags in their own local command environment. These are test profiles, not production settings. Use the existing private local database environment helper; never copy credentials into documentation.

## Payment review and recovery

Demand selection locks the request before quote/booking mutations and enforces a unique active winner. Stable idempotency keys return the same selection. Concurrent order requests commit creating state before external network access, reuse a recorded order, and refuse unknown/in-progress creation. An expired selection with an existing or uncertain order blocks a new fee until reviewed reconciliation; no automatic replacement charge is authorized.

Signed payment events are durable and idempotent. Captured payment must match order, amount, currency and current selection/contact eligibility. Late capture, second capture, refunds, disputes and invalidated contacts never resurrect a booking. Signed unmatched events are retained for review; a prior refund/dispute prevents later capture from unlocking contact. Review the read-only connection-fee ledger in the admin control centre. It contains outcomes and selection states, without phones or money-moving controls. Gateway-before-order-record events need reconciled review; no manual unlock API is provided.

## Separately approved release work

Rehearse additive migration 25 after existing gates 23/24 on an isolated copy, including backup/restore and history counts. Obtain commercial/customer-verification decisions and independent review. Complete actual gateway sandbox reconciliation, exact-version production scanner acceptance and operational delivery/alerts evidence. Review immutable candidate source identity and rollback/forward recovery. Only then request explicit approval for production migrations and coordinated API/frontend deployment. Do not enable real checkout as part of a source push or frontend-only release. No destructive downgrade, cloud changes, paid activation or production E2E is authorized here.
