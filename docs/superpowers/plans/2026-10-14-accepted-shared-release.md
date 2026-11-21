# Accepted Shared Quotes and Persistent Sessions Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans inline; preserve existing work, no commits/push/deployment or production data changes. Track RED/GREEN evidence in the existing release checklist.

**Goal:** Deliver approved shared quote acceptance and finite secure persistent login, then execute safe local verification.

**Architecture:** Extend existing request/Quote/QuoteVersion/reservation/Booking records. Acceptance names the revision; one transaction validates ownership, eligibility and capacity and snapshots the provider total. Sessions reuse RefreshSession/JWT rotation with HttpOnly cookie transport and origin/CSRF enforcement.

**Tech Stack:** React/TypeScript, FastAPI, SQLAlchemy/PostgreSQL, Playwright/Pytest.

**Spec:** Owner's 14 October execution brief and explicit provider-quote acceptance rules; existing release checklist and financial/domain invariants. Owner explicitly requests execution without another approval gate.

## Global Constraints

- Requests/quotes do not guarantee capacity. INR and existing commission/tax/cancellation/refund/payment rules stay unchanged; no price formula invented.
- Finite rotating sessions; no persistent JS-readable refresh credentials or passwords.
- Real DB checks require explicit safe LOCAL `transivox_e2e`; no fallback or real messages/payments/storage calls.
- Preserve uncommitted S3 probe and egg-info; work on existing release branch.

## Review Focus

1. Revision/duplicate acceptance must not change snapshots or duplicate bookings.
2. Hold expiry/cancellation must serialize and restore capacity once.
3. Preserve matching and private document gates, including legacy endpoints.
4. Multi-tab rotation/logout must not resurrect old account credentials.
5. Cross-site Vercel cookies may be browser-blocked; support explicit same-site topology honestly.

## Tasks

- [x] **1. Contracts.** Models/schemas/requests/quotes, additive migration 24. Test route-bound request, expiry, breakdown, revision. Produce `SharedQuoteAcceptance` and `validate_shared_quote(quote,request,expected_version,now)`; preserve full-vehicle contracts. Local contracts/offline compilation verified; actual migration not executed.
- [ ] **2. Acceptance.** `/quotes/{id}/accept-shared`; lock request→quote→provider→hold→route→vehicle/files. Reuse match evidence/holds. One unpaid booking with immutable snapshots. Test ownership, expiry/revision, replay, insufficient capacity and holds; author guarded PostgreSQL races.
- [ ] **3. UI.** Route-selected request, provider total/charges/validity, customer review/explicit acceptance/Terms. Playwright first, frontend tests/build; honest expiry/capacity/payment states.
- [ ] **4. Sessions.** Cookie endpoints using current auth, origin/CSRF checks, finite rotation; migrate JS sessions. Startup gate, role/destination restoration, logout/account separation. Test attributes, origins, rotation/expiry/revocation and browser reopening.
- [ ] **5. Release verification.** Diagnose actual load blocker without larger timeouts. Run suites/offline migrations; inspect unresolved auth/recurrence/admin scope, review diff, update existing checklist with exact rerun commands.

Pre-flight: 1→2→3 share request/quote fields; 4 changes auth transport consumed by 3; 5 verifies all. Legacy bearer endpoints stay compatible but unsafe legacy shared acceptance is prohibited.

Ruling: no-commit/no-production request overrides workflow commit/cleanup steps. Preserve current release branch and independent S3 work; record evidence uncommitted.

## Resume point — 15 October

Tasks 2–4 implemented in part and locally boundary-tested, not completed: real PostgreSQL acceptance/concurrency/expiry/revocation and deployed cookie checks remain blocked by missing E2E_DATABASE_URL. Required remaining engineering: shared operator matching controls, provider revision UI and the new acceptance transaction's isolated race regressions. Task 5: 300 backend nonintegration,46 frontend,35 synthetic browser checks passed; lint/domain typing/offline migration24 passed. Read-only security review completed, its two significant findings fixed RED→GREEN. Exact evidence, unresolved scope and user commands live in the existing release-candidate checklist. Do not repeat the audit or claim fully verified launch readiness.

Latest closure pass supersedes that resume point: operator matching/expiry controls
and provider revision UI implemented and browser-checked; nine guarded real HTTP
capacity-race scenarios plus actual migration23/24 preservation regression authored
and collected. 324 backend nonintegration,46 frontend,37 built-preview browser
checks passed. Fake app direct imports now require exact isolated database binding.
Real DB execution remains blocked; independent final review failed on usage limit,
so only self-review completed. No production operations or commits.
