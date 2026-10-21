# Operator gates: alerts, recovery and policy inputs

Prepared only. No alert subscription, retention, cloud service or restore is
activated. Proposed thresholds require owner/on-call approval.

## Actionable alert proposal

| Signal | Proposed trigger | Owner action |
|---|---|---|
| Readiness | 3 consecutive failures over 3 minutes | Operator checks sanitized DB/Redis diagnostics; no automatic migrations/restarts |
| API 5xx | >2% with >=20 requests over 5 minutes, or 3 consecutive auth/server errors | Correlate request IDs/source SHA, identify dependency/schema issue, pause rollout |
| Auth/session | sustained 401/429 spike >3x normal baseline | Check abuse, rate limits, cookie/CORS topology; never disable protections |
| Payment | capture mismatch or late_confirmation_requires_review audit event | Finance owner reconciles gateway/order/currency/policy; never auto-refund |
| Scanner | resource Warning/Error, tag failure, nonclean result, or no scan completion after 15 minutes | Keep approval blocked, inspect exact-version permissions/plan metrics |
| Capacity | negative-capacity constraint failure or repeated allocation conflicts beyond baseline | Stop new affected route operations, inspect idempotency and transaction evidence |
| Backup | last successful backup older than approved RPO; last restoration older than approved interval | Operator verifies encrypted backup and performs isolated restore |

Required owner inputs: primary/backup operator, notification channel and approved
recipient, service hours/escalation, RPO/RTO, log/backup retention and budget.
The public support hours are not an agreed 24/7 incident response SLA.

API emits structured http_request/request_error events and X-Request-ID. Current
local patch removes raw exception traces/messages from middleware. Do not export
Authorization/Cookie headers, body/SQL parameters, email/token, S3 key/filename,
signed URLs or identity contents. Default Vercel runtime logging alone is not a
configured alert. `SENTRY_DSN` currently exists as a setting but has no active
instrumentation; setting it alone does not create monitoring. Choose the existing
Vercel/log platform or approve an integration before claiming alerts are active.

## Local restoration

BLOCKED: Docker Linux engine /version returns HTTP500 and guarded local PostgreSQL
does not respond. No database replacement/reset, Docker factory reset, daemon
restart or unrelated-volume deletion was attempted. Existing
`scripts/backup-postgres.ps1` targets the development compose database, NOT the
restricted transivox_e2e target; do not use it as a production backup recipe.

After Docker repair, use only the restricted transivox_e2e role and approved local
host. Create harmless disposable schemas, run real migrations and insert fictional
rows, capture schema/count/checksum evidence, dump to a protected ignored local
directory, restore into a separately isolated exact-name transivox_e2e instance
on another loopback port, compare schema/data/constraints, and exercise reads.
No production backup input; this proves local restoration mechanics only. Review
resolved container/volume IDs before cleanup and retain evidence separately.

## Production restoration rehearsal proposal

1. Confirm exact production project/branch/endpoint/neondb binding privately.
2. Obtain explicit approval for a fresh recovery point and isolated restore
   branch/compute, including charges, access restrictions and expiration.
3. Verify current revision/critical row counts and recovery freshness. A current
   copy is not evidence of historical restore or recoverability.
4. Restore a selected retained historical point into a new branch; do not reset
   production, overwrite retained recovery branches or route real traffic there.
5. Restrict access, disable outbound delivery/payment/scanner actions, compare
   expected schema/counts/approved non-sensitive fingerprints and run read-only
   app checks. Record elapsed time and achievable data-loss window against RPO/RTO.
6. Owner reviews evidence and expiry/retention/cleanup. Never automatically
   downgrade migrations 23/24 or claim lossless production rollback.

Existing recovery branches are retained, not modified. Before any approved
candidate rollout, migration 23's legacy provider/assignment impact must be read
from the applicable production environment; local fixture emptiness is irrelevant.

## Policy and business inputs still required

| Item | Current evidence | Owner/professional input |
|---|---|---|
| Terms | versioned consent exists; draft pending legal review | qualified approval of final entity, liability, marketplace and jurisdiction text |
| Privacy | separate published policy absent | controller identity/contact, purposes, processors, sharing, rights, grievance and retention |
| Cancellation/refunds | booking snapshot and operator refund-recording logic exist; separate public policy absent | final cancellation/refund rules and processing expectations matching code |
| KYC/Aadhaar | private versioned manual review; scan-clean not authenticity | necessity/consent/legal basis, accepted documents, retention/deletion, access and incident process |
| Business identity | TransivoX brand and provided support email/hours known | registered legal name/type, address, GST/issuer details where applicable; do not invent them |
| Financial disclosure | provider final quote, assistance/extra-stop/night/waiting charges | commission/tax/toll/parking/gateway-fee rules and invoice responsibilities approved by professional |
| Service coverage | feature flags and controlled geography exist | approved launch cities/operations/cargo restrictions/support ownership |

No speculative legal conclusions or final policy text is published by this task.
Independent penetration testing and qualified Indian legal/privacy/tax review
remain separate external gates, not satisfied by this engineering review.

## Unresolved product scope (not approved omissions)

- Google sign-in: no implemented OAuth route/provider configuration identified;
  adding it needs identity-linking, duplicate-account and consent decisions.
- Phone-only login: current widget verifies a signed-in phone, not login; needs
  recovery/ownership/session and abuse rules. OTP is deferred for this package.
- Recurring requirements: scheduled one-off shipments exist; recurrence series,
  per-instance quote/booking/cancellation/time-zone rules need a scope decision.
- Broader admin configuration: focused admin actions exist, not a general settings
  editor; clarify allowed fields, privilege/audit and financial effective dates.
- Maps remains deferred. Real distance/time evidence and route suitability without
  manual review cannot be claimed. Actual pickup/delivery verification cannot be
  fully proven while real OTP delivery is deferred; local fakes are not delivery.
