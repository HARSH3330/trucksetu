# AGENTS.md — TransivoX Engineering Guide

This file applies to the entire repository. Follow it for every task unless a more specific `AGENTS.md` exists deeper in the directory tree. Direct user instructions and system/developer instructions take precedence.

## Mission

Build TransivoX into a trustworthy, polished, production-grade marketplace for heavy-vehicle logistics in India. Optimize for safe real-world operations, not impressive demos. A feature is valuable only when its data is real, its permissions are enforced, failure states are clear, and it can be tested and operated safely.

“Make it crazy” means exceptionally useful, fast, clear, secure, accessible, and reliable. It does not mean adding animation, AI, dependencies, complexity, or scope without a user need.

## Product Model

TransivoX connects customers with independent transport providers, fleet owners, vehicle owners, and drivers. It is a marketplace and coordination layer; providers set the final transportation quotation. TransivoX may suggest a trip price and itemize charges, but it must not present that suggestion as a mandatory Ola/Uber-style fare.

Current commercial rules include:

- loading and unloading: each has a ₹100 base plus ₹7 per parcel;
- the first two intermediate stops are included;
- additional-stop charge after two stops: currently ₹500;
- night-service charge: currently ₹500;
- waiting charges are separate and must be shown explicitly;
- providers submit the final quotation;
- commissions, taxes, tolls, parking, refunds, and gateway fees must be itemized rather than hidden.

Never describe money as escrow unless a legally valid regulated escrow arrangement actually exists.

## Repository Map

- `src/` — React, TypeScript, Vite frontend.
- `src/components/` — live API-backed product screens.
- `src/lib/api.ts` — frontend API boundary, session rotation, and shared API types.
- `backend/app/api/` — FastAPI route modules.
- `backend/app/core/` — configuration, database, security, middleware, logging, and rate limits.
- `backend/app/models.py` — SQLAlchemy persistence models.
- `backend/app/schemas.py` — shared request/response validation.
- `backend/app/domain.py` — framework-independent business invariants.
- `backend/app/services/` — storage, payment, communications, and other external adapters.
- `backend/migrations/` — Alembic migrations.
- `backend/tests/` — backend unit, security, workflow, and integration tests.
- `scripts/` — operational scripts for migrations, smoke checks, backups, and one-time admin operations.
- `.github/workflows/` — CI and controlled production-migration workflows.
- `docs/superpowers/specs/` — approved architectural specifications.
- `SECURITY.md` and `DEPLOYMENT.md` — mandatory security and release guidance.

## Working Agreement

1. Inspect the relevant code, tests, current Git status, recent commits, and applicable documentation before changing anything.
2. Preserve user changes. Never discard, overwrite, reset, or “clean up” unrelated work.
3. Find the root cause of defects before proposing or implementing a fix.
4. For new behavior, establish intent and a small design before implementation. Do not silently choose business rules.
5. Write a failing test before production code for every bug fix or behavior change when the project has a viable test boundary.
6. Make the smallest coherent change that solves the approved problem. Avoid unrelated refactors.
7. Use real API-backed behavior. Never present hard-coded sample records as live production data.
8. Keep frontend types, API contracts, database models, migrations, tests, and documentation synchronized.
9. Verify with fresh command output before claiming anything works.
10. Report limitations and unrun checks explicitly. Never convert “not tested” into “working.”

## Git and External-Change Policy

- Do not commit or push unless the user explicitly says `commit`, `push`, or otherwise clearly authorizes it for the current work.
- Do not interpret approval to implement as approval to commit or push.
- Before an authorized commit, inspect the diff, run relevant verification, and ensure no secret or unrelated file is staged.
- Use focused commit messages describing the behavior delivered.
- Do not rewrite published history, force-push, reset hard, or discard work unless explicitly instructed and the exact risk is explained.
- Do not deploy, promote a deployment, run production migrations, rotate production secrets, modify cloud resources, send messages, charge money, issue refunds, or change third-party dashboards without explicit authorization.
- A push is not proof of deployment. Report source-control and deployment status separately.

