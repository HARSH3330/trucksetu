# Customer-led marketplace local verification

Recorded 23 October 2026 (IST). Local uncommitted candidate on `codex/launch-preparation-no-otp-maps`, base HEAD `ba3057784e36f1c984e90f54b0695586a8c97650`. No commit, push, deployment, production migration, cloud change, real payment or external send. This report supersedes the old isolated-verification next task; it does not grant launch approval.

## Delivered locally

Customer-led landing/navigation; server drafts and review/publish composer; private-safe verified-provider demand discovery; versioned bids and comparison; single-winner selection with immutable quote/fee/contact snapshots; separate INR 1,000 per-booking fee ledger; backend captured-payment contact unlock; purchased-contact reopening; later verified driver included; read-only admin fee/event review. New additive migration `20261021_25` preserves existing request/quote/booking/history tables. Existing shared publication, search, reservation and explicit acceptance remain independently enabled. Legacy full-vehicle allocation and freight collection are retained behind explicit flags.

Promised verified provider or preassigned driver contact is checked before checkout and again before disclosure. A provider contact purchase is labelled as such, without charging for a pending driver. Phone details are available only through the owning customer's protected contact endpoint; list/bid/snapshot/audit records contain no purchased phone. Contact access requires matching captured order/amount/currency, current selection eligibility and contact proof. Later driver assignment does not issue another fee order.

## Fresh completed checks

| Check | Result and scope |
| --- | --- |
| Backend unit/security/workflow suite | 360 passed; retained-flow regression command explicitly enables legacy allocation and transport collection in that local process only |
| PostgreSQL integration suite | 41 passed, 1 skipped, 182.16 seconds; sequential guarded local DB only |
| Frontend unit suite | 46 passed; final repeated Windows thread-worker run also passed 46 |
| Frontend build | TypeScript and Vite passed; final bundle 499.70 kB, CSS 85.36 kB |
| Browser marketplace journeys | 3 passed, zero failures/retries/skips: 1440, 768, 390 pixels; separate customer/provider/other-customer/admin contexts |
| Backup/restore | Passed: 54 public tables including temporary probe had matching row counts/SHA256 fingerprints; deliberately deleted marker restored and temporary probe removed |
| Migration checks | Isolated PostgreSQL through 25; unit migration-chain/offline SQL checks passed; existing migration/history regressions included |
| Focused lint, browser TypeScript, diff whitespace | Passed |

The integration skip is `PILOT_E2E_DATABASE` opt-in signup/auth smoke. It was not enabled for this run. Cookie/session/refresh/logout database integration cases did run. Do not describe the skip as passing.

Browser cases cover server draft save/resume; package-volume computation; publish; provider bid; fee/freight separation; stable selection; simulated order; forged/wrong-amount/wrong-currency event rejection; matching signed capture; duplicate webhook; owner-only contact; reopening without another order; independent provider assignment; later driver without another fee; admin access; keyboard focus and mobile/tablet overflow. Screenshots were inspected at desktop and mobile widths. An additional final shared-publication check is recorded separately below.

The main three browser journeys preceded the final narrow restoration of shared publication. Current backend guard regressions, frontend unit/build and a separate primary-experience shared-publication browser check cover that correction. Historical eight retained browser journeys passed earlier in this task before the major product change; they are dated evidence and were not relabelled as fresh final-candidate coverage.

## Reproduced defects fixed

- Request creation explicitly reloads cargo/stops after persistence to prevent asynchronous relationship serialization failure.
- Missing signed order/payment references are rejected before reconciliation.
- Unmatched authenticated refunds/disputes are persisted; later capture cannot unlock a previously refunded/disputed contact.
- Expired/uncertain gateway orders block another selection fee pending reconciliation. Repeated order calls reuse the same recorded order.
- Old freight order reuse cannot evade the disabled transport-collection guard.
- Selection frontend idempotency key now meets server length limits while remaining stable for the quote/version.
- Provider tabs refresh after independent customer activity; captured selection labels update without discarding the purchased contact.
- Expiry cancels provisional trips. All new-demand trip operations require eligible captured selection evidence, closing the reviewed unpaid-trip path and releasing resources.
- Shared publication is governed by shared-capacity/compliance gates, independently of the legacy full-vehicle allocation flag.

