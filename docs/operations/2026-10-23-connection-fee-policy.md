# Operational update — 24 October 2026

The earlier hypothetical waiver-tax test path is disabled. All waiver checkout remains blocked. Refund execution/reconciliation now has an explicit guarded Test Mode adapter/CLI, with migration28 metadata. No automatic live executor exists. Actual Razorpay verification remains blocked on keys; see [current report](../testing/2026-10-24-razorpay-test-mode-verification.md). Earlier verification below remains dated.

# Connection fee, reveal, cancellation and provider-failure credit

Owner instructions dated 23 October 2026 supersede previous undecided-refund/provider-failure copy. Local implementation only; no real charge/refund, push or deployment.

Base fee INR1,000 per booking. Proposed configurable tax rate0.20 gives INR200 tax and INR1,200 total. This is not a confirmed applicable tax rate. Real checkout requires explicit rate confirmation AND the independent live-checkout flag and non-test approved policy; defaults remain blocked. Freight remains a provider quote settled directly; no credit/refund here affects transport fare.

Captured matching backend payment creates contact eligibility only. GET contact returns no number before an explicit POST reveal. POST reveal verifies owner/payment/current contact and commits revealed_at/audit under the same demand/selection lock used for cancellation. Repeated reveals/access do not charge again. Historical audited contact access is backfilled as revealed in additive migration27.

Before reveal, cancellation immediately blocks future contact and records one full refund obligation for the captured amount including paid tax. The refund is REQUESTED, not processed; no external adapter is called. Only a verified matching refund event can mark it processed. Retrying reuses the same request. A valid late capture after pre-reveal cancellation also records the refund obligation. After reveal, ordinary cancellation is not refundable and requires explicit acknowledgement. A concurrent pre-reveal cancellation cannot silently become a nonrefundable cancellation if reveal wins: it returns409 for renewed acknowledgement. Previously disclosed contact cannot be made unseen.

An independent authorized administrator must confirm selected-provider failure with an audited reason after captured payment and reveal. This blocks future contact and issues exactly one single-use platform-fee credit per failed booking. There is no refund for that failure. Customer cannot issue it, self-review is denied, and duplicate/concurrent administrator requests return the same credit. Issuance does not settle freight or automatically resolve an in-progress physical trip.

A credit is reserved before creating any gateway order, under customer/credit row locks. Only one booking can reserve it. A credit is redeemed only when its reserved booking receives a matching verified capture, in that same transaction. It cannot be reused by another checkout. Unused/no-order reservations are released by cancellation or selection expiry; uncertain/created orders require reconciliation. Redeemed-credit restoration after cancellation is not invented and remains an operations/policy decision.

Credit display: Platform connection fee waived. Waiver tax remains pending confirmation, so actual waiver checkout is blocked. To test redemption only, APP_ENV=test + test-only fee policy + an explicitly hypothetical positive CONNECTION_FEE_WAIVER_TEST_TAX_AMOUNT can create a simulated payable-tax order; this is not an applicable tax calculation. No zero-amount capture is fabricated. A confirmed zero-tax waiver flow will need its own approved eligibility/accounting rule before enabling. Do not infer waiver tax from the proposed ordinary fee tax.

Unresolved: applicable tax rate/wording/invoicing, tax on waiver, credit expiry, transferability, invalid-contact treatment, redeemed-credit restoration, replacement-booking details beyond one platform-fee credit, real refund execution/reconciliation approval, legal/statutory review. No expiry/transfer policy or consumer-rights waiver has been invented.

Migration chain now includes26 customer KYC and27 reveal/refund/credit history after25. Deploy API/frontend from the same reviewed immutable source; preserve all history and do not auto-downgrade. Local tests use actual PostgreSQL locks and signed simulated events. Actual Razorpay sandbox/refund integration and production approvals remain separate.
