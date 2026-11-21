# Customer-led demand and bidding marketplace

Updated 22 October 2026 (IST). Owner authorizes local implementation, additive migrations and isolated verification. No commit, push, production migration, deployment, paid activation or real sends/payments.

## Intent and impact

Customers post requirements without truck terminology. Verified providers discover private-safe demand summaries and offer explicit bids. Customer selects a bid, reviews a separate connection fee, and gets the promised verified provider or assigned-driver contact only after matching captured-payment evidence. Freight price and payment remain separate. Existing login, document scan/version/manual-review gates and historical bookings survive.

Reuse transport_requests, cargo_items, quotes/versions, bookings/allocations/trips, role/session checks and the payment gateway/signature validator. Add draft persistence, a request mode/revision, packaging metadata and a separate connection-selection/payment ledger. Keeping fee accounting separate prevents treating it as a freight deposit. Additive migration only; legacy rows keep legacy mode. One primary customer/provider interface wraps existing operational screens. Preserve existing route/capacity/shared acceptance code and constrain conflicting entry points with server-side flags.

## Decisions and fail-closed configuration

Owner confirmed one winning provider per demand and a server-configurable ₹1,000 INR one-time connection fee per booking. Freight is quoted separately and paid directly to the provider. This fee is not transport fare, a deposit or an advance. A verified provider contact or already-assigned verified driver contact must exist before checkout; label exactly which contact is being purchased. Provider-contact checkout must never promise a driver phone pending assignment. A driver assigned later to that same booking is included without another fee. Purchased contact is revisitable without another charge.

Use ₹1,000 in isolated sandbox tests only. Tax treatment, cancellation/refunds, provider-failure handling and replacement-provider fees remain undecided. No automated refunds, real payment collection or invented commercial rules. ENABLE_REAL_CONNECTION_CHECKOUT stays false; production fee policy cannot use undecided tax. Customer document KYC remains an explicit product question; local test policy uses the existing verified account, without inventing a new document flow.

Single winner does not disable shared capacity. Existing shared search, reservations, matching review and explicit acceptance remain retained and enabled. Shared-capacity publication remains available under its existing shared-capacity flag and compliance gates. The new demand path currently accepts one vehicle per award; multiple-vehicle/split-load support remains a separate scope decision and is not claimed complete.
## State and privacy design

Use existing request draft/published/allocated/cancelled states plus selection_pending; quote active/selected/accepted/withdrawn/expired. A selection binds customer, request revision, quote version, vehicle, immutable freight/fee snapshots and expiry. Request-first locking and one active selection enforce a single award. Expired pending selections release eligibility; late captures record funds and require review, never resurrect a booking or unlock contacts. Captured/failed/refund/dispute events are idempotent and authenticated. No transaction stays open during gateway order creation or customer checkout.

Contact endpoint returns locked, unavailable or unlocked; it checks ownership, captured matching fee, active booking and the promised verified contact proof. The selected contact user and phone hash are pinned before checkout. Only this endpoint returns the purchased phone to the paying customer. Verified driver details added later are included on the same booking. Audit access without storing raw phone in audit events. Public list/detail/bid responses exclude contact and precise addresses; owner details remain private. Obvious phone/email/URL text is rejected or redacted, with documented obfuscation limitations. Prior disclosure cannot be undone.

Persist signed unmatched gateway events with curated references, never raw webhook payloads. A refund/dispute arriving before capture must keep contact locked when capture is eventually received. Gateway order creation is committed before network access; unknown creation outcomes require reconciliation rather than another charge.
## Delivery sequence

1. Preserve pre-change baseline and existing fix: request creation explicitly loads cargo/stops; 25 PostgreSQL cases plus new regression and eight browser journeys. Retain failures and source fingerprints as dated evidence.
2. Failing tests for draft ownership, demand privacy/eligibility, own-demand bidding, bid lifecycle and legacy direct-call refusal; implement compatible schema/routes.
3. Failing PostgreSQL cases for selection races, immutable snapshots, vehicle overlap, captured/forged/mismatched/duplicate/late payments and contact authorization; implement selection/fee services and adapters.
4. Customer demand wizard with server drafts, review/publish, private details, bid comparison/selection/fee state; provider demand discovery, bids and assignment using real APIs. Retain private fleet/compliance and admin operations. Update navigation and customer-led landing page in existing visual system.
5. Add separate-session desktop/mobile/keyboard browser journeys with clearly marked local payment/scan simulations. Run affected complete suites, migration checks, isolated backup/restore and screenshots. Update handoff, configuration, feature-retention and release plans. Exact tested dirty source fingerprint; no publication.

## Release boundary

Local success is not launch approval. Required decisions above, real exact-version scanning, Razorpay sandbox reconciliation, real email receipt, deployed browser cookie behavior, recovery/alerts, independent security and qualified legal/privacy/tax review remain. Production rollout must be separately approved, rehearse migrations with impact/recovery evidence, then API and matching frontend; no automatic destructive downgrade.
