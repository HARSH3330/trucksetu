# Account email verification — 25 October 2026

Scope: current dirty feature/customer-first-marketplace candidate at unchanged ba3057784e36f1c984e90f54b0695586a8c97650. All existing changes preserved; no commit/push/deploy, production mutation, DNS mutation, real email, or payment integration activity.

Read [private setup, DNS observations and controlled recipient plan](../operations/account-email-setup.md).

## Changes

- Registration now attempts verification delivery through the optional email dependency after committing the account, verification record and session. Delivery configuration/failure does not remove the existing registration session behavior. Browser signup passes the dependency explicitly and retains HttpOnly refresh cookies; no refresh token is added to the browser JSON response.
- Generic SMTP adapter explicitly supplies a CA/hostname-verifying SSL context before login or sending. Optional server-only EMAIL_REPLY_TO is supported. SMTP refusal remains failure; acceptance is not inbox delivery.
- Added validated server-only PUBLIC_FRONTEND_URL and fragment links for verification/reset. Existing manual code/token entry remains usable when links are not configured. The browser consumes a valid link into masked reset/token state, clears its fragment through replaceState, and requires explicit form submission. No verification/reset mutation occurs simply by opening a link.
- Added ACCOUNT_EMAIL_COOLDOWN_SECONDS with a60-second default. Recovery/resend checks the latest durable record while holding the existing user row lock; repeated requests return the same generic202 without another send. Existing outer rate limits are preserved. No new migration.
- Corrected new-password accessible naming: explanatory requirements now use aria-describedby rather than becoming part of the input label.
- Updated root and isolated-preview environment examples with blank new optional configuration fields. No credential file or actual value was added.

## Results

| Check | Result | Evidence/scope |
|---|---|---|
| SMTP acceptance/refusal and verified TLS, safe frontend-link generation/validation, recovery expiry/reuse/attempt limits/generic responses/session invalidation | PASS | Combined affected backend run24passed, including two real isolated PostgreSQL cases; mocked/in-memory delivery only |
| Browser-cookie and existing rate-limit contracts | PASS |20passed in separate focused run; no real email |
| PostgreSQL registration, cookie issuance, verification delivery and immediate-resend suppression | PASS | Final strengthened case1passed: registration, unknown/known resend response equality, no duplicate send, reset-token reuse400, old access401, old refresh cookie401, new-password login200 |
| PostgreSQL verify/reset lifecycle | PASS | Unique schema in loopback127.0.0.1:55432/transivox_e2e; restriction guard passed; expired/reused tokens rejected, old access denied after reset; schema cleaned only by its generated identifier |
| Actual SMTP protocol/TLS loopback capture | PASS | Workspace verify-local-smtp.py; one synthetic message captured over STARTTLS, Reply-To checked, untrusted certificate rejected before message transmission; outputs/2026-10-25-local-smtp-capture.json outside Git |
| Frontend email-link parser and AccountSecurity rendering | PASS |6focused unit tests passed again after the accessibility adjustment |
| Desktop/mobile email links and explicit submission | PASS (SIMULATED API) |2Playwright cases1440/390px; all non-loopback requests blocked; reset fragment removal, masked prefill, no automatic POST, explicit reset, clearing token and independent verification link; no screenshots/traces enabled |
| TypeScript and Vite build | PASS | npm run build, also rebuilt by final successful browser run; existing nonfatal >500KB bundle warning remains |
| Affected Python lint | PASS | Ruff affected files; git diff --check passed before final documentation write |
| Public DNS/canonical web origin | PASS (read-only observation) | Two resolvers: no MX/root TXT answers; existing DMARC quarantine preserved; apex308 ->www, www200 |
| SMTP vendor/sender credentials and provider-specific DKIM status | BLOCKED | No local SMTP host, username/password or sender configured; provider identity/selector records not known |
| Actual email-provider acceptance, recipient mailbox receipt, spam placement and domain authentication | BLOCKED / NOT RUN | Owner inputs and separate send approval required; zero real sends |
| Full signup account-enumeration resistance | FAIL (existing contract limitation) | Duplicate-account409 retained alongside immediate authenticated signup. Recovery/resend are generic. Requires a scoped signup-contract decision; not falsely labelled solved |

Initial expected regression failures confirmed the missing verified TLS context, email-link modules, cooldown suppression and registration delivery dependency. First browser attempt failed on the existing password label including helper text; fixed the actual label and both cases passed. Strengthened registration test initially missed the required-sender capture override and returned503; corrected the test dependency override only, then it passed. These do not represent unresolved final test failures.

## Remaining inputs and next action

Owner: identify existing SMTP service/account; privately supply SMTP_HOST/SMTP_PORT/SMTP_USERNAME/SMTP_PASSWORD/EMAIL_FROM; choose optional monitored EMAIL_REPLY_TO; supply provider-issued sender/domain authentication records and one approved test recipient. PUBLIC_FRONTEND_URL local http://127.0.0.1:5173 and future approved production https://www.transivox.in; production/preview configuration is not changed. Reuse existing service if it supports STARTTLS; do not purchase or switch providers speculatively. Sender-domain verification does not provision a receiving mailbox. Preserve MX, the current DMARC record and any SPF policy discovered on immediate pre-change recheck; never create duplicate SPF policies. Real delivery requires separate explicit authorization, using only the designated recipient and isolated database. No user secret or received token belongs in chat.
