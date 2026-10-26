## STOP: recovery isolation incident corrected, release remains blocked — 26 October 2026

Read [incident and verified correction](operations/2026-10-26-recovery-isolation-incident.md) FIRST. This supersedes earlier claims that recovery restoration/migrations were isolated and production untouched. restore_snapshot without explicit finalize:false moved the ORIGINAL production endpoint/default to the restored copy;23–29were then applied while it was production-bound. Original branch22was preserved. At02:36:15UTC original endpoint restored to original22branch; original production name/default/primary restored. Endpoint-specific read verifies22/6users; API live/ready/version200. Possible writes during02:17–02:36UTC remain un-reconciled. Preserve all copies; no further endpoint move/write cleanup without reviewed approval. Auto-review rejected an extra-endpoint move as disruption risk; no workaround attempted. No new app deployment/live payment, but DO NOT claim no production configuration impact. Owner notified and follow-up approval requested.

Separate preview is synthetic/empty of users, migrated29, restricted runtime role/unique secret/isolated configuration; its endpoint is disabled. Current main CI1099527PASS:430unit/72PostgreSQL/54frontend, lint/types/build/containers. Browser job pending; collection interference fixed preserving8legacy checks and adding dedicated customer/Maps/email configurations; browser results not yet claimed. GitHub draftPR1 remains release-blocked. KYC/tax/Maps/AWS/protected-recovery decisions and owner99Testcheckout remain pending.

## Latest GitHub release preparation and CI repair — 26 October 2026

Reviewed source ed4d073 pushed on release/customer-first-20261026, draft PR https://github.com/HARSH3330/trucksetu/pull/1. NO deployment: both Vercel projects list zero release-branch deployments; production remains ccd594d/main. Preview runtime now least privilege, separate migration role, unique secret and production security validation; preview storage/scanner/Redis/host linkage remain unconfigured and deployment blocked. Updated [isolation/recovery record](operations/2026-10-26-release-isolation.md).

Initial GitHub CI: frontend tests/build PASS; backend units/lint/types/migrations PASS; PostgreSQL71PASS/1FAIL due test Redis lifecycle. Browser CI collection FAIL missing jwt from stale root package list. Reproduced parity failure, aligned root/backend dependencies and browser installer, scoped HTTP budget regression to ASGI boundary (production rate limits untouched). Three focused tests PASS/lintPASS; follow-up GitHub CI must be verified, do not reuse initial failures as success. Fresh99Test checkout page200/contains both fresh orders; owner interaction pending. Protected recovery remains plan-blocked; AWS has no credentials/profile; tax/KYC approvals absent. No live checkout/publication activation.

## Active release isolation — 26 October 2026

Owner now authorizes release branch/commit and push ONLY after deployment-trigger and preview-credential safety. No production deploy/migration/live payments. Read [actual isolation and recovery evidence](operations/2026-10-26-release-isolation.md) and [unapproved KYC notice draft](operations/2026-10-26-kyc-consent-draft.md). These supersede older shared-preview/missing-frontend-URL statements below. Both projects'27shared entries now production-only, preserving IDs/types; production frontend URL prepared, not deployed. Separate empty preview project created; checkout/storage/scanner/SMTP remain disabled/unconfigured. Fresh snapshot restored to separate recovery branch at22/50tables; protection blocked by plan limit. AWS credentials unavailable. Two fresh99Testorders await owner interaction; no capture/refund completion claimed. Intended99TOTAL production tax remains unconfirmed, live checkout gated. Exact release-branch Git deployment disabled in both roots. Full source manifest remains required before commit/push; do not infer push completion from this entry.

## Coordinated production release preparation — 26 October 2026 IST

Owner requested a concrete production release package, explicitly NO deployment/production migration yet. Read [exact release proposal](operations/2026-10-26-coordinated-production-release.md), [fresh verification](testing/2026-10-26-coordinated-release-verification.md) and [full source manifest](testing/2026-10-25-coordinated-release-manifest.json). Both actual serving Vercel frontend/API aliases reconfirmed ccd594df8a78f56041876c058b522e0624db4fb6. Candidate remains feature/customer-first-marketplace, HEADba3057784e36f1c984e90f54b0695586a8c97650 plus dirty changes;3undeployed commits and broad marketplace/KYC/session/security/CI/infrastructure-template scope, not only Maps/payment/email. No commit/push/deploy/DNS/paid resource/production migration or additional external email/charge/refund.

Fresh explicit read-only Neon production branch transaction returned22; migrations23->24->25->26->27->28->29pending. Runtime API-to-DB binding remains unverified due sensitive values. Aggregate affected provider/document/booking/trip counts0at inspection, not permission to skip backup. Existing recovery branches15October are not fresh verified restore points. Migration23reverification and all seven refused downgrades make old-code rollback conditional and unsafe without review.

Final fresh backend429passed (external network blocked); frontend54passed; types/build/Ruff/domain mypy/offline linear29SQLpassed;4isolated PostgreSQL migration/KYC/Maps checks passed. New local email race check1passed; normal subject/Reply-To/TLS loopback capture passed, no external send. npm prod/all advisory audits0; OSV87installed Python packages0findings, not a production lock. Bounded known-credential/pattern/3included-commit/path scan has no findings; no general unknown-secret guarantee. Test-isolation bug fixed only in publication test. Sandbox CLI initially refused29; reproduced/fixed to acceptONLY28/29and rejectolder/future while retaining all sandbox/database-role guards; actual refund not executed.