## Skill and Workflow Selection

Use the most relevant available skill or structured workflow before acting. When these skills are available:

- use `superpowers:using-superpowers` to select applicable workflows;
- use `superpowers:brainstorming` before creating features, components, workflows, or changed behavior;
- use `superpowers:systematic-debugging` for defects, failing tests, production errors, and unexpected behavior;
- use `superpowers:test-driven-development` for implementation and bug fixes;
- use `superpowers:writing-plans` after an approved multi-step specification;
- use `superpowers:executing-plans` when implementing an approved plan directly;
- use `superpowers:verification-before-completion` before completion claims, commits, or push requests;
- use `superpowers:requesting-code-review` for large or security-sensitive implementations;
- use document, PDF, spreadsheet, presentation, image, or computer-control skills only when the requested artifact actually requires them.

Do not invoke every skill mechanically. Use the smallest set that covers the task, follow each selected skill completely, and tell the user when a skill introduces a design/review pause.

Do not delegate to subagents unless the user explicitly requests delegation or the active instructions permit it. When delegation is authorized, keep security-sensitive integration and final verification with the primary agent.

## Architecture Principles

- PostgreSQL is the source of truth for users, roles, requests, quotations, booking snapshots, allocations, trips, capacity, payments, refunds, invoices, commissions, KYC metadata, disputes, messages, and audit events.
- Redis supports rate limiting, caching, and coordination. It is not the durable source of truth.
- S3 objects containing KYC or evidence are private. Access occurs only through short-lived signed operations and server-side authorization.
- External services are behind adapters. Route business logic through service modules instead of scattering provider-specific HTTP calls across endpoints.
- Keep business invariants in testable domain functions where practical.
- Use database transactions, row locks, idempotency keys, and immutable snapshots for allocation, capacity, payment, cancellation, and state transitions.
- Never use floating point for money, weights requiring exact decimal behavior, commissions, or taxes. Use `Decimal`/`Numeric` and serialize deliberately.
- Store timestamps in UTC and convert only at display boundaries.
- Prefer focused modules and explicit interfaces. Split files when a unit takes on unrelated responsibilities.

## Identity, Roles, and Authorization

Supported public roles are `customer`, `provider`, `fleet_owner`, and `driver`. Privileged roles are `admin` and `superadmin`.

- Enforce authorization on the backend for every protected read and mutation. Hidden buttons are not security controls.
- Treat resource ownership and role permission as separate checks.
- An administrator may operate only within explicitly defined admin endpoints or documented exceptions.
- A superadmin is not exempt from audit logging, validation, or safety rules.
- Public signup must never assign `admin` or `superadmin`.
- Do not permit privileged users to remove their own final privileged role, suspend themselves, or create another superadmin through a general-purpose endpoint.
- Suspending an account must revoke active refresh sessions.
- Password hashes, refresh-token hashes, OTP hashes, recovery tokens, secrets, and authentication internals must never appear in API responses or logs.
- Maintain generic authentication errors where specificity would enable account enumeration.
- Use the current-user record returned by the API for role routing. Do not infer permissions from UI state or a decoded token alone.

Default authenticated destinations:

- `admin` or `superadmin` → Marketplace Control Centre;
- `provider` or `fleet_owner` → Provider dashboard;
- `driver` → Trip operations;
- `customer` → Customer dashboard.

## KYC, Aadhaar, and Sensitive Documents

KYC data is exceptionally sensitive.

- Never print, log, fixture, screenshot, or commit real Aadhaar, PAN, driving-licence, RC, insurance, permit, or bank data.
- Collect only information required for an approved verification purpose.
- Keep buckets private with public access blocked, encryption enabled, and least-privilege identities.
- Preserve the direct-to-storage upload pattern; do not proxy large private files through the API without a documented reason.
- Enforce file-size, declared MIME type, extension, and file-signature checks.
- A document must not be registered or viewable for approval until the configured malware scanner reports a clean result.
- Do not treat a submitted or scan-clean document as verified. Manual acceptance of every required, unexpired document is required while automated KYC is disabled.
- Use short-lived signed downloads and audit access to sensitive files.
- Mask identifiers in general lists. Full documents belong only in the explicit review workflow.
- Preserve resubmission, rejection, suspension, expiry, and reviewer-reason history.
- Never claim that TransivoX verification guarantees authenticity, vehicle condition, legal compliance, or future behavior.

