# Production UI cleanup — local implementation

### Subsequent public UX and auth fix update — 2026-10-14

Follow-up work adds allowlisted hash deep links/refresh/Back behavior, signed-out Ship goods/Find loads navigation, a public safety page and FAQ, an explicit nontracking SVG illustration, filter apply/reset/count, selected-load search URLs, and a footer with the owner-provided support email and Monday–Friday 10:00–18:00 IST hours. Separate privacy/refund policies remain honestly unpublished. API-returned user identity now reloads protected screens after sign-in, and consumed homepage seeds no longer overwrite edited drafts. Fresh final browser suite: **25 passed**; frontend **38 passed** and build passed. See the post-audit status in `2026-10-14-functionality-audit.md`. The earlier source-control and check-count sections below are historical, preceding the user-authorized main push.

## Source-control boundary

`origin/main` was checked directly and already contains `085af222881fb57e60191e8bbb4f1dc55a892bcc` (Require versioned Terms acceptance before booking). The requested `git push origin main` returned **Everything up-to-date**. No new commit, unrelated release files, UI changes, deployment or production operation was pushed. The remaining local Terms router change depends on the broader uncommitted authentication-first work and was not shipped independently.

## Implemented

- `src/production-ui.css`: shared existing-brand typography, spacing, flatter surfaces, restrained headings/corners, visible focus, touch targets and reduced motion. Keeps mobile operational buttons, action labels, document expiry/status and all load records visible. Wide direct-child panel tables scroll locally.
- `src/main.tsx`: labelled homepage route fields now populate the requirement form; explicit blank values replace unrelated draft locations. Removed fabricated shipment defaults and sample extraction, fake notification dot, unsupported trust promises and unused filter/vehicle-preference controls. Clear-search acts on the actual list query. Shared API client handles sign-in timeouts/errors; recoverable errors retain email and clear password. Publication is locked during submission and displays the returned reference, not a fabricated ID or promised notifications.
- `src/lib/useDialog.ts`: sign-in and requirement dialogs have names, keyboard containment, Escape dismissal, scroll locking and opener focus restoration. Publishing retains a named dialog and moves focus to Done. Other modal flows are not claimed audited; external OTP widget lifecycle is deliberately unchanged.
- `LiveKYC.tsx`: locks create/submit/review during requests, preserves failed forms, exposes status feedback, labels review selectors/reason and confirms rejection/suspension. Filter failures produce a retryable error instead of an unhandled rejection. Storage/malware/required-document/role checks remain backend-owned and unchanged.
- `LiveAdmin.tsx`, `AccountSecurity.tsx`, `PhoneVerification.tsx`: simpler operational copy without database/configuration internals or unsupported verification claims. Phone proof acceptance semantics unchanged.
- `AGENTS.md`: concise production UI conventions added without replacing engineering/security instructions.

The real API-backed screens remain in the application. Shared capacity was not hidden or narrowed to full-vehicle-only. No new dependency or backend contract/business rule was added.

## Verification and evidence

Fresh frontend unit tests: **38 passed**. TypeScript/Vite production build: **passed**. Final local Chromium public/widget/UX suite: **17 passed (40.8s)**, including the uncaught-JavaScript-error diagnostic. Git diff whitespace check passed. Checked homepage/sign-in at 360px, 768px and 1280px, mobile admin-to-KYC navigation, provider form failure, route/draft behavior, real response-reference rendering, publication keyboard focus and the existing fake widget journey. No timeouts were increased and no assertions skipped.

Regressions were observed failing before fixes: unlabelled/ignored home route inputs, missing sign-in dialog semantics, fabricated draft defaults, hidden mobile admin queue buttons, enabled KYC create during submission, stale saved destination, and publication success losing dialog semantics/focus. An ambiguous Sign in selector was corrected to target the real form submit; a introduced JSX delimiter error was fixed before the final successful build.

Screenshots (generated safe local data, not identities): `test-results/ui-before-home.png`, `ui-after-home-1280.png`, `ui-after-home-360.png`, and `ui-after-sign-in-{360,768,1280}.png`. Desktop before/after and mobile sign-in were visually inspected. HTML report: `playwright-public-report/index.html`; failing runs retain traces/screenshots. Console network failures are deliberately expected against the unreachable local API; that is not evidence of a deployed outage. UX tests assert no uncaught JavaScript exceptions, without logging input values.

## Boundaries / remaining work

- Browser role/API fixtures are synthetic. They verify frontend behavior only, not authentication/authorization, persisted KYC decisions, real uploads/scan results, payments or delivery. No real provider was contacted.
- `E2E_DATABASE_URL` is absent here. Full real multi-role PostgreSQL/KYC/booking/trip journeys remain blocked, with no database fallback. Existing guarded setup is in `2026-10-14-release-handoff.md`.
- Populated Fleet/driver trip/payment/review screens received shared styling but their complete mobile/keyboard task flows were not exercised this turn. Recovery/other dialogs still need their own keyboard lifecycle review; do not infer whole-site accessibility certification from these checks.
- Shared-capacity publication/reservation/consent UI, provider-KYC immutable storage references, external configuration/delivery, sandbox payment reconciliation, legal/business approvals and operational release gates remain as documented in the release handoff. Text-assisted requirement entry is honestly marked unavailable, not simulated. Existing unreachable demo components were left untouched to avoid unrelated refactoring; they are not production journeys.
- There is no frontend lint script/configuration in this repository. No lint success is claimed; TypeScript build and tests ran.

## Rerun (PowerShell, repository root)

```powershell
npm test
npm run build
npx playwright test --config playwright.public.config.ts
npx playwright show-report playwright-public-report
```

UI changes remain local for review. Public launch is not approved by this report.