Fresh GET-only Razorpay reconciliation confirms existingTestkey mode and old1200paymentcaptured; no refund, no reveal on that real selection;99ordersno payments andlocallyexpired. Local order_local/pay_ui captures remain simulations. NoLive test/activation; productionkeys/webhook matching unreadable. User reports3emails with SPF/DKIM/DMARCPASS inONE unspecified approved Gmail mailbox; Inbox/Spam placement and second-mailbox receipt unconfirmed. No repeated external messages.

NO-GO for full operational launch: missing production Maps browser-key/ownedMapID/restriction proof; PUBLIC_FRONTEND_URLentrymissing; sensitiveSMTP/payment production values cannotbe matched; preview credentials stillshared; productionKYC/scanner/consent/retention/onboarding notaccepted;99inclusiveproduction pricing/tax unresolved and fallbackstill1200; completed99capture/reveal/refund andproductionrefundoperationsnotverified; freeze SHA/config/artifacts, protected fresh backup/rehearsal/window notready. Package distinguishes safely disabled capabilities from core publication/payment blockers. No approval requested for a blocked/unspecified deployment; next owner inputs are consolidated in the proposal.

## Owner-authorized real Brevo email verification — 25 October 2026 IST

Read [real SMTP results and limitations](testing/2026-10-25-brevo-real-email-verification.md). Owner authorized sends only to two named Gmail recipients. Completed guarded isolated local test journey: actual Brevo587 STARTTLS TLSv1.3/certificate validation/authentication PASS;6SMTP-accepted messages total,3per approved address (registration/resend/reset). Zero other recipients. Configured60-second cooldown preserved and tested, including suppression with no send and resend after62seconds. Both accounts: superseded verification400, current200/reuse400; reset200/reuse400; old access401, old refresh401, new-password login200/logout204. Actual message URLs matched local frontend origin and fragment format; frontend HEAD200. Existing local account collision guard passed before creating the two synthetic users. No credentials/tokens/body printed or persisted in evidence.

SMTP acceptance is NOT confirmed inbox delivery. Owner asked to confirm Inbox/Spam receipt and Gmail Show original SPF/DKIM/DMARC result statuses; pending. Real browser UI not rerun: current real journey uses actual API code over in-process ASGI with same local PostgreSQL/config; prior simulated desktop/mobile browser evidence retained separately. Test wrapper used default booking-update subject, whereas normal account factory uses account-security subject; recorded as harness limitation, no extra sends. Tokens/links have been consumed by automated tests. Prior expiry/invalid negatives reused as local evidence only. No app source changes this run; workspace-only Windows harness pseudo-environment defect corrected before any SMTP operation.

Branch/currentdirtycandidate preserved; no push/deploy/DNS/production/Razorpay change. Workspace outputs/2026-10-25-brevo-authorized-email.json has sanitized results. No further email automatically scheduled; do not blindly rerun the six-message journey or overwrite its retained synthetic accounts. Next action is recipient confirmation/header statuses; do not equate provider acceptance with delivered/domain-authenticated email.

## Saved email configuration verified — 25 October 2026 IST

Owner saved repository-root .env and explicitly requested local API restart/configuration verification only. Restart completed: actual API listener PID24472, local127.0.0.1:18000 ready; actual working directory repository root. Effective settings preflight using the same preserved process environment confirms SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD, EMAIL_FROM and PUBLIC_FRONTEND_URL populated; SMTP_PORT587. Optional EMAIL_REPLY_TO blank. Root .env remains the selected Git-ignored private file; no duplicate credential file created or values printed. STARTTLS source confirmed before login/send with ssl.create_default_context certificate/hostname validation. Exact isolated database/payment safety guard passed; no production or Razorpay change, no SMTP connection/authentication test and no email sent. This supersedes the preceding blank-template status only. Sender/domain verification, provider DNS authentication and actual recipient delivery remain unverified; real sends still require owner authorization. Sanitized startup evidence is in workspace outputs/2026-10-25-email-startup-configuration.json.

## Local email configuration-path correction — 25 October 2026 IST

Owner selected Brevo and reported saving SMTP credentials. Direct read-only presence checks found NONE of repository-root .env, backend/.env, root .env.txt or backend/.env.txt. No existing credential file was overwritten or renamed. Created exactly one blank template at repository-root .env (confirmed Git-ignored), and requested the app editor open it; app returned queued. SMTP_HOST/SMTP_USERNAME/SMTP_PASSWORD/EMAIL_FROM/EMAIL_REPLY_TO/PUBLIC_FRONTEND_URL remain blank; SMTP_PORT blank uses application default587. No credential value printed, no Brevo connection/authentication/send attempted.

Actual old API listener PID9508 ran workspace/run-local-maps-api.py from the TASK WORKSPACE, so its relative .env loading did not target the repository root. Updated ONLY that workspace-local launcher to chdir to the absolute repository root before importing backend settings; production Settings behavior/code untouched. Root .env is now the single intended local backend configuration. Existing environment preserved privately in memory during restart; no copied credential file. Guarded preflight confirmed exact isolated loopback database and disabled real/sandbox checkout. Actual restarted API listener PID5080 (Windows virtualenv wrapper PID31180) verified running from repository root, serving127.0.0.1:18000; /health/live200. STARTTLS with hostname/CA validation remains in source; effective port587. Other processes/payment integration untouched.

