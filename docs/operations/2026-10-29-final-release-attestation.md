# Exact-commit release attestation — 29 October 2026

Source: `634b41df258fa74e0e900643cc202896b3e146d3`, branch `release/customer-first-20261026`, parent `fa2595741d261cf15d2c0849b13e446d1eaffd20`. Reviewed commit pushed normally to PR1; no merge. Only the eleven reviewed code/test/workflow/documentation paths were included; pre-existing handoff contents preserved. Source checkout was clean after commit. This post-commit attestation does not change the frozen source identity.

## Evidence and remaining gates

| Check | Result | Evidence |
|---|---|---|
| Incident release-preparation sign-off | PASS | Owner accepts retained-state findings and historical evidence limit. No detected stranded records or repair indicated; absolute historical no-loss proof unavailable. Copies and snapshot preserved. |
| Reconciliation endpoint cleanup | PASS | Fresh metadata: ep-morning-sunset-axii59da remains read_only, min/max0.25CU, idle, suspended_at2026-10-29T08:51:31Z, bound to br-young-wind-axoimpov. Existing endpoint bindings retained. |
| Push deployment guard | PASS for observed branch | Both root/backend vercel.json disable this exact branch; no deployment Actions job. Post-push both projects list zero release-branch deployments. No production deployment invoked. |
| Source/build artifact binding | PASS | artifact-manifest.json records exact SHA and four SHA256 digests. Source is Git archive of exact commit. All64 backend wheel Python files equal archive. Frontend built with existing public Production Maps inputs, explicit production API origin and legacy marketplace false. No private environment files copied; only tracked example templates in source. |
| Hosted CI | PASS | Run40858565724 backend/frontend/containers and browser run40858565740 all success for head634b41df. Browser steps all success:72 PostgreSQL integration tests,8 legacy KYC/session/shared/vehicle browsers,8 demand/fee/session browsers,3 customer KYC/management browsers,5 simulated Maps and2 simulated email-link browsers. These simulations do not establish real Google/Brevo acceptance. |
| Google Cloud private configuration | PASS, owner evidence | Owner confirms www referrer, Maps JavaScript API/Places API(New), owned JavaScript Map ID and billing. Vercel frontend Production entries present. Real production functionality unperformed. |
| Brevo configuration | BLOCKED for sensitive-value correctness | Five required backend Production entries present; PUBLIC_FRONTEND_URL exact www; active sender evidence reused. SMTP host/port/login/production-key/sender private confirmation pending. Provider delivery, mailbox receipt and authentication unperformed. |
| Frontend API origin setting | BLOCKED for private value confirmation | Sensitive Production VITE_API_URL exists; exact value unavailable from connector. Local artifact explicitly targets https://trucksetu-api-nine.vercel.app/api/v1. Owner confirmation requested separately. |
| Fresh backup/restore readiness | BLOCKED | PostgreSQL18; PITR6hours; no automatic snapshot schedule. Only snapshot snap-little-tree-ax4fn88h from2026-10-26T02:17:08Z. New snapshot/export/isolated restore/resources unperformed and require separate authorization. Local rehearsals used PostgreSQL16, not a fresh production PG18 restore. |
| Production release and functional checks | BLOCKED / unperformed | No migration, staging, promotion, configuration change, repair or email. Local packages are not Vercel deployment outputs. |

Current observed production frontend: dpl_APPh8etW4m7yRoC4zDSyjtkWeExi. Latest observed API alias: dpl_Ap8PFvvqmfxiwhkrfZZgLhLUupRu, created2026-10-29T10:28:05.134Z, source redeploy/main. Both still ccd594df8a78f56041876c058b522e0624db4fb6. The API observation supersedes the earlier recorded dpl_7pdmUXDmaY9bjQZFRxbPX8n3wyGe; it is not the reviewed release and was not created by this task.

## Backup preparation requiring separate approval

On morning-forest-29164100, verify original br-polished-surf-axulzu38 / ep-fragrant-surf-axkjz078 / neondb and schema20261014_22. Approve a fresh named manual snapshot of that branch and record ID/time/expiry; preserve the existing incident snapshot. Agree operator, IST window, RPO/RTO, private backup destination/key custody before any logical export. No plan/protection/retention upgrade is included; stop on plan refusal.

