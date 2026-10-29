# Launch preparation ledger

Spec: owner attachment `6dd9921f-686e-4e9b-a5ef-3face8033ce9/Pasted text.txt`.
Base: `66c63d17897837afc88f457dab0c0e7b8942ac2a` (clean working tree).
Local branch: `codex/launch-preparation-no-otp-maps`. No commit/push/deploy authorized.

## Tasks and shared interfaces

1. Establish exact project/release/database identities and connector capability.
2. Reuse 19/20 October evidence; restore isolated DB availability if safe; extend
   missing real UI prerequisite coverage without weakening auth/scan controls.
3. Reproduce/fix payment, recovery or sensitive-logging defects; focused regressions.
4. Prepare private scanner/storage, payment/email test plans and operator templates.
5. Local restoration evidence if DB available; alerts, security/legal handoff.
6. Run affected checks; reviewed diff, PR proposal and consolidated owner actions.

Interfaces: schema 23/24 must precede candidate API; matching frontend requires
cookie/shared routes; scanner clean-tag evidence must name the immutable version;
payment callbacks must preserve terminal booking state and immutable totals.

Ruling: remain in an authorized local development branch in the existing checkout
to preserve the working local virtualenv/DPAPI credential helper; no main changes.
Ruling: use current named plan/ledger rather than automated plan scripts that
assume per-task commits; user explicitly prohibits commits for this work package.

## Current evidence

- GitHub authenticated repository read PASS; default branch main.
- Candidate 66c63d1; deployed API/frontend both ccd594d, verified with production
  aliases through Vercel. API dpl_BycVRnLKUmjYfcKXMbkwrVesGYqj; frontend
  dpl_FExE8Kd4d9uFR29nAgsLHmUUpoB8. Deployment READY is not integration proof.
- Neon project/production branch/endpoint mapping checked before read-only SQL:
  neondb revision 20261014_22, users.auth_version present. No writes.
- Recovery pre-migration/pre-repair and migration rehearsal branches still listed.
- Razorpay filtered read FAIL: Authentication failed / INVALID_ARGUMENT. This is
  connector failure, not evidence that website credentials are invalid.
- No AWS Core tool exposed; plugin search returned unrelated AWS Data Analytics.
  Current process has no API AWS keys or configured expected bucket; historical
  real S3 probe remains separate evidence, not a new deployed KYC result.
- Docker Desktop is already running, engine /version returns HTTP500. No restart,
  data deletion, replacement database or production fallback attempted.
- Local PostgreSQL safety helper exists; subsequent DB work must pass explicit
  exact-name/allowed-host checks before any connection or reset.

## Findings under investigation

- Payment webhook unconditionally promotes any advance-paid booking to confirmed,
  including cancelled or progressed states. Reproduce before modifying.
- OperationsMiddleware logger.exception can include exception messages/tracebacks
  containing sensitive provider/database details. Reproduce before modifying.

## Continuation — 21 October 2026

Owner repeated the same work package in attachment
`28327c7a-63ce-4f6c-94e6-73f5f2dfce46/Pasted text.txt`; resume this ledger,
not another audit. No commits, pushes, deployments or production migrations.

- Confirmed local payment fix preserves cancelled/completed/disputed/in-transit
  booking state on late captured/offline funds, records operator audit evidence,
  locks booking before payment and serializes identical webhook events. Raw-body
  HMAC, captured amount/currency and permissions remain intact. Fake DB/gateway
  regression evidence only; real locking and sandbox reconciliation are blocked.
- Confirmed local logging fix reports correlation/type without exception text or
  traceback; controlled 500 retains secure response headers and request ID.
- Extended local recovery/SMTP/vehicle negative-scan tests; expanded real-browser
  scenarios for UI-created shared route/request and mobile vehicle uploads/review.
- Full non-integration run initially 352 passed / 1 failed: global in-memory
  rate-limit state leaked between TestClient scenarios. Isolated only the vehicle
  test's limiter dictionary; real limits remain unchanged. Final 353 passed.
- npm audit reproduced one high-severity Vite finding (three launch-editor
  advisories). Pinned the patched same-minor Vite 8.2.4; retained targeted
  source-map-js 1.2.2 lock update. Fresh audit: zero known vulnerabilities.
- Frontend 46 passed; public browser suite 37 passed against patched lockfile.
  Responsive design suite tracked in the consolidated handoff. Backend Ruff,
  domain mypy and offline linear migrations through 24 passed.
- Eight real-DB browser tests collected; expanded shared/vehicle specs passed
  explicit TypeScript check. Initial ad-hoc commands lacked --ignoreConfig and
  --types node; corrected command passed without installing dependencies.
- Guarded local DB validation passed; connection timed out. Docker engine check
  returned HTTP500. No resets/restarts/fallbacks. Fresh PostgreSQL, full real-DB
  browser journeys and backup/restore remain BLOCKED, not passed.
- Fresh authenticated GitHub/Vercel/Neon reads confirm main production deploys
  ccd594d, production revision 22 and auth_version present. Read-only aggregate
  production counts: zero bookings, nonterminal trips, verified providers/KYC,
  non-rejected legacy KYC documents and approved vehicles at query time. Recheck
  before any approved migration; this is not continuing permission to write.
- Public production /health/live and /ready returned 200; DB/Redis available.
  /version still reports malformed ca on old deployed source. Candidate's fix
  remains undeployed. Generic readiness is not S3/scanner/payment proof.
- Razorpay filtered connector read still fails authentication; no further retries.
  AWS management connector/local credential chain unavailable. No real provider
  sends, payments, refunds, uploads or scanner activation.
- Source secret pattern scan returned two existing fictional Neon test fixtures;
  reviewed as examples, not new secrets. Not an independent security assessment.

Ruling: do not broaden this package into a new ClamAV subsystem without the
written-design approval required by brainstorming. Proposed architecture is in
`docs/superpowers/specs/2026-10-21-private-malware-scanner-design.md`; no scanner
result was fabricated and production remains GuardDuty-tag gated.
Ruling: do not auto-restart/reset Docker or create replacement storage when the
engine returns HTTP500; unrelated applications/data must remain undisturbed.
Ruling: fix the evidenced dependency issue on its current minor line, not via
`npm audit fix --force` or a broad dependency update.

Deferred minors: existing >500 kB frontend chunk warning and dependency
deprecations; no speculative bundle refactor in this security/release package.
Final review is a primary-agent source/diff review, not independent penetration
testing. Full blocker, owner-action and release sequence: consolidated handoff.

Fresh-context read-only review was dispatched as required by the review skill,
but the reviewer stopped immediately with an account usage-limit error and
returned no findings. No independent review pass is claimed; no retry loop.
Primary-agent diff review remains the available review evidence. This is an
additional pre-merge review gate, not a reason to change production or skip tests.