Focused read-only security review found the expiry defect; its unit and PostgreSQL regressions failed before the fix and passed afterward. The reviewer inspected the exact fix and reported no residual finding in those changed guards. This is a focused review, not an independent production security audit.

## Isolation and recovery evidence

Only existing Docker container `transivox-e2e-postgres`, volume `transivox_e2e_postgres_data`, host `127.0.0.1:55432`, database `transivox_e2e`, restricted role `transivox_e2e_user`. Guards require explicit exact-name/local-host E2E URL, APP_ENV=test, TRANSIVOX_E2E=true, E2E_REAL_AWS=false. No production/Preview/Neon fallback. Public schemas are reset only by guarded browser setup; integration cases use isolated schemas or transactions. Runs were sequential for database work.

Docker was unavailable after interruption. Bounded startup initially timed out, then existing Desktop/container reached ready; identity/connectivity passed before restore. No factory reset, purge, volume deletion, WSL shutdown or infrastructure change. Preserve private DPAPI helpers, virtualenv and existing ignored artifacts. The restore dump contains synthetic fixture data and remains in local work, not source control or public deliverables.

Payment gateway calls and captured events are simulated in the guarded E2E app. Compliance prerequisites are explicit fictional version-bound fixtures, not real scanner approval. No Razorpay transaction or real money was collected. Preserve immutable VersionId scan/manual-review gates.

## Limits and release decisions

Real checkout stays disabled. Tax treatment, cancellation/refund rules, provider-failure handling and replacement-provider fees remain undecided. Customer document-KYC policy remains open; local policy uses existing account verification without inventing new documents. The new demand path supports one suitable vehicle per award; multiple-vehicle/split-load support is a separate scope decision. Shared-capacity functionality and historic data remain retained. Practical contact-text filtering does not claim to defeat all obfuscation.

Unmatched gateway-before-order-record events require reconciled operations review; no manual unlock, automatic refund or repeated charge is supplied. Refund/dispute/contact invalidation locks future access but cannot undo a contact previously seen.

Before real activation: commercial/customer-verification decisions, actual gateway sandbox reconciliation, exact-version scanner acceptance, delivery/alert/recovery evidence and independent release/security/legal/privacy/tax review. Production migrations 23/24/25 and coordinated API/frontend deployment need separate explicit approval. Historical production/main `ccd594d` observations are from 21 October and were not rechecked here. Do not run production E2E or destructive downgrades.

See [retention/configuration/release guidance](../operations/customer-demand-marketplace.md), [specification](../superpowers/specs/2026-10-21-customer-demand-marketplace-design.md), [plan](../superpowers/plans/2026-10-21-customer-demand-marketplace.md) and the source manifest produced alongside this report. Continue from these focused records; avoid a new broad audit.


## Final shared-capacity and source evidence

Final primary-experience shared-publication browser case passed: 1 test, 27.6 seconds, 390 pixels, legacy full-vehicle flag false. Opened the preserved publication disclosure, verified the form and Publish route control, confirmed the API reached its own 422 payload validation rather than the legacy 409 gate, and checked no horizontal overflow. Initial focused assertion forgot to open the disclosure; its failed trace is preserved in local work. No product gate was weakened to make the check pass.

[Final changed-source manifest](2026-10-23-customer-demand-source-manifest.json): 48 changed source/config/test files atop ba305778; combined SHA256 `92de6d1387ac93a578293dfba9acb84925704cf4ce899597bc3bc220daaa4967`. Documentation and generated/ignored artifacts are excluded. The source remains dirty/uncommitted. Use the source manifest and test records together; a hash alone is not test evidence.

Local verification work is complete. The next step is commercial/customer-verification decisions and separately approved real-integration/release review, not another project audit. No production action is authorized by this report.
