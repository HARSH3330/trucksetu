# Razorpay Test Mode refund execution and verification — 23 October 2026

User authorizes isolated sandbox orders/payments/refunds and a narrowly exposed HTTPS webhook; no live money, production settings, push or deployment.

Use the existing HTTPX gateway and additive refund execution fields (migration28). Keep a CLI-only explicit sandbox refund executor: no new public refund-control route. Persist immutable payment reference, payload and one provider idempotency key before any external call. Before retries, list the payment's refunds and match the durable obligation reference; fetch the specific refund and payment before recording completion. Unknown HTTP outcomes retain the same key/body; pending and failed provider refunds are fetched again rather than recreated. Mismatched or unrelated refunds require review; never declare completion from a request acknowledgement. All transitions use selection-first then refund locks; network calls occur outside transactions. Provider idempotency protects overlapping executors/crash recovery.

The alternative of blind retries is unsafe; recording manual refunds alone cannot verify the requested integration. No new background infrastructure is necessary for this controlled test; automatic live refund execution stays unavailable.

Test-only gateway mode requires APP_ENV=test, explicit ENABLE_RAZORPAY_SANDBOX, rzp_test_ credentials, and an exact loopback dedicated E2E database URL/role/port. Test fee policy is illustrative ₹1000 + ₹200; tax-confirmed and live flags remain false. Waiver checkout is blocked for real Test Mode too; no positive waiver tax or fake free capture.

Public relay exposes POST /api/v1/connection-fees/webhook only, bounded body and request time, constant loopback upstream, HMAC validation; all admin/reset/bootstrap/docs/test endpoints 404. Tunnel only the relay, never the internal API/browser test server. Synthetic actors and local KYC prerequisites must be labelled simulations.

## Execution plan
- [x] Check Git and latest evidence; credential presence and exact local DB identity.
- [x] Add failing HTTP-adapter and isolated PostgreSQL refund retry/reconciliation tests.
- [x] Implement sandbox guard, immutable attempt persistence, idempotent adapter and CLI runner; strengthen refund event binding.
- [x] Run focused tests including concurrency, failure, invalid response, refund events, checkout guard and relay isolation.
- [x] Prepare and verify HTTPS relay and secure credential entry.
- [ ] Run actual Razorpay journey: blocked on missing Test Mode credentials.
- [x] Record actual blocked outcomes separately from simulations; update handoff and remaining blockers.

Official references: https://github.com/razorpay/markdown-docs/blob/master/api/refunds/normal-refunds-idempotent.md ; https://razorpay.com/docs/api/refunds/create-normal/ ; https://github.com/razorpay/razorpay-python/blob/master/documents/refund.md . A processed refund is final provider processing, not proof of real bank receipt (there is no real bank transfer in Test Mode).
