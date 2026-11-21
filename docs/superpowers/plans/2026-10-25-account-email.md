# Account email continuation — 25 October 2026

Owner-authorized scope: local implementation and verification only; no actual provider delivery, DNS mutation, deploy, push or payment changes.

Preserve session issuance, browser HttpOnly cookies and auth-version/refresh-session invalidation. Reuse generic STARTTLS SMTP adapter; explicitly validate TLS certificates. Add server-only canonical frontend origin, fragment-based account links with explicit form submission, optional Reply-To and configurable resend suppression. Issue registration verification through the same adapter after persisting the account/session. Keep unconfigured delivery nonfatal to registration. Use synthetic accounts, unique isolated PostgreSQL schemas, mocked delivery and a loopback TLS catcher. Record actual DNS observations and provider inputs; do not invent vendor DNS values or mailbox identities.

Non-enumerating signup is an explicit contract limitation: immediate authenticated signup and existing duplicate-account responses remain unchanged under the instruction to preserve authentication behavior. Recovery/resend responses stay generic. An email-first signup redesign requires a separate scoped decision.

Verification: regression failures first, affected SMTP/recovery/link and cookie/rate-limit tests, real isolated PostgreSQL token lifecycle and registration/cookie journey, local TLS catcher, desktop/mobile browser simulations, TypeScript and build. No broad audit or unrelated suite reruns.
