# Isolated preview and exact release sequence

Proposal only; no Vercel/AWS/Neon changes, push or deployment. Existing shared production/preview entries are unsafe for candidate previews until inspected and separated.

## Required isolation matrix

| Binding | Preview requirement | Production boundary |
| --- | --- | --- |
| VITE_API_URL | Dedicated preview API origin | Never transivox.in/live API |
| DATABASE_URL / migration URL | New empty isolated schema/database, restricted role | No production branch, clone with personal records or fallback |
| Redis | Separate instance/credentials | No production keys/namespace |
| Upload bucket | Separate private versioned preview bucket | Never production KYC data |
| Result bucket/worker/queue/DLQ | Separate preview scanner stack and IAM | Never consume production events/results |
| Payment | Test merchant credentials only; real checkout false | No live orders/charges |
| Email | Local/test capture or allowlisted sandbox delivery | No real-user sends |
| SMS/WhatsApp | Unset/disabled until an explicit isolated test plan | No production credentials |
| Sessions | Separate random secret, host/origin/cookie scope | No production login reuse |
| Customer policy | Approved real policy or fail closed | test_only policy forbidden outside APP_ENV=test |

Environment templates under ops/preview contain blanks, not credentials. Resolve exact URLs and resources in an operator-private configuration. Vercel git deployment behavior must be inspected and approved before a push. If no isolated preview exists, keep push blocked or separately approve a verified non-deploying publishing path. Do not change Git integration implicitly.

The scanner template takes an explicitly reviewed source bucket. For preview, provision a new private versioned SSE bucket with no real identity data first and pass its name. The production bucket must never be reused for preview. Notification fragments require exact reviewed merge; they are not replacement configurations. Approve every paid resource before creation.

## Compatibility and release checks

Additive migrations 23/24/25/26/27 retain history. The local current head is 20261023_27. Migration 25 adds demand/fee records; 26 adds customer KYC independently from provider/vehicle records;27 records reveal/refund/credit history and conservatively backfills historical contact audits. No downgrade is automatic; both newer migrations refuse destructive rollback. Recheck actual production revision before any separately approved release; the revision22 observation is dated 21 October. Local unit history/offline SQL and isolated PostgreSQL tests validate current chain, not production readiness.

Keep API/frontend on the same immutable candidate SHA; record scanner image digest separately. Resolve the provider-first-publication flag as an explicit scope decision; shared-capacity code remains retained. Real checkout and automated payouts stay disabled regardless of source publication.

## Deployment order after explicit approval

1. Final reviewed commit/source manifest, all applicable gates, personal AWS account/roles/scan workflow, policies and cost approval. No working-tree deployment. Prepare rollback API/frontend/image references and a protected DB backup; test a restoration in isolation. Recheck production schema/deployment identity immediately before release.
2. Rehearse preview empty-DB upgrade through27 and real harmless website upload -> exact-version scan -> backend registration -> authorized review -> eligibility. Confirm forged/pending/non-clean/error/unauthorized paths stay blocked. Verify correct cookie/CORS origins, alerts, no production traffic and no real charges/messages.
3. Approve production window and backup/restore point. Hold incompatible mutations/traffic while applying migrations23,24,25,26,27 exactly once using the reviewed migration artifact and privileged migration identity. Application runtime remains least-privilege. Stop on failure; do not deploy incompatible frontend or auto-downgrade.
4. Deploy API from the candidate SHA with real checkout disabled and scanner/customer configuration fail-closed until verified. Confirm /version exact SHA, liveness and readiness, schema head and role-specific authorization. Readiness alone does not prove scanner/gateway/storage/delivery.
5. Deploy frontend from the same SHA after API contract checks. Verify designated-account login/restore/logout, demand/quote/selection/booking screens and contact lock; only approved harmless test documents. Production is never the E2E target.
6. Enable KYC only after real deployed scanner/website exact-version/manual-review verification and legal/privacy approval. Live payments require a separate decision/approval for tax, refunds, provider failure and replacement fees plus actual sandbox reconciliation. Do not infer permission from hosting approval.
7. Monitor queue age/DLQ/heartbeat, API errors, auth and scan outcomes. If API is incompatible, hold traffic and forward-fix or roll back compatible artifacts; preserve all new data and immutable evidence. No destructive DB rollback.

Remaining user inputs are consolidated in the handoff/evidence report; no credentials should be pasted into chat.

Current fee rules and remaining decisions: see 2026-10-23-connection-fee-policy.md. Proposed20% tax is not confirmed. Real refund execution remains unapproved.