For an approved isolated restore: restore the exact new snapshot to a NEW distinctly named branch, explicitly finalize:false, omitting target_branch_id. NEVER finalize_branch_restore. Verify all original endpoint/default/primary bindings before proceeding. A new bounded0.25CU compute needs explicit separate scope; read-only validation requires no writes, while migration rehearsal requires write permission ONLY on that isolated copy. Never reuse/move an existing endpoint. Compare schema, constraints and bounded aggregate business/audit/financial invariants without exposing personal records. Record restore duration and achievable RPO/RTO; suspend only the newly approved compute even on failure. Preserve the restored copy until explicitly authorized otherwise. Any live restore/cutover/replay requires new approval.

## Proposed production execution — not authorized

1. Require green exact-source CI, approved target-platform builds, private configuration/project-root/runtime binding confirmation, fresh recovery point and restore proof, operator/window/RPO/RTO. Preserve paid checkout, sandbox checkout, tax/test/bootstrap and KYC/scanner gates in their reviewed safe states. This is a limited release, not acceptance of paid-launch/privacy/scanner gates.
2. Apply reviewed maintenance/write control and preserve webhook retention/retry handling. Recheck original DB identity/current22, alias IDs and current financial work. Stop on drift.
3. From exact frozen source backend and approved direct migration identity: `python -m alembic -c alembic.ini current`, require20261014_22; run ONCE `python -m alembic -c alembic.ini upgrade 20261025_29`; require current/head29. Never use floating upgrade head, stamp or blind retries.
4. Migration chain: 20261014_23 KYC version pins/reverification; 20261014_24 shared acceptance/snapshots; 20261021_25 customer demand/drafts/selections/events; 20261023_26 customer KYC; 20261023_27 connection-fee history/refunds/credits; 20261023_28 sandbox refund metadata/idempotency; 20261025_29 private demand locations. Migration23 changes eligibility and audits existing records. All downgrades23–29 refuse destructive rollback.
5. Build/stage API on trucksetu-api from approved SHA, record immutable Vercel deployment ID/source/config, validate protected staged access, then promote API under write control. New API requires29. Check /health/live, /health/ready, /version exact SHA plus separately queried actual schema/binding; readiness SELECT1 alone does not establish schema compatibility.
6. Stage/promote matching frontend on trucksetu-whri from same SHA/public build configuration. Record its Vercel ID. Verify canonical https://www.transivox.in, API origin, auth/CORS/cookies and disabled capabilities before reopening approved traffic. Old main redeploy must not substitute for source selection.
7. Verify Maps/Places search, selection, pin placement and fallback on www, with real restricted browser key. No claim of provider functionality from variable presence or simulated CI.
8. Email remains separately gated: existing authorization covers password reset only, dedicated-test-account status unconfirmed; registration verification/resend need separate authorization. Use real application routes and bounded smoke test only after approval. Owner privately confirms receipt, production link behavior and authentication; never log codes/tokens/full links. API/provider acceptance is separate evidence.

Rollback: do not downgrade23–29 or assume old API compatibility with29. Hold writes on failure, preserve webhook/financial/audit history, prefer reviewed forward fix. Frontend rollback requires compatible API/schema. Database restore/endpoint cutover/replay needs a separate explicit data-loss decision. No automatic snapshot finalization, endpoint movement or data repair.

## Artifact rerun and identification

Run `C:\Users\harsh\OneDrive\Documents\ChatGPT\truck\release-prep-fa259574\.venv\Scripts\python.exe C:\Users\harsh\OneDrive\Documents\ChatGPT\truck\release-final-634b41df\package_final.py` to revalidate/repackage the already built exact-commit files and regenerate sanitized hashes. Fresh frontend builds require the same private-injected public Maps configuration; never copy backend secrets into frontend assets. GitHub CI links and artifact IDs will be appended when browser CI finishes.

Target Vercel deployment IDs: unavailable until separately authorized staging/deployment. Source/build ZIPs, backend wheel and GitHub test-report artifacts have distinct identities and must not be presented as deployed artifacts.

## Completed hosted CI provenance and reports

GitHub PR checks identify head634b41df258fa74e0e900643cc202896b3e146d3. Actions checkout uses PR merge4deae52d3ffe335dfd1e005c7fd6db281fe157b1 (candidate into unchanged main ccd594d). Browser checkout log confirms that SHA. A fresh fetch and tree comparison proves both merge and frozen candidate have identical complete source tree f301e936c0a38362913ef51989e368bb4581e170; no different source was tested. This is source-tree equivalence evidence, not a claim the checkout SHA itself was634b41df.

