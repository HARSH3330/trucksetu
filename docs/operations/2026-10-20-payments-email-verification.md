# Controlled integration verification proposal — no sends or payments authorized

## Razorpay

Connector read failed: Authentication failed / INVALID_ARGUMENT. That is not a
test of the website's API credentials. Reconnect the intended test merchant
privately. Connector tools are read-only and do not expose a test/live selector;
successful retrieval alone cannot establish test mode or create/refund payments.

API variables: `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`,
`RAZORPAY_WEBHOOK_SECRET`. Key ID is returned to checkout publicly; the two
secrets remain API-only. For the sandbox, privately confirm the key ID begins
`rzp_test_`, merchant mapping and an isolated staging database before writes.

Actual callback: `POST https://trucksetu-api-nine.vercel.app/api/v1/payments/razorpay/webhook`.
The existing code accepts `payment.captured`, validates the raw-body HMAC using
the webhook secret and checks order, amount, currency and captured status. It
requires `X-Razorpay-Signature` and `X-Razorpay-Event-Id`. `authorized` and order
creation are NOT successful payment. No browser-return callback marks funds paid.

Do not aim a sandbox webhook at production neondb. Create an approved staging
API/domain with isolated DB/Redis/secrets, then substitute its origin in the
callback above. Metadata/Preview labels alone do not establish isolation.

After separate approval:
1. Designate fictional customer/provider/admin accounts and one unpaid booking.
   Record its immutable total/currency and current state, no card/bank secrets.
2. Customer creates one test advance order through
   `POST /api/v1/bookings/{id}/payments/online`; repeat the same idempotency key.
   Assert one pending order/payment and server-calculated amount. Browser total
   tampering must not change what the gateway receives.
3. Complete one sandbox checkout using Razorpay's official test instruments.
   Authorized-only stays pending. Verified captured evidence updates ledger once.
4. Retry the identical event and a distinct event for the same capture. Assert
   one financial effect. Local negative tests cover bad signatures, mismatched
   amount/currency/status and malformed payloads; do not forge live webhooks.
5. Inspect payment ledger and booking through actual customer/admin contexts.
   A late capture cannot reopen a cancelled booking or rewind trip/dispute state;
   its audit entry requires an operator to reconcile money and policy.
6. Review the existing cancellation snapshot. A refund is not initiated by the
   current application gateway adapter. Owner must approve and execute a test
   refund in the test merchant dashboard, verify its processed result, then use
   `POST /api/v1/bookings/{id}/refunds/manual` to record that externally completed
   refund with a unique reference. Repeating it must not duplicate the refund
   record; exceeding approved refundable balance must fail. Do not present this
   admin recording endpoint as an automated Razorpay refund integration.
7. Issue/download the invoice record only when allowed by implemented state and
   configured issuer details. Compare stored commission/tax/net snapshots after
   changing staging settings; historical records must not recalculate.

Acceptance evidence: source SHA; staging isolation; order/payment/event/refund
references in a restricted ledger; totals/status transitions; duplicate behavior;
invoice snapshot. No full provider payload, card data or signature in reports.
Real sandbox lifecycle, concurrent webhook/cancellation and invoice delivery
remain unverified until actually executed. No change to commission/tax policy.

## Email

Existing adapter: `SmtpEmailProvider`, STARTTLS SMTP (not implicit SMTPS).
API-only variables: `SMTP_HOST`, integer `SMTP_PORT` (normally 587),
`SMTP_USERNAME`, `SMTP_PASSWORD`, `EMAIL_FROM`. Username/password are private;
do not put any SMTP setting in VITE variables. No email webhook/callback exists.

Owner prerequisites: choose the SMTP provider and approved sender identity;
privately configure credentials; copy the provider's exact SPF/DKIM DNS records
and choose a reviewed DMARC policy for the sender domain. Do not guess DNS values
or claim support-email ownership proves the domain is authenticated. Confirm TLS,
sender verification, test quotas and which recipient is approved for one send.

Actual flows:
- `POST /api/v1/auth/verification/resend` → generic 202, email verification code.
- `POST /api/v1/auth/verify-email` → email + code, expiring/attempt-limited/single use.
- `POST /api/v1/auth/password-reset/request` → generic 202, recovery token.
- `POST /api/v1/auth/password-reset/confirm` → email + token + new password;
  increments auth_version and revokes active refresh sessions.

These are code/token-entry flows in Account help, not invented emailed reset-link
routes. SMTP recipient acceptance is not mailbox receipt. The API deliberately
returns the same generic request response for unknown/ineligible/send-error
accounts to avoid enumeration; use private sanitized audit records to diagnose.

Approved real-delivery test: send to only the designated fictional account/inbox,
record SMTP accepted/not accepted without token/body, ask recipient to confirm
actual inbox/spam receipt, enter code/token privately in the website, verify old
code/token rejection after reuse/expiry/resend and old-session invalidation after
reset. Repeat unknown-account request without revealing account existence. Do
not ask the owner to paste received codes, passwords or provider credentials here.