Changes involving Aadhaar, retention, consent, automated KYC, biometrics, or identity-provider integrations require explicit legal/privacy review before production use.

## Payments and Financial Integrity

- The backend creates payment orders and calculates payable amounts. Never trust a browser-supplied total.
- A Razorpay order or `authorized` event is not successful payment. Mark funds paid only after cryptographically verified captured-payment evidence matching order, amount, and currency.
- Verify webhooks using `RAZORPAY_WEBHOOK_SECRET`, not the API key secret.
- Make webhook/event processing idempotent and retain the provider event reference.
- Do not store full card, CVV, UPI PIN, bank credential, or raw payment secret data.
- Offline payments remain `pending_confirmation` until an authorized administrator confirms them.
- Refunds, commissions, tax calculations, invoice issue, and settlement decisions require immutable records and audit events.
- Never silently recalculate historical booking, commission, cancellation, or tax snapshots after a configuration change.
- Automated payout remains disabled unless explicitly designed, legally reviewed, tested in a sandbox, reconciled, and approved.
- Any change to money movement requires focused tests for duplicate requests, retries, partial failure, mismatched amount/currency, replayed webhook, cancellation, and refund behavior.

## Marketplace and Trip Rules

- Customers publish transportation requirements; verified providers submit quotations.
- Preserve quote-version history and negotiation records.
- A booking must snapshot the accepted route, cargo, price, allocation, charge breakdown, and relevant policy values.
- Enforce allocation capacity and multi-provider totals transactionally.
- Only legal trip transitions defined by the domain workflow are allowed.
- Pickup and delivery OTPs are independently generated, hashed, attempt limited, expiring, and status gated.
- Never reveal OTPs in production responses or logs.
- Route pricing is advisory. Google Routes supplies distance/duration evidence when configured; missing Maps configuration must produce a controlled, honest error rather than fabricated distance.
- Shared-capacity matching must preserve ordered-route compatibility, cargo restrictions, timing constraints, and row-locked reservation capacity.
- Hazardous, temperature-controlled, animal, fuel, chemical, explosive, and other specialist cargo remains unavailable unless the applicable feature, legal, safety, insurance, and operational requirements are deliberately enabled.

## API Standards

- Keep versioned public routes under `/api/v1`.
- Use Pydantic models with explicit bounds for external inputs.
- Use `EmailStr`, enums/allowlists, decimal bounds, maximum string lengths, and pagination caps as appropriate.
- Return stable structured responses. Coordinate breaking changes with frontend types and tests.
- Use correct HTTP semantics: `201` creation, `202` accepted async work, `204` empty success, `400/422` invalid input, `401` unauthenticated, `403` unauthorized, `404` concealed/missing resource, `409` state conflict, `429` rate limit, and controlled `503` dependency unavailability.
- Avoid leaking resource existence across authorization boundaries.
- Apply rate limits to authentication, OTP, pricing, AI, uploads, payments, and privileged recovery operations.
- Mutations affecting money, capacity, allocation, verification, privileges, or irreversible workflow state must be transaction safe and audit logged.
- Do not put provider credentials, stack traces, SQL, or internal exception text in client responses.

## Database and Migrations

- Every persistent schema change requires a reviewed Alembic migration.
- Do not use `create_all` as a production migration strategy.
- Keep migration history to one head unless an intentional merge migration is part of the change.
- Prefer additive, backward-compatible migrations followed by application rollout and later cleanup.
- Avoid destructive column/table changes without a data migration, backup/restore plan, and explicit approval.
- Do not run production migrations automatically at application startup or from serverless instances.
- Use the pooled Neon URL for runtime and the direct migration URL for Alembic.
- Run `scripts/check-migrations.ps1` for migration changes.
- Never edit production data manually as a shortcut for missing product behavior unless explicitly authorized and accompanied by a verified recovery plan.

