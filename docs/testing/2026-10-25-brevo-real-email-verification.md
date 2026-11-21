## Owner follow-up and remaining local checks — 26 October 2026 IST

Owner reports all three messages received in ONE unspecified approved Gmail mailbox, all with SPF/DKIM/DMARC PASS. This is owner-provided evidence; mailbox identity, Inbox/Spam placement and second-mailbox receipt remain unconfirmed. Do not assign this confirmation to a particular recipient or infer deliverability for all recipients. No further external emails were sent.

The new isolated PostgreSQL race/negative regression passed: three concurrent resends create one message and one verification row; concurrent verification consumes once; concurrent resets produce one success/one rejection and one auth-version increment; wrong/expired tokens do not change the password; old access/refresh sessions fail after reset; provider failure and unknown-account requests have equal generic responses. External SMTP was explicitly forbidden in that test. A loopback-only TLS catcher also confirmed the ordinary account factory's security subject and Reply-To, and rejected an untrusted certificate before sending. This closes the subject check locally, not as a new Brevo-delivery claim.

# Real Brevo SMTP verification — 25 October 2026 IST

Owner explicitly authorized registration verification, resend and password-reset delivery ONLY to two named Gmail addresses. Recipient identities are retained in the workspace-only allowlisted runner and local test database, not repeated in this report. No other recipients were used. No production/DNS/deployment/payment action; verified Razorpay integration untouched. Existing dirty branch and HEAD preserved.

## Actual integration results

| Check | Result | Evidence |
|---|---|---|
| Isolated local database | PASS | Exact127.0.0.1:55432/transivox_e2e; current_user transivox_e2e_user, no superuser/create-db/create-role; APP_ENVtest, KYC simulationfalse, real and sandbox checkoutfalse |
| Brevo STARTTLS/authentication | PASS (REAL) | Port587, provider advertised STARTTLS; certificate/hostname-verified upgrade, TLSv1.3 and successful SMTP authentication |
| Registration delivery | PASS for SMTP acceptance (REAL) | Two new synthetic customer accounts, one per approved address; each provider-accepted message recorded only after send_message accepted recipient |
| Immediate resend cooldown | PASS | Generic202 and zero extra sends for each account; existing cooldown unchanged |
| Resend after cooldown | PASS for SMTP acceptance (REAL) | Waited62seconds for configured60-second cooldown, one additional accepted message per account |
| Verification | PASS | Superseded code400; current code200; same code reuse400, both accounts |
| Reset delivery | PASS for SMTP acceptance (REAL) | One provider-accepted reset email per account |
| Reset single-use and sessions | PASS | Current reset token200, reuse400; existing access401 and refresh cookie401; new-password login200 then logout204, both accounts |
| Actual message link origin | PASS | Guarded sender parsed each actual message only in memory, matched recipient and exact local frontend origin; token/code in fragment, no HTTP query token; frontend HEAD200 at http://127.0.0.1:5173 |
| Recipient restriction | PASS | Hard allowlist, maximum six send attempts; actual accepted total6, exactly3per approved recipient |
| Inbox versus Spam receipt | BLOCKED | Recipient confirmation requested; SMTP acceptance alone does not establish mailbox receipt |
| SPF/DKIM/DMARC at recipient | BLOCKED | Asked owner to inspect Gmail Show original and report result statuses only; no inbox integration/headers available |
| Browser UI | NOT RUN in this real SMTP journey | Real API code exercised through in-process HTTP ASGI transport using the same local DB/config as running API; prior2desktop/mobile simulated browser cases retained separately |
| Expired/invalid token negative cases | REUSED local evidence | Prior local recovery tests, not extra real sends and not claimed as a new provider-delivery test |

## Scope and limitations

The SMTP sender wrapper enforced the approved recipients and captured message bodies only in process memory to inspect/use codes and tokens. No password, credential, body, verification code, reset token, token-bearing link, access token or refresh cookie was printed or written to evidence. Actual SMTP acceptance came from the unmodified real SmtpEmailProvider, not a fabricated acknowledgement. The same PostgreSQL data is accessible to the ordinary local API, so the email origin is consistent with the local website. Both local test accounts were newly created only after confirming the approved addresses had no existing local accounts; no prior account was overwritten. Final fresh sessions were logged out. Retained synthetic account rows are identifiable as Owner Authorized Email Test.

The guarded test wrapper called the adapter directly, so these six emails used its default subject “TransivoX booking update”. The ordinary account-email dependency uses “TransivoX account security”; its subject was not validated through real delivery in this run. This is a harness limitation, not evidence that the production factory uses the booking subject. No extra sends were initiated to repeat the journey. All links/codes used by automated verification/reset have now been consumed; recipient checks should inspect receipt and authentication results, not expect those links to remain usable.

The first local preflight failed before SMTP due to Windows drive-directory pseudo-environment entries being incompatible with os.environ assignment. Corrected only the workspace test harness to exclude those pseudo-entries while preserving application variables. No messages or SMTP connections occurred in those failed preflight attempts. No application source change was needed during this real provider run.

## Sanitized evidence and remaining action

Workspace evidence: outputs/2026-10-25-brevo-authorized-email.json; runner verify-brevo-authorized-email.py (not Git source, guarded against rerunning existing accounts). This report contains only sanitized state/status evidence; provider SMTP queue/message IDs are not exposed by the current adapter, so no IDs are invented.

Owner: confirm Inbox/Spam/no receipt separately for each approved address; in Gmail Show original report only SPF/DKIM/DMARC PASS/FAIL where available. Do not share message bodies, codes or links. No authentication-record/DNS change is proposed without those results and exact provider instructions. Mailbox receipt and domain-authentication readiness remain unverified until that evidence arrives. No further send is scheduled or automatically retried.