Next: owner privately fills the root .env template, then recheck populated booleans and restart this local API. Credentials are not yet verified and no external email delivery is authorized. Do not infer SMTP authentication or delivery from local configuration checks. Workspace outputs/2026-10-25-email-startup-configuration.json records sanitized startup proof. Configuration guide below reflects template creation; older file-absent evidence is historical.

## Latest continuation — local account email integration, 25 October 2026 IST

Read [current email verification](testing/2026-10-25-account-email-verification.md) and [private configuration, DNS findings and controlled-delivery plan](operations/account-email-setup.md) before further email work. Existing dirty feature/customer-first-marketplace candidate and HEAD ba3057784e36f1c984e90f54b0695586a8c97650 preserved. No push/deploy/production/DNS/real-email/payment operation. Do not touch verified Razorpay integration.

Generic STARTTLS SMTP adapter reused; no vendor/sender/SMTP credentials configured in inspected local settings. Added explicit certificate/hostname validation, optional EMAIL_REPLY_TO, validated API-only PUBLIC_FRONTEND_URL and safe frontend fragment links with explicit submission, registration verification delivery preserving session/cookie behavior, and durable resend suppression with configurable60-second default. Existing recovery rate limits preserved. Improved password accessible label. No migration.

Fresh evidence: affected backend24passed including2isolated PostgreSQL cases; cookie/rate-limit20passed; final frontend6passed; desktop/mobile browser2passed with simulated APIs and all non-loopback requests blocked; types/build and affected Ruff/diff checks passed. Strengthened registration PostgreSQL case rerun1passed after final test extension: immediate resend suppressed, known/unknown202equal, explicit verification, reset-token reuse400, old access401, old refresh cookie401 and new-password login200. Counts overlap; do not sum reruns. Actual loopback-only TLS SMTP capture passed synthetic message/Reply-To and rejected an untrusted certificate before message transmission. External delivery remains NOT RUN/BLOCKED. Real local SMTP is not real provider acceptance/inbox delivery.

Read-only public DNS via two resolvers found no MX or root TXT answers for transivox.in and an existing DMARC quarantine policy. No DKIM selector/provider guessed, no DNS changed. Public HEAD: apex308 ->www, www200. Required local inputs: identify existing SMTP provider/account; privately supply SMTP_HOST/PORT/USERNAME/PASSWORD/EMAIL_FROM, optional monitored EMAIL_REPLY_TO; supply exact provider-issued authentication records and designate one controlled recipient plus separate approval for real sends. Repository-root .env is ignored and currently absent; run API from repository root. PUBLIC_FRONTEND_URL local http://127.0.0.1:5173, future approved production https://www.transivox.in, isolated preview's own HTTPS frontend. Never put SMTP credentials in VITE/.env.local, logs or chat. Preserve existing MX/DMARC/unrelated DNS and avoid duplicate SPF. A sending service does not necessarily provide an incoming mailbox.

Remaining contract limitation: recovery/resend responses are generic, but signup retains the existing duplicate-email409 and immediate authenticated-session behavior. Full signup non-enumeration requires an explicitly scoped signup-flow decision; it is not reported as solved. Existing frontend bundle-size warning remains nonfatal. Maps and payment evidence below remain dated and untouched.

# TransivoX project handoff

## Latest local Google Maps verification — 25 October 2026 IST

Owner explicitly resumed local Maps integration/real API tests; OTP remains deferred and no Razorpay operation was authorized in this Maps task. Read [actual Maps results and remaining production gates](testing/2026-10-25-local-google-maps-verification.md) and [configuration/run instructions](operations/local-demand-maps.md). Actual frontend127.0.0.1:5173, ordinary isolated API18000, guarded local DB55432/transivox_e2e; KYC simulationfalse, real checkoutfalse and Razorpay sandboxfalse on this API. Existing separate payment processes/configurations were not changed for Maps verification.

Real Google Maps/Places New worked with the owner's private .env.local browser key and DEMO_MAP_ID: actual India Gate/Connaught Place predictions selected independently, private addresses/pins synchronized, Google attribution present, real keyboard marker drag required confirmation, manual pickup edit cleared only its pin, draft save/dashboard resume retained values. Real network/draft smoke1passed with0Googleerrors/0failedGoogle requests; mobile390nooverflow and Termsinside map. Actual publication403required customer KYC;0published before/after, no bypass. Full successful publication is only simulated-compliance PostgreSQL/browser evidence, not a real KYC-approved flow.

New additive nullable private location columns applied ONLY to local DB:28->20261025_29. Backend focused15passed, PostgreSQL1passed, frontend52passed with final4affected state tests, final typechecks/buildpassed; migration/Ruff/diffpassed. Final browser5simulated +1real passed. Fixed late Places overwriting newer manual city/pin edits after a failing regression, mobile radio/mapoverflow/loading retry and UTF8 labels; separated static simulation harness from Vite/HMR interference. Current source manifest/testing report records boundaries and files. No route distance/geocoding call or change to backend Routes adapter. No key printed/staged, .env.local ignored.