## Frontend Quality

- Use TypeScript and functional React components.
- Prefer the shared API client over ad hoc `fetch` calls so timeouts, token rotation, error parsing, and headers remain consistent.
- Keep complete authenticated user/role state where navigation or permissions depend on it.
- Every API screen needs loading, empty, retryable-error, forbidden/signed-out, and populated states.
- Do not mark fake records as live. Demo-only information must be unmistakably labeled and excluded from production workflows.
- Preserve the TransivoX visual language while improving hierarchy, spacing, responsiveness, and clarity.
- Design mobile first and verify desktop behavior. Avoid layouts that only work at one screenshot size.
- Use semantic HTML, keyboard-accessible controls, visible focus, meaningful labels, adequate contrast, and non-color-only status indicators.
- Buttons must perform their advertised action. Remove or disable unfinished actions with an honest explanation.
- High-risk actions require confirmation, clear consequences, and a reason when auditability matters.
- Avoid excessive animations. Respect reduced-motion preferences for nonessential motion.
- Keep bundle growth deliberate; do not add a dependency for behavior easily implemented with existing tools.

### Production UI conventions

- Keep the existing ink/teal/lime brand; use restrained shared surfaces, 8px corners, readable field labels, and visible 44px actions. Avoid decorative emoji, fabricated shipment defaults, notification dots without unread evidence, and unsupported trust claims.
- Use specific logistics copy and preserve explicit empty/error/unavailable states. Keep technical deployment/configuration details in operator documentation, not customer screens.
- Preserve mobile action labels and review controls; do not hide records or operational actions to fit the viewport. Keep tables locally scrollable and file expiry/status text readable.
- Existing modal flows need a named dialog, keyboard containment, Escape dismissal, focus restoration and scroll locking. External verification widgets own their separate dialog lifecycle; test compatibility before applying these helpers to that flow.

## Admin Console

Follow the approved design in `docs/superpowers/specs/2026-10-07-admin-operations-console-design.md`.

- Admin lists are server-side searched, filtered, sorted, and paginated.
- Return the minimum operational fields required.
- Do not add unrestricted database or CSV export without a separate privacy/security design.
- General admin lists must not return KYC file contents, message bodies, OTP data, authentication data, or payment secrets.
- Administrative mutations require server-side role checks and audit events.
- Ordinary admins cannot modify privileged accounts. Superadmins cannot assign another superadmin through general role management.
- Audit logs are append-only from the console.

## External Integrations and Configuration

- Configuration comes from environment variables described in `.env.example`; never hardcode credentials.
- Never commit `.env`, service-account keys, database URLs, webhook secrets, API keys, tokens, or copied production logs containing secrets.
- Do not print secret values during troubleshooting. Report only whether a value is set, validly shaped, and which environment/project receives it.
- Treat frontend `VITE_*` values as public. Never place server secrets in them.
- Restrict Google Maps keys by API and appropriate application/server boundary.
- Use TLS endpoints for Neon, Redis, and external providers.
- Handle optional integrations honestly: MSG91, WATI, SMTP, Gemini, Maps, S3, malware scanning, and Razorpay must fail closed or degrade through an explicitly designed fallback.
- Do not claim an integration is connected because a build succeeded. Verify the relevant runtime operation.

## Legal, Privacy, and Content

- Do not invent legal entity names, addresses, GSTINs, grievance contacts, licence numbers, tax treatment, policy dates, or regulatory claims.
- Treat legal, tax, transport, Aadhaar, privacy, employment, insurance, payment, and consumer-protection conclusions as requiring qualified Indian professional review.
- Keep Terms, Privacy Policy, Cancellation/Refund Policy, KYC Consent, pricing disclosures, and the actual product behavior consistent.
- Record policy version and acceptance evidence when users agree to material terms.
- Preserve mandatory consumer and statutory rights; do not rely on broad disclaimers to remove non-excludable obligations.
- Avoid claiming “guaranteed,” “certified,” “escrow,” “fully secure,” or “legally compliant” without verified grounds.

