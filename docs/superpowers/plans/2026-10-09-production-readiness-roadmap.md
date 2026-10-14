# TransivoX Production Readiness Roadmap

**Goal:** Finish independently actionable engineering work while the owner configures providers and resolves commercial/legal decisions.

**Scope:** This is a delivery roadmap, not an approved detailed implementation design. Phase A establishes actual gaps before subsystem-specific implementation plans are written. No completion percentage or timeline is assigned before inventory.

## Global constraints

- Preserve all existing uncommitted changes.
- No commit, push, deployment, production data changes or live provider operations without explicit authorization.
- Testing is on hold at the owner's request. Implementation is not verified completion until deferred checks resume. Agree on resuming focused regression tests before bugfix implementation requiring a test-first gate.
- Keep real roles/ownership enforcement, private documents, clean-scan enforcement and transaction integrity intact.
- Do not invent business rules, legal details, credentials or integration success.
- Local KYC success validates simulated storage/scanning, not AWS or deployed behavior.

## Phase A — Inventory and dependency map

- [ ] Inspect repository status, relevant routes/models/UI, environment templates, deployment/security documentation and existing tests.
- [ ] Classify every scoped capability as implemented, partial, absent, configured-but-unverified, or blocked by owner decision.
- [ ] Record evidence and blockers separately; a variable's presence does not prove runtime connectivity.
- [ ] Produce a prioritized implementation backlog and separate subsystem plans for confirmed gaps.

**Gate:** Evidence-backed inventory and approved scope; no speculative implementations.

## Phase B — Role navigation and admin access

- [ ] Inspect session restoration and current-user routing in src/main.tsx, src/lib/api.ts and admin screens.
- [ ] Route admin/superadmin to the Control Centre, provider/fleet_owner to Provider dashboard, driver to Trip operations and customer to Customer dashboard using API-returned roles.
- [ ] Preserve backend permissions and controlled signed-out/error states; navigation is not authorization.
- [ ] Document any admin functionality gaps separately from navigation.

**Deferred acceptance:** Login/reload destinations, expired sessions, denied customer access and ordinary-admin privilege boundaries.

## Phase C — Vehicle-document uploads

- [ ] Inspect Fleet, vehicle review, KYC, storage and document persistence before designing additions.
- [ ] Identify missing RC/insurance/permit upload and review support; approve required types and expiry rules rather than silently choosing them.
- [ ] Reuse direct private uploads, bounds/signature validation, clean malware-scan registration, protected downloads and audited manual review.
- [ ] Include schema migration only if the existing persistence contract cannot safely support vehicle-linked records.
- [ ] Provide pending/error/retry/rejected states and preserve decision history on replacement.

**Owner dependency:** Required vehicle-document policy if current rules do not establish it; AWS configuration for later staging validation.
**Deferred acceptance:** Ownership denial, pending/threat scan blocking, valid registration, expiry, replacement and protected admin review.

## Phase D — Recovery and email

- [ ] Inventory verification/reset endpoints, tokens, rate limits, sessions and frontend screens.
- [ ] Implement only confirmed gaps with generic anti-enumeration responses, expiring single-use tokens and appropriate session revocation.
- [ ] Document sender/provider variables and delivery failure handling without exposing secrets.

**Owner dependency:** Email provider, verified sender/domain and private environment configuration.
**Deferred acceptance:** Invalid/expired/replayed tokens, delivery failure, abuse limits and actual staging delivery.

## Phase E — Operational readiness

- [ ] Review required configuration, optional-service failure behavior, liveness/readiness and redacted logs.
- [ ] Close confirmed configuration/error-handling gaps and prepare alert/runbook integration without modifying cloud dashboards.
- [ ] Document backup, restore, migration, rollback and incident procedures; distinguish documentation from a tested restore.
- [ ] List external provider operations still unverified, including Maps, OTP, payment webhooks and AWS.

**Owner dependency:** Monitoring destination, environment access/approvals and backup service choices.
**Deferred acceptance:** Dependency outages, alert delivery, restore drill and approved environment smoke checks.

## Phase F — Consent and financial consistency

- [ ] Inspect account/booking policy acceptance and recorded policy version/evidence.
- [ ] Compare displayed charges and persisted booking snapshots against approved marketplace rules.
- [ ] Correct confirmed implementation discrepancies; leave unresolved commission, waiting, cancellation/refund and tax decisions blocked.
- [ ] Preserve provider-set final quotation and explicit itemized charges; do not claim escrow.

**Owner dependency:** Entity/contact details, commercial decisions and qualified Indian legal/privacy/tax review.
**Deferred acceptance:** Consent gating/version changes, charge calculations, immutable historical snapshots and relevant payment invariants.

## Phase G — Release handoff (not deployment)

- [ ] Produce changed-file summary, environment-variable matrix, migration ordering, manual steps and remaining blockers.
- [ ] Resume verification only after the testing hold is lifted: focused regressions, relevant suites/builds, isolated local E2E and approved staging integration checks.
- [ ] Review diff and security-sensitive changes before asking for source-control authorization.
- [ ] Track commit/push, deployment and runtime verification as separate milestones.
- [ ] Keep public launch blocked on unresolved critical defects and independent security/legal review.

## Parallel owner track

1. Supply legal entity, address, support/grievance contacts and GSTIN if applicable.
2. Confirm commission/payer, waiting policy, cancellation/refund policy and whether extra-stop charge is per stop.
3. Configure email, Maps restrictions, private S3/scanner and Razorpay test webhooks; keep secrets in environment settings.
4. Complete MSG91 when ready; WhatsApp remains optional.
5. Confirm final frontend/API domains and obtain legal/privacy/tax review.
6. Authorize individual staging/live operations and release actions explicitly when ready.

## Recommended order and dependencies

A -> B -> C -> D -> E -> F -> G. D/E preparation may proceed while C awaits document-policy decisions. Owner configuration proceeds alongside A-F. G cannot certify production readiness while testing remains on hold.

## Review focus

- Session restoration must not route privileged accounts using stale UI/token-only roles.
- Scan-clean documents must not be described as manually verified.
- Replacement must not revive rejected document acceptance.
- Optional provider failure must not fabricate success or disclose internal secrets.
- Changed pricing/policies must not mutate historical financial snapshots.
