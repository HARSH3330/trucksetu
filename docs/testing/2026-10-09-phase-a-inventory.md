# Phase A — implementation inventory

Date: 2026-10-09. Scope: static repository inspection for the production-readiness roadmap. No tests, builds, database/cloud calls or deployments were performed. This is not a security certification or exhaustive line-by-line audit.

## Evidence and baseline

- HEAD: 085af22 (versioned Terms acceptance); preceding commits include signup errors, admin-console design and admin recovery.
- Existing modified/untracked application, E2E, migrations, configuration and documentation files were preserved.
- The owner supplied a local Chromium result showing three KYC journeys passing. That validates the described fake-storage/scan scenarios only. The separate real PostgreSQL regression outcome remains unconfirmed in this phase.
- Production environment values and external dashboards were not inspected. Integration configuration cannot be classified as working or missing merely from source defaults.

## Inventory

| Capability | Classification | Source evidence and gap |
|---|---|---|
| Signup/login/refresh/logout | Implemented code; broader runtime unverified | backend/app/api/auth.py has public role allowlist, hashing, rotating sessions and current-user checks; src/lib/api.ts handles rotation. Local KYC login passed in supplied output. |
| Role navigation | Confirmed incomplete | src/main.tsx stores only full_name, always opens dashboard after login/avatar, and startup restores name without role routing. LiveDashboard labels privileged-only accounts as Customer dashboard. Driver destination is also not role-aware. |
| Admin overview | Partial implementation | LiveAdmin.tsx uses real marketplace-health/funnel APIs and links to review screens. App renders admin only if view is admin, with no normal role-aware entry. |
| Full admin operations console | Designed, not implemented | Approved admin-console spec defines users/search/status/roles/bookings/tabs. API modules have no corresponding general /admin/users or /admin/bookings list/mutation routes; LiveAdmin lacks these sections. Existing focused operations endpoints should be reused. |
| Provider KYC | Implemented; local simulated journey passed | api/kyc.py, LiveKYC.tsx and storage.py implement application, private uploads, exact clean-scan gating, protected download, manual review/history. Owner/driver/fleet rules differ. Actual AWS and admin UI journey are unverified. |
| Vehicle metadata/manual review | Implemented code; runtime unverified | api/vehicles.py supports vehicle metadata, expiry-based eligibility and administrative review; LiveFleet/LiveVehicleReview exist. |
| Vehicle-specific document files | Confirmed absent | LiveFleet explicitly says uploads remain deferred. Models have application-linked KYCDocument but no vehicle-file model found; vehicles API has no file upload/register/download endpoints. Provider KYC RC is not a per-vehicle file workflow. |
| Public password recovery | Confirmed absent | Auth route inventory contains no public forgot/reset-password endpoints; AuthModal only login/signup. Temporary-token admin recovery exists and is not a customer recovery substitute. |
| Email verification | Partial | Signup stores hashed expiring code, verify-email endpoint exists. Signup does not call email delivery; no resend route or verification form in AuthModal. SMTP notification adapter exists separately. |
| SMS/WhatsApp/email notifications | Adapter code exists; integration unverified | services/communications.py contains MSG91, WATI and SMTP providers; configured runtime delivery not verified. WhatsApp optional. |
| Quotes/bookings/trips/capacity | API-backed screens and routes exist; end-to-end unverified here | requests, quotes, bookings, capacity and trip workflows are present. Do not infer whole-website success from KYC tests. |
| Homepage loads | Confirmed misleading live presentation | Home in src/main.tsx renders constant loads under LIVE MARKETPLACE. API-backed Loads screen exists separately. Replace with real data/empty/error states or label as demo without implying availability. Other old demo components remain in main.tsx; distinguish unreachable legacy code from rendered behavior before removal. |
| Maps/advisory charges | Implemented code; configuration/runtime unverified | api/pricing.py uses Google Routes and controlled missing-config error; domain.py calculates explicit assistance/stop/night/waiting charges with Decimal. Final provider quote model preserved. |
| Payments | Integrity implementation exists; sandbox journey unverified | payments.py and service adapter contain server amount calculation, idempotency, signatures and captured-evidence validation. Full checkout/webhook/refund/reconciliation verification remains deferred. |
| Terms acceptance | Implemented for booking creation; legal content draft | terms.py records version/hash/acceptance and audit; bookings.py invokes require_terms; quote screen uses TermsConsent. One-time per current version, not permanent acceptance for all future versions. Capacity/payment boundary consent needs trace-through before claiming all paths covered. |
| Privacy/refund/KYC consent/retention | Finalization/design needed | Draft Terms explicitly await entity/contact/jurisdiction confirmation. Dedicated published policy files were not found in inspected repository; embedded text is not proof of complete standalone policies. Retention/deletion design and qualified review required. |
| Liveness/readiness/logging | Implemented baseline | main.py and core middleware provide health endpoints, DB/Redis readiness and request logging. No runtime checks performed. |
| Alerting/error reporting | Partial | SENTRY_DSN exists in config but no SDK initialization found in main/core. External uptime/alerts unknown. |
| Backup/recovery | Partial documentation/local script | backup-postgres.ps1 uses Docker compose local trucksetu DB, not managed Neon. No restore script found. Scheduled encrypted production backup/restore evidence is unverified. |
| CI/release | Partial, with confirmed static gaps | ci.yml has lint/test/build/migration stages, but dedicated serialization regression now needs E2E_DATABASE_URL/allowlist/local flags absent from that workflow. New playwright.yml has visibly misindented E2E_PROVIDER_EMAIL/E2E_ADMIN_EMAIL entries. No YAML parser or CI run performed during hold. |