Production Maps still needs project-owned Map ID, reviewed production browser-key restrictions/privacy/data treatment, migration29/API/frontend compatibility and existing preview/release approvals. No Google billing/referrer/API blocker observed locally; dashboard restriction scope not independently inspected. No push/deploy/production migration/API enablement/billing/OTP/Razorpay operation. Existing other release work remains incomplete; do not treat this focused report as a broad audit or public-launch approval.


## Checkout screen updated to99 — 25 October 2026 IST

Owner requested removing1200 from visible checkout. Loopback18113 now displays99total including all charges and ONLY new9900paise Test Mode orders: reveal order_Ts3sKagAkTnh39 (selectionf62d3db7-d726-407d-9f0c-bc3f17cc8a74), refund order_Ts3sOWEJLZa8Gq (selectiona6dd73f9-72f8-46b8-9673-9c6925ab2e00). Both created through ordinary running API and contactlocked. Browser verified header and bothbuttons99, no1200copy. Historical orders preserved privately but excluded from screen. No payment/refund executed for this update; live remainsdisabled. Browser handoff page updated; usercheckout stillrequired.



## Current Test Mode fee — 25 October 2026 IST

Owner confirmed99INR TOTAL including everything after being asked total versus base; apply to new Test Mode checkout only, live prohibited. Private workspace load-razorpay-test-env.ps1 now uses policy razorpay-sandbox-fee-99-v2 with base82.50 plus16.50 illustrative20percent test tax =99.00 (9900paise). This preserves the prior proposed test rate, not a confirmed legal tax determination. Running isolated API restarted and public marketplace config verified total99, test_onlytrue, real_checkout_availablefalse. Configuration arithmetic assertions passed. No new payment/order/refund initiated for this config change. Historical1200orders/booking snapshots unchanged and cannot be repriced; existing checkout helper buttons refer to those older orders. Fresh99checkout requires a new selection and order. Prior1000base/1200total statements are historical for test policy; production commercial/tax activation remains blocked. No production/source push/deployment.


## Current Test Mode execution — 25 October 2026 IST

Read testing/2026-10-25-razorpay-test-execution.md. Owner saved private Test credentials and confirmed dedicated webhook. Test authentication200; local DB isolation reverified; API/relay reloaded without changing HTTPS URL. Two real Test Mode orders120000paise INR prepared. First order required exact provider receipt/amount/currency audited reconciliation after ambiguous503; second succeeded through normal API. Actual failed mock-bank attempt produced genuine signed payment.failed delivery, outcome failed_no_unlock, contact locked. Repeated checkout reuses existing order; other customer404; local reconstructed replay with same actualeventID200/200, invalid401, one stored event. No capture or refund occurred.

Automatic approval review rejected entering the official synthetic card/continuing checkout, requiring user handoff even in Test Mode. Do not bypass. User next completes both existing reveal/refund checkout buttons at loopback http://127.0.0.1:18113/ using Test Mode only, without revealing/cancelling in app. Then agent verifies actual captured evidence and explicit reveal/repeat access on first booking, pre-reveal full sandbox refund and exact provider final reconciliation on second. Capture/reveal/refund success remain BLOCKED, not passed. No credentials need reentry. Live checkout/tax confirmation false; illustrative20percent remains test-only. No push/deploy/production change. Processes/tunnel kept for user handoff.


## Owner-authorized Test Mode resumption — 25 October 2026 IST

Owner explicitly resumed synthetic Razorpay Test Mode payments/refunds; live remains prohibited. This supersedes the earlier payment pause only. Dashboard changes and actual provider journey await owner confirmation and private keys. Private razorpay-test.dpapi.xml is absent; preflight-only signing secret exists. No API key/secret printed or provider operation initiated.

Current temporary webhook URL: https://studied-buffalo-prescribed-labs.trycloudflare.com/api/v1/connection-fees/webhook . Local API18110 and webhook-only relay18111 run with the separate patched release runtime. Read-only identity guard confirmed local127.0.0.1:55432/transivox_e2e, restricted transivox_e2e_user, head20261023_28. No reset/bootstrap E2E router exposed. Fresh local-signature HTTPS transport200/replay200/invalid401, one unmatched event, unchanged bookings/captured entitlements; docs/reset/bootstrap404. Evidence outside Git: outputs/2026-10-25-razorpay-https-signed-transport.json. These are simulated event transport results, NOT Razorpay-originated delivery.

Use a dedicated Test Mode webhook because ownership of the existing14-event webhook is unconfirmed. Handler supports payment.captured, payment.failed, refund.created, refund.processed, refund.failed, payment.dispute.created. Preserve existing integration until owner confirms it is unused. Privately enter Test keys and same dedicated webhook signing secret using workspace secure-entry script; reload API/relay credentials without restarting tunnel before dashboard test. Current processes use preflight signing secret until that reload. Do not attempt provider journey until dashboard confirmation. Live checkout/tax confirmation stay false; illustrative test-only1000+200; waiver blocked. Temporary URL requires running local PC/processes and changes if tunnel restarts. No production settings changed.


## Active owner instruction — 24 October 2026: non-payment release work

Razorpay credential setup and ALL external Test/Live operations are explicitly paused until the owner resumes them. Do not request the credential-entry script, read private Razorpay values, reopen a tunnel or call Razorpay. OTP and Google Maps remain deferred. Current authorized work is local customer/provider/admin/KYC/UI/auth/release preparation, read-only AWS availability and public pricing research. No push/merge/deploy/production data/migrations/DNS/paid resources/real messages/payments/refunds. Preserve dirty candidate and reuse valid evidence. Work-in-progress plan is in the task workspace work/2026-10-24-release-continuation-plan.md. Final results will supersede the older next-task text below.