- CI https://github.com/HARSH3330/trucksetu/actions/runs/40858565724 : backend job123395665692, frontend123395664960, containers123396677361, all success; no uploaded deployment artifact.
- Browser https://github.com/HARSH3330/trucksetu/actions/runs/40858565740 : job123395664593 success, all test stages executed.
- Report artifact12890308105, playwright-kyc-report, digest sha256:06ddfb0cbc27ee9c466438c2e3584f229538879fb5dc8d58f742c8d03187d842.
- Report artifact12890756857, playwright-customer-release-reports, digest sha256:81a09ed7d5cd2ee2c16f53a12ce33b596769a3fdfc56cf6723bca0836dcda02e.
- Both reports bind workflow head634b41df and expire2026-11-12; they are test reports, not deployment bundles.
- Sourcery skipped its review because the full PR has306files, exceeding its300file API limit. The scoped independent review described in the candidate record was completed; no automated full-PR review is claimed.

## Remaining-gate refresh — 29 October 2026 IST

No completed audit was rerun. Fresh checks were limited to the still-open gates. Production remains at `20261014_22`. The original branch `br-polished-surf-axulzu38` remains primary/default with endpoint `ep-fragrant-surf-axkjz078`. PostgreSQL is version18 with six hours of retained history; the production branch has no automatic snapshot schedule and the only manual snapshot remains `snap-little-tree-ax4fn88h` from 26October. This proves the restore inputs are identifiable, but does not provide a fresh release recovery point or a tested restore.

The frontend Production Maps entries are readable through the provider API and have the expected browser-key and non-demo Map ID shapes. The owner separately confirmed the Google restrictions, APIs, owned Map ID and billing. `PUBLIC_FRONTEND_URL` is exactly `https://www.transivox.in`. Vercel returns no plaintext for Production `VITE_API_URL`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `EMAIL_FROM`, `DATABASE_URL` or `MIGRATION_DATABASE_URL`; their presence cannot be promoted to value correctness. Only the owner's actual Google response has been received. SMTP, API-origin and database-binding private confirmations therefore remain open.

Both Vercel projects build from the repository root: `trucksetu-api` uses root `pyproject.toml` with entrypoint `backend.app.vercel:app`; `trucksetu-whri` uses the root Vite application. The private setting entry locations are the Production environment-variable pages of those exact projects. Production `ENABLE_REAL_CONNECTION_CHECKOUT`, `ENABLE_RAZORPAY_SANDBOX` and `CONNECTION_FEE_TAX_CONFIRMED` are all `false`, so the release does not enable paid connection checkout, sandbox payments or unapproved tax handling.

The production approval can be consolidated only if it is conditional: first create a fresh snapshot and prove an isolated restore with `finalize:false`; proceed to migration and staged deployments only if those checks pass. The approval must name the operator, IST window, RPO and RTO, and authorize the new snapshot, isolated restored branch and one bounded0.25CU compute. A plan upgrade, endpoint rebind, restore finalization, data repair, email send or feature-gate expansion is outside that approval.

## Approved recovery execution stopped at provider limit — 29 October 2026 IST

The owner authorized up to two fresh snapshots, one isolated `finalize:false` restore, one bounded0.25CU compute, restore validation, migration rehearsal and the conditional production sequence. Before mutation, the original production branch/endpoint identity passed and proposed resource names had no conflict. Neon rejected the first fresh snapshot with HTTP422 `snapshots limit exceeded` because the preserved26October snapshot consumes the project's available snapshot slot.

No fallback branch, restore, compute, migration, deployment, configuration change or email was attempted. Fresh post-failure metadata confirms exactly one snapshot (`snap-little-tree-ax4fn88h`), six branches, six endpoints, no newly named resource, and the original production branch remains primary/default with its original endpoint. The preserved snapshot was not deleted. Continuing now requires a material plan change: a plan upgrade/additional snapshot capacity, or explicit acceptance of a normal copy-on-write branch plus encrypted logical backup in place of a fresh provider snapshot. The latter is weaker than the reviewed snapshot gate.

The frozen backend has no maintenance-mode or write-freeze middleware across its95 mutating routes. Its Celery beat configuration can write expired-capacity releases every60seconds when a worker is running, and payment/connection webhooks can write audit and state records. A safe production freeze therefore requires either a new reviewed maintenance control and fresh commit/CI, or an explicitly approved full backend traffic pause plus confirmed shutdown of every Celery worker/beat and a database-session check before migration. On any partway stop, backend traffic and writers must remain held; webhook retries must be preserved; no old API may resume against schema29; recovery requires a forward fix or a separately approved restore/cutover decision.