## Prioritized engineering backlog

1. **Phase B:** Fix role-aware login, startup and avatar routing using complete API-returned CurrentUser; preserve permissions. Then explicitly scope full admin-console implementation as a separate deliverable rather than presenting navigation as completion of the console.
2. **Release-critical adjacent task:** Replace the rendered homepage sample loads labelled live. Keep unrelated unreachable demo cleanup separate.
3. **Phase C:** Design per-vehicle document persistence/API/UI with private direct uploads, clean-scan enforcement, ownership, review decisions, expiry/replacement history and audit. Required types and operational expiry rules need confirmation where not established.
4. **Phase D:** Add secure public recovery and complete email delivery/resend/verification UI. Design token single-use/expiry, rate limits, generic responses, session revocation and retry behavior before implementation.
5. **Phase E:** Repair CI configuration/isolation without weakening safeguards; wire optional monitoring behind configuration; prepare Neon-specific backup/restore runbook and document external alert/retention requirements.
6. **Phase F:** Trace every booking path through versioned consent, review actual pricing/financial snapshots against approved rules, and prepare policy content only from owner-supplied details. Do not invent tax/refund obligations.
7. **Phase G:** Review all uncommitted changes (including packaging artifacts), write environment/migration handoff, and resume verification only with owner approval. Source-control/deployment actions require separate authorization.

## Owner dependencies

- Legal entity/address, support/grievance contact, applicable tax identity and qualified legal/privacy/tax review.
- Commission payer/rate, waiting allowance/rate, cancellation/refund policy, extra-stop interpretation and per-vehicle document requirements where ambiguous.
- Email provider and verified sender/domain; private environment configuration for AWS/scanner, Maps, Razorpay test webhooks and eventual MSG91.
- Monitoring/alert destination, production backup/retention choices, final frontend/API domains and staging/live authorization.
- Do not provide secret values in chat. No infrastructure was changed or connectivity inferred in this inventory.

## Verification debt and completion gate

Testing remains on hold. All listed code implementations remain subject to the relevant security/transaction/UI and integration checks. Phase A is complete as a bounded static inventory, not proof of production readiness. First next task is Phase B, with a small approved routing design; agree when focused test-first checks may resume before claiming its behavior verified.