## Latest continuation — Razorpay sandbox refund execution, 24 October 2026 IST

Read [current Razorpay verification and private setup instructions](testing/2026-10-24-razorpay-test-mode-verification.md) first. This section supersedes older statements that no executable refund adapter exists or that a hypothetical waiver tax can enable checkout. Real sandbox verification is **BLOCKED by missing Test Mode API credentials/webhook secret**. No Razorpay order/payment/refund has been created; no real provider-originated delivery or live integration is claimed.

Branch `feature/customer-first-marketplace`, HEAD `ba3057784e36f1c984e90f54b0695586a8c97650`, existing dirty candidate preserved. No commit/push/production deployment/migration or production setting change. User now specifically authorizes isolated real Razorpay Test Mode payments/refunds and temporary webhook exposure, never live money or production actions.

Implemented guarded Test Mode HTTP order/payment/refund adapter and CLI-only refund executor, durable key/body/refund references, unknown/pending/failed/processed reconciliation and exact signed refund matching. Refund creation acknowledgement is not completion. Additive migration28 was applied ONLY to verified loopback PostgreSQL127.0.0.1:55432/transivox_e2e, restricted transivox_e2e_user. Single schema head20261023_28. All waiver checkout, including historical hypothetical test-tax override, is now blocked pending real tax/accounting decisions.

Fresh affected unit checks67 passed; final refund executor/webhook PostgreSQL9 passed; final binding/unique credit/blocked-waiver2 passed. Earlier affected PostgreSQL26 passed; these counts overlap and some preceded final corrections, detailed in the report. Ruff/diff check and offline migration compilation passed. Unchanged frontend/browser/scanner/full-suite evidence was reused, not relabelled as a new run.

Temporary webhook-only HTTPS tunnel passed public route isolation and signed transport/replay through actual local API/PostgreSQL using a clearly simulated unmatched event:200/200/401, one event and no new booking/entitlement. This is not a Razorpay delivery. Fixed local Windows psycopg event-loop startup after reproducing the failure. All temporary tunnel/API/relay processes were stopped while credentials are missing; restart will require a fresh Test Mode webhook URL. Private DPAPI entry/loader/launcher scripts and evidence are outside Git in the task workspace. Next: owner privately enters intended merchant Test Mode keys; restart the isolated API/relay, register only Test Mode webhook and execute the explicitly authorized actual sandbox journey. Keep live checkout/tax confirmation false and never expose reset/bootstrap/admin endpoints. Preserve all earlier local data/helpers and source changes.


Updated **23 October 2026 (IST)**; historical production snapshot is from 21 October. Original handoff creation was documentation-only.
Owner subsequently authorized publishing all pending source to this development
branch. Read Git HEAD/status for publication state; the snapshot below identifies
the pre-commit tested contents, not remaining dirty work after publication.
Production rollout remains blocked; no deployment, migration or cloud activation.
**Not public-launch ready.** Read this before continuing; do not restart a broad audit.

## Current scanner, customer KYC and fee-policy continuation — 23 October 2026

This is the existing full production-site pivot, not a fresh build. Feature branch `feature/customer-first-marketplace`, base/current HEAD `ba3057784e36f1c984e90f54b0695586a8c97650`, all candidate changes uncommitted and preserved. No push/deployment/production migration/cloud activation or real payment/refund/send.

Read [consolidated current verification and remaining inputs](testing/2026-10-23-scanner-fee-release-verification.md) first; it supersedes older next-task and undecided-refund/customer-implementation statements below. Real local ClamAV and configurable customer submission/review/publication gates are implemented; actual AWS/scanner/site acceptance remains blocked by access. Additive schema now includes26 customer KYC and27 explicit reveal/refund/credit history after25. Base fee1000, proposed unconfirmed tax20%=200, total1200; real checkout remains disabled. Explicit Reveal contact, full prereveal refund request, no ordinary postreveal refund, and audited one-use failure credit are implemented locally; waiver tax and listed credit rules remain unresolved.

Fresh380 backend tests,46 frontend tests,57 PostgreSQL plus1 skip and6 focused cases,8 final browser tests, actual ClamAV detection/oversize cases and a58-table local restore passed. Current head is20261023_27. Rate-limit failures were synthetic-client test interference, fixed only at test boundaries. Preserve ignored helpers/evidence. Next task is restore personal AWS access for minimal account/bucket/IAM reads, review the costed proposal and remaining policy inputs, then obtain separate external-action approvals. Do not restart a broad audit or rerun completed local checks without new changes.

## GitHub preparation update — 23 October 2026

This is the existing Trucksetu pivot, targeting a full production website, not a limited MVP. Local feature branch: `feature/customer-first-marketplace`, based on `ba3057784e36f1c984e90f54b0695586a8c97650`. All existing work is preserved. No new commit, push, PR, deployment or production migration has occurred during this preparation.

Owner requires customer Aadhaar and PAN document review before demand publication. This requirement is not implemented; the existing-account sandbox policy does not meet it. Real checkout remains disabled pending commercial policy decisions. The current source retains shared-capacity functionality but disables provider-first public publication by default; this differs from the older recorded evidence below and requires separate scope confirmation before release.

