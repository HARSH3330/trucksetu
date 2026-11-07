# Account email setup and controlled delivery — 25 October 2026

## Provider and private configuration

The current adapter is generic SMTP with STARTTLS, now using an explicit certificate/hostname-verifying SSL context. There is no vendor SDK or identifiable configured SMTP vendor in the local settings inspected. The adapter can be reused with an existing provider that supports authenticated STARTTLS; do not assume that the registrar, the public support mailbox or the existing DMARC report destination identifies the sending provider. Implicit TLS-only SMTP requires a separate adapter change; do not enter that provider's implicit-TLS port into the STARTTLS adapter.

Presence only, checked locally without displaying values:

| API variable | Current local state | Owner input |
|---|---|---|
| SMTP_HOST | Missing | Provider-issued SMTP hostname |
| SMTP_PORT | Present through application default | Confirm provider's STARTTLS port |
| SMTP_USERNAME | Missing | Provider-issued SMTP username |
| SMTP_PASSWORD | Missing | Provider-issued SMTP password/app password |
| EMAIL_FROM | Missing | Approved sender address/identity |
| EMAIL_REPLY_TO | Missing; now supported, optional | Monitored reply mailbox if different from sender |
| PUBLIC_FRONTEND_URL | Missing; now supported | Canonical frontend origin for this environment |
| ACCOUNT_EMAIL_COOLDOWN_SECONDS | Present through application default | Optional server-side cooldown override |

Enter credentials privately in the repository-root `.env`:
`C:\Users\harsh\OneDrive\Desktop\english learning\logistic\trucksetu\.env`.
A blank credential template now exists at this path and is Git-ignored; checks found no existing root/backend .env or .env.txt before creating it. The owner selected Brevo, but SMTP credentials are not yet populated in this template. The workspace-local run-local-maps-api.py launcher now explicitly switches to the repository root before importing Settings, making this file selection independent of the calling directory. Other startup commands must use the repository root as working directory because production Settings retains its existing relative `.env` behavior. Do not put SMTP variables in `.env.local`, VITE-prefixed variables, screenshots or chat. Do not copy production database/payment/storage configuration into local email testing. Supplying credentials does not authorize real sends; keep tests on overridden capture adapters until separate approval.

Set PUBLIC_FRONTEND_URL to `http://127.0.0.1:5173` for the existing local website. The local API address is not the frontend link origin. For a future approved production configuration, use `https://www.transivox.in`: read-only public HEAD checks observed apex308 redirecting to www, and www200. Set an isolated preview's own HTTPS frontend origin in its API configuration; never use production links for synthetic preview accounts. No production configuration was changed. Origin-only validation rejects credentials, query strings, fragments, paths, unsupported schemes and non-loopback HTTP; production additionally requires HTTPS. ALLOWED_ORIGINS remains a separate CORS setting and must include the appropriate frontend. Generated account tokens/codes use fragments, not HTTP query parameters; the UI clears a valid sensitive fragment after loading and requires explicit submission.

## Sender verification, receiving mail and DNS

The owner must identify the existing SMTP service/account and approve the EMAIL_FROM identity and, if used, EMAIL_REPLY_TO identity. Verify the sender/domain in that provider. Some providers also restrict Reply-To addresses; follow that provider's actual requirements rather than assuming it must always be verified. Reply-To must be a monitored receiving address if replies are expected. A transactional sending service does not necessarily provide an incoming mailbox: create or reuse a mailbox/alias with a receiving-mail provider separately where required. A sending-only From identity does not by itself require a receiving mailbox, but its verification method may require access to one.

Read-only DNS on25October2026, using Windows DNS and Google public DNS HTTPS resolver:
- transivox.in MX: successful DNS response with no MX answers.
- transivox.in root TXT: successful DNS response with no TXT answers; no root SPF observed.
- _dmarc.transivox.in TXT: existing DMARC quarantine policy, relaxed alignment and an existing report destination. Preserve the record and report destination; this observation does not establish control of that reporting service.
- DKIM selectors are provider-specific and cannot be reliably enumerated. No selector/target was guessed.

Before proposing any change, obtain the provider dashboard's exact domain-verification TXT/CNAME, DKIM selector names/types/targets, SPF instructions (including which domain they apply to), and any custom MAIL FROM/bounce-domain records. Some providers require MX on a bounce subdomain; distinguish those from receiving-domain MX. Recheck each exact owner/name and current TTL immediately before a separately approved change. Preserve all unrelated records and existing MX. Maintain at most one SPF TXT policy per owner name; merge authorized senders into an existing policy if one appears on recheck, rather than creating a duplicate. Preserve the current DMARC quarantine policy and verify SPF or DKIM alignment before real delivery. Do not invent provider DNS values or weaken DMARC to make a test pass.

Sources: [SPF single-record requirement](https://www.rfc-editor.org/rfc/rfc7208#section-3.2), [Python SMTP TLS documentation](https://docs.python.org/3/library/smtplib.html#smtplib.SMTP.starttls).

## Real-delivery plan — NOT RUN, requires separate approval

1. Owner supplies provider/account identity, private SMTP fields, approved From/Reply-To, exact provider DNS instructions and ONE recipient they control. Confirm that recipient may be used for synthetic registration and recovery and that testing remains on isolated PostgreSQL.
2. Read-only check provider sender verification, quotas/restrictions, required TLS mode and DNS propagation/alignment. Obtain explicit approval before any needed DNS changes; no such approval is inferred here.
3. After explicit send approval, register that one synthetic account through the local website. Record only send acknowledgement and sanitized audit state. Recipient privately confirms inbox/spam receipt, From/Reply-To and SPF/DKIM/DMARC results from message headers. SMTP acceptance is not proof of inbox delivery.
4. Open the verification link on the computer running the local website (or an approved isolated HTTPS preview). Confirm no automatic verification, submit explicitly, verify account state, then reject reuse/invalid/expired codes. Do not paste received tokens or passwords into chat.
5. Exercise resend cooldown and existing rate limits with local capture; avoid unnecessary real messages. Unknown accounts must retain the same public recovery/resend response.
6. Request one reset to the same designated recipient. Confirm receipt and canonical frontend origin, explicitly set a new password, verify old access and refresh sessions fail, new login succeeds, and reset-token reuse fails. Exercise expiry, invalid tokens, provider errors and rate-limit negatives locally to avoid repeated real sends.
7. Record separate outcomes for SMTP acceptance, mailbox receipt, authenticated domain alignment, UI completion and session invalidation. Do not call an unacknowledged send delivered. No real email has been sent during this work.

## Remaining contract decision

Recovery/resend responses are generic across known/unknown/ineligible/send-error accounts. Registration retains the existing immediate-session behavior and duplicate-account409 response. Therefore full signup non-enumeration is NOT achieved. An email-first signup redesign must be explicitly scoped rather than disguised as a mail-adapter fix. Phone OTP, payments, maps and production deployment are outside this email change.
