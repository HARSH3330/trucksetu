# Playwright KYC End-to-End Test Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic, guarded local Playwright suite that exercises the real TransivoX provider KYC flow and separately supports opt-in real AWS verification.

**Architecture:** Use a strict TypeScript preflight utility for database/mode safety, inject the private-storage adapter through FastAPI dependencies, and run a test-only FastAPI entrypoint with local upload/scan controls. Playwright drives the production React UI with separate provider/admin contexts and generated fictional PDFs; PostgreSQL remains real and is migrated before the run.

**Tech Stack:** Playwright Test, TypeScript, React/Vite, FastAPI, SQLAlchemy/Alembic, PostgreSQL, pytest.

**Spec:** `docs/superpowers/specs/2026-10-07-playwright-kyc-e2e-design.md`

## Global Constraints

- Require `E2E_DATABASE_URL`; never fall back to application database variables.
- Permit reset only when the parsed database name is exactly `transivox_e2e` and the parsed host exactly matches `E2E_ALLOWED_DATABASE_HOSTS`.
- Never reset in staging/AWS mode.
- Apply the real Alembic migrations before local tests.
- Keep fake uploads and scan controls out of the production FastAPI entrypoint.
- Generate only fictional PDFs prominently marked `NOT A REAL IDENTITY DOCUMENT`.
- Use distinct provider and administrator sessions and accounts.
- Do not contact real AWS unless `E2E_REAL_AWS=true` and staging variables are explicitly supplied.
- Do not commit or push this implementation.

## Review Focus

- Encoded or malformed PostgreSQL paths must not bypass the exact `transivox_e2e` database-name check.
- Hostname matching must be exact after URL parsing; suffix or substring matches must fail.
- Any real-AWS/staging flag must disable all reset behavior before a database command runs.
- A forged local clean-scan request without the test control token must fail.
- Browser artifacts and logs must not disclose passwords, bearer tokens, or signed query strings.

---

### Task 1: Database and execution safety preflight

**Files:**
- Create: `e2e/safety.ts`
- Create: `e2e/safety.spec.ts`
- Create: `e2e/global-setup.ts`
- Modify: `package.json`

**Interfaces:**
- Produces: `validateE2EEnvironment(env: NodeJS.ProcessEnv): E2EEnvironment` and a global setup entrypoint that runs reset/migration commands only after validation.
- Consumes: environment variables defined in the specification.

- [ ] Write failing unit tests for a missing `E2E_DATABASE_URL`, fallback attempts, wrong/encoded database names, non-PostgreSQL schemes, exact allowed/disallowed hosts, and reset rejection under `E2E_REAL_AWS=true`.
- [ ] Run the safety test and confirm it fails because the module/API is absent.
- [ ] Implement URL parsing and a typed validated environment without reading `DATABASE_URL` or `MIGRATION_DATABASE_URL`.
- [ ] Run the safety tests and confirm they pass.
- [ ] Add guarded reset/migration setup that invokes the existing real Alembic configuration only in local mode and seeds dedicated test accounts through a test support command.
- [ ] Verify the unit tests again; do not execute a reset without an approved matching local URL.

### Task 2: Injectable private storage and isolated E2E support API

**Files:**
- Modify: `backend/app/api/kyc.py`
- Create: `backend/app/services/dependencies.py`
- Create: `backend/e2e_support.py`
- Create: `backend/tests/test_e2e_storage_support.py`

**Interfaces:**
- Produces: `get_private_document_storage() -> PrivateDocumentStorage`, an API dependency override, and local-only fake upload/scan control routes.
- Consumes: production KYC storage contract (`upload_url`, upload validation, `require_clean_scan`, download URL as needed).

- [ ] Write backend tests proving KYC routes resolve storage through a dependency and the production app exposes no E2E control routes.
- [ ] Run the focused pytest file and confirm the expected failures.
- [ ] Add the storage dependency and replace direct route construction without changing production behavior.
- [ ] Run the focused tests and existing KYC security tests.
- [ ] Write failing tests for support-app startup restrictions, upload acceptance, default pending scans, exact clean transition, invalid/missing control tokens, and production-mode refusal.
- [ ] Implement a temporary-directory fake storage adapter and test-only FastAPI support routes that are registered only by `backend/e2e_support.py`.
- [ ] Run the focused support tests and KYC security tests until green.

### Task 3: Fixtures, sessions, and the KYC browser journey

**Files:**
- Modify: `playwright.config.ts`
- Delete: `tests/example.spec.ts`
- Create: `e2e/fixtures/pdf.ts`
- Create: `e2e/fixtures/accounts.ts`
- Create: `e2e/fixtures/api.ts`
- Create: `e2e/kyc.spec.ts`
- Modify: `.gitignore`

**Interfaces:**
- Produces: runtime-generated valid PDFs, provider/admin context helpers, and the deterministic KYC E2E scenario.
- Consumes: validated URLs/config from Task 1 and local scan controls/storage boundary from Task 2.

- [ ] Write a failing fixture test proving generated bytes are a valid PDF signature and include the required fictional-document warning.
- [ ] Generate minimal valid PDFs in Playwright output storage and make the fixture test pass.
- [ ] Configure Chromium default execution, optional cross-browser projects, base URL, screenshots, traces, failure video, HTML reporting, serial KYC execution, and sanitized output paths.
- [ ] Implement provider UI login, owner application creation, pending-scan rejection, explicit clean transition, missing-required-document validation, remaining uploads, and submission to `under_review` using actual accessible labels.
- [ ] Implement a separate administrator context that authenticates independently and verifies the protected administrative review queue.
- [ ] Run Playwright list/config validation, then run the journey only when the guarded local PostgreSQL prerequisite is available.

### Task 4: Commands, CI, and operator documentation

**Files:**
- Modify: `package.json`
- Modify: `.github/workflows/playwright.yml`
- Modify: `.env.example`
- Create: `docs/testing/PLAYWRIGHT_KYC.md`

**Interfaces:**
- Produces: `e2e:kyc`, `e2e:kyc:cross-browser`, `e2e:kyc:report`, and explicitly gated `e2e:kyc:aws` commands plus Windows setup instructions.
- Consumes: all earlier task entrypoints and environment contracts.

- [ ] Add scripts without removing existing frontend scripts or Playwright dependencies.
- [ ] Expand the scaffold workflow with Python 3.12, an isolated PostgreSQL service/database, backend dependency installation, deterministic Chromium execution, and artifact upload; omit production/AWS secrets.
- [ ] Document exact Windows PowerShell PostgreSQL/database/user creation, environment variables, installation, browser setup, run, report, and cleanup commands.
- [ ] Document real-AWS mode as opt-in, non-resetting, and incapable of being inferred from local success.
- [ ] Run TypeScript checks, frontend unit tests/build, backend focused/full available tests, Playwright test discovery, and `git diff --check`; record every unavailable infrastructure check explicitly.