Read-only Vercel environment metadata still shows shared production/preview entries for API URL, payment keys, AWS storage and messaging credentials in both projects. No branch-specific preview entries were returned for this feature branch. Preview isolation cannot be established; do not push until an isolated preview or independently reviewed non-deploying publishing path is established. No secret values were decrypted and no cloud settings were changed.

Fresh backend verification: 363 tests passed, Ruff passed, domain mypy passed, and offline migration compilation passed with single head `20261021_25`. The preceding full isolated PostgreSQL run remains 47 passed, 3 HTTP-429 failures and 1 skipped; no new passing integration claim is made. Older browser/restore evidence remains dated; final booking/ledger browser assertions remain unrun.

## Current local continuation — 23 October 2026

The owner subsequently authorized a customer-led demand/bid MVP with one winning provider and a configurable INR 1,000 one-time connection fee per booking. This is a separate fee for the explicitly promised verified provider/driver contact, not freight payment. A verified number must exist before checkout; driver contact added later on the same booking costs no second fee. Real checkout remains disabled pending tax, cancellation/refund, provider-failure and replacement-provider decisions. Shared capacity, including publication, remains independently enabled and retained.

Working branch remains `codex/launch-preparation-no-otp-maps`, HEAD `ba3057784e36f1c984e90f54b0695586a8c97650`; local implementation and verification changes are uncommitted. No push, deployment, production migration or cloud change occurred. Historical production observations below remain dated evidence.

Read [current focused verification](testing/2026-10-23-customer-demand-verification.md), [feature retention/configuration/release boundary](operations/customer-demand-marketplace.md) and the customer-demand specification/plan before continuing. New additive local migration is `20261021_25` after 24. Separate fee/event tables preserve freight accounting and historical data. Auth, immutable scan evidence, manual review and KYC gates remain authoritative. Sandbox evidence uses fictional compliance fixtures and simulated signed payment events; it is not actual scanner/gateway acceptance.

This section supersedes the old “Single next task” at the end. Preserve all dirty work and ignored helpers. Reuse current evidence; do not restart the audit. Complete any explicitly listed remaining checks in the focused report, then review commercial/customer-verification decisions and independently approved real-integration/release gates. No production E2E, scan bypass, automatic refund, new fee on an unresolved checkout, destructive downgrade or unapproved external action.

## Purpose, architecture and instructions

TransivoX/Trucksetu connects Indian customers with independent transport providers,
fleet owners and drivers. Provider quotations explicitly accepted by customers set
final prices; route-price suggestions are advisory. Shared capacity is required.

React/TypeScript/Vite frontend (`src/`); FastAPI/SQLAlchemy/psycopg backend
(`backend/app/`); PostgreSQL source of truth; Alembic migrations; Redis abuse
protection/coordination; private versioned S3 documents; external-service adapters
in `backend/app/services/`. Frontend/API are separate Vercel projects.

Follow root `AGENTS.md`, `SECURITY.md`, `DEPLOYMENT.md` and `DESIGN.md`, plus any
deeper instructions. Preserve architecture, role/ownership checks, monetary
snapshots and user changes. Use Phosphor-only functional icons. Use applicable
skills: diagnosis/TDD for defects, approved design before new subsystems, fresh
verification before claims. Do not delegate unless active instructions permit it.

## Pre-publication verification snapshot: preserve everything

- Branch: `codex/launch-preparation-no-otp-maps`.
- Base HEAD: `66c63d17897837afc88f457dab0c0e7b8942ac2a`.
- Tests covered this base WITH the following pending changes, not base HEAD alone.
- Modified: `backend/app/api/payments.py`, `backend/app/core/middleware.py`,
  `backend/tests/test_account_recovery.py`, `backend/tests/test_vehicle_documents.py`,
  `docs/testing/2026-10-14-release-candidate-checklist.md`,
  `e2e/fixtures/shared_database.py`, `e2e/public-session.spec.ts`,
  `e2e/release-shared.spec.ts`, `package.json`, `package-lock.json`.
- Untracked: `backend/tests/test_release_payment_callbacks.py`,
  `test_release_sensitive_logging.py`, `test_smtp_acceptance.py` (same directory),
  `e2e/release-vehicle.spec.ts`, `docs/operations/`, `ops/`, the scanner design,
  launch ledger, consolidated handoff/source manifest linked below, and this file.
- Preserve ignored `.tmp/` operational helpers, DPAPI-encrypted local credentials,
  `.venv/`, reports/screenshots and pinned `.tmp/production-schema-ccd594d`
  checkout. Never commit credentials/generated artifacts or reset/clean the tree.
- [Changed-source manifest](testing/2026-10-21-launch-source-manifest.json) records
  19 source/template files; combined SHA256
  `7991604990131366135b7b591845343e9849c106bbeebe166988d601cce7b0b0`.
  Documentation/generated outputs are excluded. Recheck status before editing.

## Last verified production — 21 October

Authenticated Vercel reads identified **both** API and frontend at
`ccd594df8a78f56041876c058b522e0624db4fb6`, branch `main`:

