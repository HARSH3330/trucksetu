# Razorpay Test Mode verification — 24 October 2026 IST

**Actual gateway journey is BLOCKED: Test Mode credentials have not been supplied. No Razorpay order, payment, capture or refund was initiated.** The missing sandbox refund execution/reconciliation path is implemented and tested locally. Public HTTPS webhook transport was verified, then temporary processes were stopped while waiting for keys.

Repository: https://github.com/HARSH3330/trucksetu ; branch `feature/customer-first-marketplace`; HEAD `ba3057784e36f1c984e90f54b0695586a8c97650` plus preserved local changes. No commit, push, production deployment, production migration or production configuration change. Read the new source manifest for current contents; older broad-suite evidence is dated and was not indiscriminately repeated.

## Isolation and configuration

Actual database identity query confirmed `127.0.0.1:55432/transivox_e2e`, role `transivox_e2e_user`, with superuser/create-role/create-database all false. Existing Docker PostgreSQL is loopback-published. Applied additive local migration `20261023_27 -> 20261023_28` without resetting data. No production or Neon connection was used.

`ENABLE_RAZORPAY_SANDBOX=true` requires `APP_ENV=test`, `RAZORPAY_KEY_ID` starting `rzp_test_`, `RAZORPAY_KEY_SECRET`, and the exact dedicated loopback DB/user/port with no URL query overrides. Every real adapter operation repeats this guard. `RAZORPAY_WEBHOOK_SECRET` is separate from the API key secret. Initial private configuration check found all three absent. No secret values were printed or committed.

The isolated test policy explicitly says ₹1,000 base + ₹200 illustrative tax = ₹1,200 (`120000` paise). `ENABLE_REAL_CONNECTION_CHECKOUT=false` and `CONNECTION_FEE_TAX_CONFIRMED=false` remain set. Real Test Mode orders use a separately permitted test-only fee policy; this does not enable live checkout. Waiver checkout is now blocked universally, including the old hypothetical test-tax override. No free-booking capture or waiver tax was fabricated.

## Implemented refund execution

- Additive migration28 stores the immutable payment reference, provider idempotency key, exact request payload, provider refund ID, attempt/error metadata and reconciliation time on the unique booking refund obligation.
- Explicit CLI `backend/connection_refund_sandbox.py REFUND_REQUEST_UUID` executes/reconciles one existing full refund. There is no new public executor, reset or bootstrap route, and no automatic live refund worker.
- Selection/refund locks serialize preparation and reconciliation. The exact key/body is committed before network activity; no DB transaction remains open during HTTP calls. Overlapping calls use Razorpay's same provider idempotency key. A timeout never means the refund failed to reach Razorpay.
- Before a new POST or uncertain retry, fetch the payment and its refunds. Match the obligation's receipt/notes; refuse unrelated refunds, mismatched payment/order/amount/currency and saturated listings. Existing pending/failed refunds are fetched rather than recreated. The same refund is fetched after a successful POST before recording its final status. Missing or failed provider evidence remains unresolved and contact-locked.
- Only exact bound `processed` evidence completes the obligation. `pending`, `failed`, `unknown` and `review_required` are distinct. An API acknowledgement is not completion. Signed refund events match payment, obligation/refund ID, full amount, currency and event/status; stale failed/pending events cannot regress a processed refund.
- A regression found failed status becoming pending after a later fetch timeout; fixed and verified. A separate regression found non-ASCII signature headers raising an exception; malformed signatures now return false.