## Testing Requirements

Use risk-proportionate tests, with stronger coverage for authentication, authorization, money, capacity, KYC, and trip transitions.

Frontend commands from the repository root:

```powershell
npm test
npm run build
```

Backend commands from `backend/` in Python 3.12 with development dependencies installed:

```powershell
ruff check app tests migrations
mypy app/domain.py
pytest --cov=app --cov-report=term-missing
pytest tests/integration -q
```

Migration check from the repository root:

```powershell
.\scripts\check-migrations.ps1
```

Operational API smoke check, only against an explicitly approved environment:

```powershell
.\scripts\smoke-api.ps1 -BaseUrl "https://approved-api.example.com"
```

Testing rules:

- First run the smallest test proving the changed behavior.
- For a bug, observe the regression test fail for the expected reason before implementing the fix.
- After the focused check passes, run the complete relevant suite.
- A frontend build does not replace frontend tests.
- Python compilation does not replace backend tests.
- Mock external services at unit boundaries, but keep integration tests for database transactions and critical adapters.
- Never call live payment, SMS, WhatsApp, email, or production storage services from ordinary automated tests.
- If dependencies or infrastructure prevent a test, state the exact missing prerequisite and do not claim the suite passed.

## Security Review Checklist

For any feature touching identity, permissions, private files, money, messaging, or admin operations, explicitly verify:

- authentication requirement;
- role and ownership authorization;
- input bounds and file validation;
- account/resource enumeration risk;
- rate limiting and replay/idempotency behavior;
- transaction and concurrency behavior;
- secret and personal-data exposure in responses/logs;
- audit event coverage;
- session revocation effects;
- failure and retry behavior;
- retention/deletion implications;
- frontend states do not overpromise backend results.

## Production and Deployment

- Read `DEPLOYMENT.md` before deployment-related changes.
- Production uses `APP_ENV=production`, `DEBUG=false`, an unpredictable secret of the required length, explicit CORS origins, and trusted hosts.
- Keep frontend and API deployments distinct unless an approved architecture changes that boundary.
- Liveness proves the process responds; readiness proves required dependencies are available. Do not confuse them.
- A successful Vercel build does not prove database, Redis, S3, Maps, Razorpay, email, SMS, or webhook operation.
- Run migrations once as a release step before routing traffic to incompatible code.
- Create and test backups. A backup that has never been restored is unverified.
- Preserve feature flags for incomplete or high-risk capabilities. Do not enable automated payouts, automated KYC, interstate operations, hazardous cargo, or live GPS merely because code exists.
- Require sandbox end-to-end checks before switching any provider from test to live mode.
- Public launch requires independent penetration testing and qualified Indian legal/privacy/tax review.

## Definition of Done

A change is done only when all applicable statements are true:

- approved intent and acceptance criteria are satisfied;
- authorization and ownership checks exist on the server;
- business invariants and failure states are handled;
- database changes include safe migrations;
- focused regression/feature tests were written and observed failing before implementation;
- relevant full test suites and builds pass with fresh output;
- no secrets, personal data, demo claims, or unrelated changes are included;
- accessibility and responsive behavior were checked for UI changes;
- external integrations were verified at the correct boundary or clearly reported as unverified;
- documentation and environment templates reflect the behavior;
- security-sensitive actions are audit logged;
- `git diff --check` is clean and the final diff was reviewed;
- remaining risks and manual steps are clearly reported;
- code remains uncommitted and unpushed until the user explicitly authorizes commit/push.

## Communication Style

- Lead with the outcome or current blocker.
- Explain decisions in plain language and include technical detail only where it helps verification.
- Separate implemented code, configured infrastructure, tested behavior, and assumptions.
- Never tell the user “everything works” when only a subset was tested.
- Give exact next steps for user-owned credentials or external dashboards without asking them to share secrets.
- When a choice changes product behavior, cost, risk, or legal posture, stop and request that choice rather than silently deciding.