| Resource | Identity |
|---|---|
| Repository | `HARSH3330/trucksetu` |
| API | `trucksetu-api`; `dpl_BycVRnLKUmjYfcKXMbkwrVesGYqj`; https://trucksetu-api-nine.vercel.app |
| Frontend | `trucksetu-whri`; `dpl_FExE8Kd4d9uFR29nAgsLHmUUpoB8`; https://www.transivox.in |
| Neon | project `morning-forest-29164100`; production `br-polished-surf-axulzu38`; endpoint `ep-fragrant-surf-axkjz078`; database `neondb` |

Explicit branch-scoped read-only SQL: revision **20261014_22**, `users.auth_version`
present. Aggregate counts were zero for bookings, nonterminal trips, verified
providers/applications, non-rejected legacy KYC documents and approved vehicles.
These are time-bound observations; recheck before an authorized rollout.

At approximately **03:26 UTC / 08:56 IST**, `/health/live` and `/ready` returned
200; database/Redis available. `/version` returned malformed `ca`; use authenticated
deployment metadata for source identity. Candidate build-ID fix is undeployed.
Runtime DATABASE_URL binding was not independently re-established from secret
configuration. Readiness does not prove S3, scanner, payments or delivery.

Local cookie sessions/logout, shared quote acceptance, provider VersionId
protection and Phosphor/restyle changes are **not deployed**. Current candidate
header has Sign out; deployed source lacks that handler/button.

Retained recovery branches: `pre-migration-20261015` (`br-morning-base-ax0dr2z2`),
`pre-repair-22-20261015` (`br-frosty-mountain-ax2vpqat`); rehearsal
`migration-rehearsal-20261015` (`br-weathered-hill-axdizmg3`). Listed unchanged;
not fresh restore points or proof of historical restoration.

## Completed locally and verification evidence

**21 October**, recorded in the [consolidated report](testing/2026-10-21-launch-preparation-handoff.md):

- Late online/offline payment confirmations preserve cancelled/progressed booking
  states; booking-first locking, webhook replay serialization, malformed-event
  handling and operator audit evidence. Tests use real HMAC but fake DB/gateway.
- Unexpected errors redact exception contents/tracebacks while retaining request
  correlation and controlled secure 500 responses.
- Recovery/email expiry, reuse, attempts, session invalidation and SMTP acceptance
  tests expanded. SMTP is simulated; acceptance is not confirmed mailbox receipt.
- Vehicle nonclean-scan tests expanded; limiter-state test isolation fixed without
  increasing/disabling production limits. Vite patched/pinned to 8.2.4;
  source-map-js lock updated to 1.2.2.
- **353 backend non-integration tests PASS**, Ruff/domain mypy PASS;
  **46 frontend tests PASS**, builds PASS; **37 public + 4 design browser tests
  PASS**, synthetic APIs/widget/storage boundaries, Chromium.
- Final logout follow-up: **2 focused tests PASS**, including 390/1440px visible
  44px logout action, cookie clearing, reload/Back protected-state checks.
- npm audit: zero known vulnerabilities after patch. Offline migration check:
  linear head **20261014_24**, SQL compilation PASS, not database execution.
- Eight real-DB browser scenarios collect; expanded shared/vehicle specs type-check
  but are **BLOCKED, not passed**. They add UI-created route/request and mobile
  vehicle creation/upload/review; fictional identities/compliance prerequisites
  remain seeded. Complete operational/multi-role/mobile coverage remains partial.

[19 October PostgreSQL evidence](testing/2026-10-19-isolated-postgresql-verification.md)
is historical: 25 real PostgreSQL cases, 6 browser journeys, 356 backend passes/
one opt-in skip, including migrations 23/24. Its source fingerprint differs;
do not apply those results to today's pending changes. Fresh-context review
failed immediately on an account usage limit; no reviewer approval is claimed.
Existing bundle-size and dependency deprecation warnings remain.

## Blockers and prioritized remaining work

1. **Restore isolated DB verification:** Docker Linux engine `/v1.56/version`
   returned `500 Internal Server Error`; guarded local connection returned
   `ConnectionTimeout`. Run current DB regressions, eight browser scenarios,
   fix reproduced failures, then isolated backup/restore. No fallback database.
2. **Scanner:** application supports GuardDuty exact-version tags only; ClamAV
   is **not implemented**. No usable AWS management connector/local credentials;
   previous `SubscriptionRequiredException` cause remains unverified. Real
   scanning/deployed KYC are blocked. Historical nine-check S3 probe is storage
   evidence only. Review [scanner design](superpowers/specs/2026-10-21-private-malware-scanner-design.md)
   before new subsystem implementation or paid activation.
3. **Razorpay:** filtered connector read failed `Authentication failed` /
   `INVALID_ARGUMENT`; not evidence website keys are wrong. Reconnect intended
   test merchant, approve isolated sandbox capture/webhook/refund reconciliation.
   Automatic gateway refunds are not implemented; current API records external
   manual refunds.
4. **Release gates:** finish operational/customer/provider/driver journeys,
   real email receipt, deployed browser/mobile persistence (cross-site cookie
   restrictions matter), alerts, backup restoration, independent security and
   qualified Indian legal/privacy/tax review. Resolve business/retention/policy
   inputs; never invent them.
5. **Coordinated release:** fresh recovery/impact review; rehearse bounded
   migrations 22→24, then separately approved production migration, API first,
   matching frontend second. Both migrations refuse destructive downgrade;
   old-code rollback can reopen unsafe unversioned behavior. No automatic restore.