Provider API references: [idempotent refunds](https://github.com/razorpay/markdown-docs/blob/master/api/refunds/normal-refunds-idempotent.md), [normal refund API](https://razorpay.com/docs/api/refunds/create-normal/), [official Python refund resource](https://github.com/razorpay/razorpay-python/blob/master/documents/refund.md). Stable idempotency headers/body and explicit provider status reconciliation follow these contracts. Refund status is provider processing evidence; Test Mode has no actual bank settlement.

## Actual evidence

| Boundary | Actual result |
|---|---|
| Focused unit/security/payment/migration checks | **67 passed**, plus expanded relay-path tests **2 passed**; overlapping counts |
| Affected PostgreSQL fee/refund suite | **26 passed**; includes simulated provider operations and previous fee tests |
| Final refund executor/webhook regressions | **9 passed**, including the failed-status timeout fix; overlaps the 26-case run |
| Exact refund binding + final blocked waiver/unique credit reservation | **2 passed**; overlaps other coverage |
| Ruff, diff whitespace, Python compilation, migration chain/offline SQL | Passed; single head28 |
| Public HTTPS path isolation | Unsigned webhook401; reset/admin/docs/contact paths404 |
| HTTPS -> relay -> API -> PostgreSQL | Locally signed unmatched simulated event200; replay200; invalid signature401; exactly one unmatched event, no booking/entitlement count change |
| Actual Razorpay Test Mode API/payment/refund/delivery | **BLOCKED: credentials missing**, not passed |
| Live operation | **UNTESTED / NOT AUTHORIZED** |

The 26-case run preceded the final universal waiver block and failed-status timeout correction; the final2 and9 focused runs verify those later changes. Counts overlap and are not a new full-project result.

The initial signed HTTPS attempt returned503 because the default Windows Proactor event loop is incompatible with psycopg async connections. A controlled same-DB comparison reproduced the error and passed using the selector loop. The private API launcher now uses the selector loop; the repeated public transport probe passed. Initial failure evidence is preserved.

Temporary HTTPS URL tested: `https://database-timing-engines-absent.trycloudflare.com/api/v1/connection-fees/webhook`. This was **not** a Razorpay-originated delivery. Cloudflared2026.10.3 came from the official Cloudflare release and matched published SHA256 `76b2805253d0d6ffacb092a7acfbee99e7af6917835c0c5410e23f3ef5052da2`. The tunnel targeted only the restricted relay on loopback18111, which forwarded the exact signed webhook path to the ordinary API on loopback18110. Bodies are bounded; signatures verified twice; authorization/cookies are not forwarded. No E2E router was mounted. The temporary tunnel, API and relay have been stopped; no18110/18111/18112 listener remains. Restart creates a new temporary URL, requiring an updated **Test Mode only** webhook registration.

## Requested journey outcomes

| Requirement | Local simulation / DB tests | Real Razorpay sandbox |
|---|---|---|
| ₹1,000 + ₹200; backend order; matching captured verification | Pass | Blocked |
| No automatic contact; explicit reveal; correct customer/booking; repeat access without another charge | Pass | Blocked |
| Separate pre-reveal full refund including tax and permanent cancellation lock | Pass, including adapter execution/final-status logic | Blocked |
| Duplicate events/requests and concurrent execution do not create duplicate obligations/refunds | Pass; public transport replay also passed with a simulated unmatched event | Blocked |
| Failed payment does not unlock; invalid signature/unrelated/wrong amount rejected | Pass; public invalid-signature transport passed | Actual gateway failure/negative journey blocked |
| Audited provider failure issues one credit; concurrent reservation single-use; waiver checkout blocked | Pass locally | No waiver payment attempted |

Sanitized actual provider references: **order IDs: none; payment IDs: none; refund IDs: none**. Names such as `order_local_*`, `pay_*fixture` and `rfnd_fixture` in tests are simulations and are not provider evidence. No real instrument, identity document or phone message was used. Existing frontend/browser/ClamAV/restore results remain dated evidence, not newly rerun integration claims. Independent security review and live refund operational readiness are not established.

## Remaining inputs and next action

1. Run the private secure-entry script below for the intended merchant's **Test Mode** keys and a dedicated test webhook secret. The script saves secrets with Windows-user DPAPI outside the repo and restricts the private folder. Never send values in chat.
2. Restart the guarded local API and webhook-only relay, register the resulting HTTPS path under Razorpay **Test Mode** with the same webhook secret, subscribing to `payment.captured`, `payment.failed`, `refund.created`, `refund.processed`, `refund.failed`. Do not edit Production webhooks or keys. The available connector is read-only; actual execution uses the guarded HTTP adapter. Dashboard access may be needed to register the Test Mode webhook.
3. Use synthetic accounts, explicitly simulated local compliance prerequisites and official test instruments for separate paid/reveal, paid/pre-reveal-refund and failed-payment bookings. Wait for actual provider capture/delivery, fetch the matching payment/refund status, and record sanitized references. Do not mark this report's blocked rows passed until that happens.

```powershell
& 'C:\Users\harsh\Documents\Codex\2026-10-21\read-docs-project-handoff-md-and\private-razorpay-test-entry.ps1'
```

Reply only **“test credentials saved”**. The existing tax/waiver-accounting, legal/privacy, scanner/preview and production release gates remain; they do not prevent the specifically authorized isolated sandbox test. Nothing here authorizes source publication or production money movement.