## Non-negotiable decisions and permissions

- Shared capacity is required: provider quote explicitly accepted by customer;
  transactional capacity, expiry/cancellation release, idempotency and immutable
  accepted financial snapshots. Acceptance never means paid.
- OTP/Google Maps are deferred, **not completed**. Google sign-in, phone-only
  login, recurring requirements and broader admin configuration remain unresolved
  scope decisions, not approved omissions.
- KYC registration/review/download require trusted clean status on the **exact
  immutable VersionId**; missing/failed/unsupported/infected remain blocked.
  Clean scanning does not replace manual document acceptance.
- Approved vehicle replacement: admin suspends; admin rejects old document with
  reason; provider uploads replacement; clean scan permits registration; renewed
  document acceptance and vehicle approval. Retain old records/audit history.
- Historical approval covered a specific 18→22 database repair/redeployment;
  it is not authorization for future writes. Current work allows local edits/tests
  and preparation only. No commit/push/merge/deploy, production migrations, cloud
  changes, paid activation, real sends/payments/refunds without specific approval.

## Configuration and local commands

Backend names: `DATABASE_URL` (runtime), `MIGRATION_DATABASE_URL` (direct),
`REDIS_URL`, `REDIS_REQUIRED`, `APP_ENV`, `DEBUG`, `SECRET_KEY`, `ALLOWED_ORIGINS`,
`TRUSTED_HOSTS`, `AUTH_COOKIE_SAMESITE`, `ACCESS_TOKEN_EXPIRE_MINUTES`,
`REFRESH_TOKEN_EXPIRE_DAYS`; frontend public `VITE_API_URL`.
S3: `AWS_S3_BUCKET=transivox-kyc-harsh3330`, `AWS_REGION=ap-south-1`, prefix `kyc/`;
secret names `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` are backend-only.
SMTP: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `EMAIL_FROM`.
Payments: `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET`;
callback `/api/v1/payments/razorpay/webhook` on the approved isolated API.
Deferred MSG91: public `VITE_MSG91_WIDGET_ID`, `VITE_MSG91_WIDGET_TOKEN_AUTH`;
API `MSG91_WIDGET_ENABLED`, secret `MSG91_AUTH_KEY`, `MSG91_TEMPLATE_ID`,
`MSG91_OTP_VARIABLE`. Deferred Maps: API `GOOGLE_MAPS_API_KEY`.
See `.env.example` and [integration/operations plans](operations/) for
IAM/CORS templates, sender setup and proposed alerts.

Prerequisites: Python 3.12, Node >=22.12, installed project dependencies,
Playwright Chromium, working Docker. If missing: `npm ci`, install backend
editable dev dependencies with venv Python (`-m pip install -e './backend[dev]'`),
and `npx playwright install chromium`.

```powershell
cd 'C:\Users\harsh\OneDrive\Desktop\english learning\logistic\trucksetu'
docker version                         # stop on engine error
docker ps -a --filter name=transivox-e2e-postgres
docker start transivox-e2e-postgres    # existing dedicated instance only
. .\.tmp\local-postgres-env.ps1       # private DPAPI helper; never print/copy
& $env:E2E_PYTHON .tmp/check-local-postgres.py
if ($LASTEXITCODE -ne 0) { throw 'Stop: isolated DB unavailable' }
# LOCAL ONLY; inspect exact target before any migrations/resets:
Push-Location backend
try { & $env:E2E_PYTHON -m alembic upgrade 20261014_24 }
finally { Pop-Location }
if ($LASTEXITCODE -ne 0) { throw 'Stop: local migration failed' }
& $env:E2E_PYTHON -m pytest backend/tests/integration -q -p no:cacheprovider
if ($LASTEXITCODE -ne 0) { throw 'Stop: PostgreSQL tests failed' }
npm run e2e
npx playwright show-report playwright-report
```

Container/volume: `transivox-e2e-postgres` / `transivox_e2e_postgres_data`;
loopback port 55432, restricted `transivox_e2e_user`. Require explicit
`E2E_DATABASE_URL`, exact `transivox_e2e`, approved local host,
`APP_ENV=test`, `TRANSIVOX_E2E=true`, `E2E_REAL_AWS=false`. Helper validates before
exporting runtime variables. Never use production/Preview/Neon as E2E fallback.
Browser tests reset this isolated DB; run sequentially. Test account defaults:
provider.e2e@example.com/admin.e2e@example.com; credentials configurable, not copied here.

For manual local fake-boundary development after validation, use separate shells:
venv Python with `PYTHONPATH=backend` → `-m e2e_server --port 18000` from backend;
frontend `VITE_API_URL=http://127.0.0.1:18000/api/v1`, `npm run dev` from root.
Do not run manual servers alongside Playwright-managed servers. No real AWS.

## Single next task

**Restore the existing isolated PostgreSQL service and verify this exact dirty
candidate.** Acceptance: engine reachable; dedicated container/volume preserved;
exact-name/host/restricted-role checks pass; local migrations through 24 and
current session/capacity/financial regressions pass; all eight real browser
journeys run or precise failures recorded; source fingerprint updated. External
integrations stay simulated and KYC scanner approval stays blocked. Stop on
unsafe targets; request approval before disruptive Docker recovery. Use the
consolidated report for details, not a new broad audit.
