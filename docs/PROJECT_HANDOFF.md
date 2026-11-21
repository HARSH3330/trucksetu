# Transivox handoff — 26 October 2026 IST

**Objective:** Prepare the customer-first marketplace, Maps, Brevo email and ₹99-total connection fee for a coordinated release. Production publication/live checkout remain gated.

**Git:** HARSH3330/trucksetu; branch `release/customer-first-20261026`; pushed commit `fa2595741d261cf15d2c0849b13e446d1eaffd20`; [draft PR1](https://github.com/HARSH3330/trucksetu/pull/1). Working tree was clean before this update; only this handoff is now uncommitted. Prior handoff history is preserved in that commit.

**Verified scope:** Recorded CI at1099527:430 backend unit,72 isolated PostgreSQL and54 frontend tests PASS; lint/types/build/containers PASS. At d4efac5,8 legacy/session/shared/vehicle browser checks and6 customer/fee/session checks PASS;2 KYC-policy assertions FAIL(status versus alert). Corrected in fa25957; its CI/browser workflows are currently RUNNING, not PASS. Later dedicated suites were skipped on the previous failure. Scanning/payment fixtures remain simulations where documented.

Preview production-credential sharing removed without replacing production secrets; separate preview database migrated29, restricted runtime role, compute disabled. Brevo relay/requested sender active; prior local STARTTLS/auth/email evidence retained. Production frontend URL and false payment/tax safety gates prepared, not deployed. GET-only Test reconciliation found yesterday’s ₹1,200 capture, no refunds, and failed refund checkout; fresh ₹99 orders have no payments. No completed ₹99 refund claimed.

**Critical incident:** Snapshot restore finalized unexpectedly, moving the production endpoint/default to the restored copy before23–29 ran. Original endpoint/name/default restored to original revision22; readiness200. Approximate exposure07:47–08:06IST; intervening writes remain unreconciled. Preserve every incident copy. No new application deployment occurred; do not claim production was untouched.

**Blockers:** Incident reconciliation; AWS scanner access/onboarding; approved KYC consent/retention; production Maps key/owned MapID; applicable tax/waiver accounting; ₹99 sandbox capture/reveal/refund.18% is research only. Neon Free lacks protected branches; deleting old backups cannot enable protection. No upgrade/deletion performed.

**Approval boundaries:** Authorized safe feature-branch pushes, isolated preparation and synthetic Test payments/refunds only. No merge, production deployment/migration, live payments, DNS, paid activation or real messages. Further incident endpoint/data cleanup requires reviewed approval; automatic review rejected an extra endpoint move as disruption risk. OTP deferred.

**Reports:** `docs/operations/2026-10-26-{production-integration-settings,recovery-isolation-incident,release-isolation,coordinated-production-release,kyc-consent-draft}.md`; `docs/testing/2026-10-26-coordinated-release-verification.md`; `docs/testing/2026-10-25-coordinated-release-manifest.json`.

**Next:** Check fa25957 CI diagnostics; resolve local failures without bypasses. Obtain incident follow-up approval, reconcile writes read-only, then complete isolated ₹99 testing and missing configuration. Present the exact release for final approval; do not deploy.

## Production email gate check — 26 October 2026 IST

Scope: production email only. Existing release/local Brevo evidence reused; no full audit repeated.

| Check | Status | Evidence |
|---|---|---|
| Checkout matches handoff | PASS | Read AGENTS.md and this handoff first. Branch release/customer-first-20261026; HEAD fa2595741d261cf15d2c0849b13e446d1eaffd20. Initial git status: only docs/PROJECT_HANDOFF.md modified, matching the handoff. Existing text preserved. |
| Recovery incident resolved | BLOCKED | operations/2026-10-26-recovery-isolation-incident.md still states RELEASE BLOCKED and possible intervening writes NOT reconciled. This handoff also lists incident reconciliation as unresolved. No closure evidence found in the reviewed release records; no database inspection/mutation performed. |
| Coordinated frontend/backend release deployed | BLOCKED | Fresh authenticated Vercel deployment lookups by serving aliases: www.transivox.in -> dpl_FExE8Kd4d9uFR29nAgsLHmUUpoB8; trucksetu-api-nine.vercel.app -> dpl_BycVRnLKUmjYfcKXMbkwrVesGYqj. Both READY Production at ccd594df8a78f56041876c058b522e0624db4fb6 on main, matching the documented old baseline, not candidate fa259574. READY is provider metadata, not proof of email operation. |
| Dedicated production test recipient | BLOCKED | Owner supplied an actual address in chat and explicitly authorized password reset ONLY. Address omitted here. Dedicated-test-account status remains unconfirmed; never reset an existing customer. Registration/verification/resend recipient authorization remains missing. Placeholder must never be used. |
| Registration, verification and resend/cooldown | BLOCKED | Not performed: prerequisites above uncleared; zero production email-flow requests/sends. |
| Password reset, token reuse rejection and old-session invalidation | BLOCKED | Not performed; no account reset or session mutation. Never target an existing customer. |
| Production verification/reset link origin and successful links | BLOCKED | No new production messages obtained; https://www.transivox.in is the required origin, not a verified result. No tokens, codes or full message links collected or stored. |
| Provider delivery evidence | BLOCKED | No production sends attempted. Prior local Brevo acceptance remains local evidence only. |
| Owner-confirmed inbox receipt and message authentication | BLOCKED | No new production receipt/authentication evidence. Historical owner confirmation for one unspecified local-test mailbox does not establish production receipt. No inbox access available in this task; request owner receipt/Inbox-or-Spam and SPF/DKIM/DMARC statuses after authorized sends. |

Next email action: require documented recovery reconciliation/closure, confirm the coordinated serving frontend/backend deployments and exact release SHA, and confirm the supplied reset-only address belongs to a dedicated test account; obtain separate recipient authorization for registration/verification/resend. Only then exercise the deployed application's source-confirmed email endpoints with bounded requests/sends and private code/token entry. Record API acceptance, provider evidence and owner-confirmed receipt separately. No deploy, configuration change, merge, migration, endpoint move, Maps/Razorpay action, real email or production account mutation occurred in this check. Recovery remains a separate unresolved blocker.
## Owner redeployment recheck — 26 October 2026 IST

Owner reported redeploying both projects after changing environment values. Fresh authenticated Vercel lookups by serving alias confirm:

| Check | Status | Evidence |
|---|---|---|
| Frontend redeployment serving | PASS | www.transivox.in now resolves to dpl_APPh8etW4m7yRoC4zDSyjtkWeExi, READY Production. This supersedes the earlier serving-deployment observation. |
| Backend redeployment serving | PASS | trucksetu-api-nine.vercel.app now resolves to dpl_7pdmUXDmaY9bjQZFRxbPX8n3wyGe, READY Production. This supersedes the earlier serving-deployment observation. |
| Coordinated release candidate serving | BLOCKED | BOTH new deployments still identify main commit ccd594df8a78f56041876c058b522e0624db4fb6, not release/customer-first-20261026 candidate fa2595741d261cf15d2c0849b13e446d1eaffd20. Redeploying the old source does not deploy the candidate email implementation. |
| Recovery incident clearance | BLOCKED | Handoff and incident report continue to mark intervening writes unreconciled. No closure evidence supplied or found in those records; no database operation performed. |
| Production email delivery, mailbox receipt and verification/reset links | BLOCKED | Not performed: release/recovery prerequisites remain uncleared. READY provider metadata does not prove updated environment correctness, application health or email delivery. No email requests/sends or account/session mutations attempted. Reset-only recipient authorization retained; dedicated-test-account status remains unconfirmed. |

Checkout rechecked: release/customer-first-20261026 at fa2595741d261cf15d2c0849b13e446d1eaffd20; only this pre-existing modified handoff changed. No deploy, merge, migration, endpoint movement or cloud configuration change was performed by this task. No credentials were printed or stored. Existing historical records above retained as dated evidence.
## Coordinated release preparation — 27 October 2026 IST

Decision: **Production execution BLOCKED.** Detailed evidence, exact artifact digests, migration/deployment proposal, recovery limitations and post-release matrix: [release preparation](operations/2026-10-27-coordinated-release-preparation.md), [artifact manifest](operations/2026-10-27-coordinated-release-artifacts.json).

| Check | Status | Evidence |
|---|---|---|
| Checkout/preservation | PASS | release/customer-first-20261026 at fa2595741d261cf15d2c0849b13e446d1eaffd20; initially only this handoff modified. Existing text preserved. No commit/push/merge. |
| Recovery identities/current schema | PASS | Explicit read-only queries confirm original br-polished-surf-axulzu38 / ep-fragrant-surf-axkjz078 / neondb at 20261014_22. Holding copy br-misty-recipe-ax4djqgq / ep-wandering-credit-axfl5bss also 22; all 49 compared application-table counts/full-row fingerprints equal; no observed incident-window timestamps in either. Fingerprints/records omitted. This is limited evidence, not incident closure. |
| Recovery reconciliation | BLOCKED | Preserved incident copy br-young-wind-axoimpov has no attached queryable endpoint. It was not compared at row level. Incident 26 October 07:47:21–08:06:15 IST; provider operations corroborate endpoint activity on the recovery branch. Database log queries returned no records; Vercel explicitly refused the old window due retention. Lost/duplicated/stranded writes remain unestablished. All copies/snapshot preserved; no cloud resource mutation or production data write. |
| Production Maps configuration | PASS for shape/presence; functional acceptance BLOCKED | Both VITE_GOOGLE_MAPS_BROWSER_KEY and VITE_GOOGLE_MAPS_MAP_ID present on frontend trucksetu-whri Production-only; nonempty, expected key shape, non-demo Map ID. Ownership, API/referrer restrictions/billing and actual production Maps/Places still unverified. No value printed. |
| Production Brevo configuration | PASS for presence/sender/URL; correctness/delivery BLOCKED | Required SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, EMAIL_FROM exist on backend trucksetu-api Production-only. Sensitive values unavailable for correctness comparison. Optional EMAIL_REPLY_TO absent, not required. PUBLIC_FRONTEND_URL exactly https://www.transivox.in; intended noreply sender active in Brevo. No real messages sent. |
| Serving deployments | PASS for observation; candidate deployment BLOCKED | Fresh alias lookup still READY Production source=redeploy, main ccd594df8a78f56041876c058b522e0624db4fb6: frontend dpl_APPh8etW4m7yRoC4zDSyjtkWeExi; API dpl_7pdmUXDmaY9bjQZFRxbPX8n3wyGe. Redeploy reused old source; exact release-branch Git deployment guards retained. |
| Local verification | PASS | 430 backend unit tests; 54 frontend tests; Ruff/domain mypy; frontend build; offline linear head29 SQL. Started installed Docker normally and ONLY existing dedicated test container/volume. Exact loopback/database/restricted-role checks passed; four real migration regressions in disposable synthetic schemas passed. Two desktop/mobile customer-review browsers and final one management browser passed in scoped runs, preserving existing local rows. Five simulated Maps and two simulated email-link browser checks passed. No production or external provider calls. |
| Candidate browser CI at fa259574 | FAIL (historical actual result) | Backend/frontend/container CI success reused; browser job 121596829384 failed three customer-review cases. New local corrections have not been committed/pushed or run in hosted CI; local passes do not relabel that job green. |
| Necessary local corrections | PASS locally; final source commit BLOCKED | Fixed implicit-label test lookups, generated Maps harness CI setup, bid-editor Escape focus restoration, and provider Active trips navigation to existing trip operations; test waits for confirmed assignment and reloads after same-hash/API-only fixture creation. Four changed code/test/workflow paths plus documentation. No backend payment/authorization rule changed. Final Git SHA requires separately authorized commit/review/hosted CI; do not deploy dirty source. |
| Artifacts | PASS for local integrity; deployment readiness BLOCKED | Exact fa259574 base archive/backend wheel/backend-source/frontend baseline retained. Corrected frontend/source archives have base-SHA-plus-uncommitted-patch provenance and SHA-256s in manifest. Verified 64 backend Python files equal base source, all artifact hashes, frontend entry/API origin and corrected source changed-path set. No staged Vercel deployment outputs/IDs; no final corrected commit fabricated. |
| Migration/recovery preparation | PASS for inspected plan; execution BLOCKED | Observed current22 -> target20261025_29; inspected23–29. New API requires29. All downgrades refuse destructive rollback. Fresh protected backup/isolated restore proof, runtime binding, operator/window/RPO/RTO and old-code/new-schema rollback acceptance remain missing; paid/scanner/privacy/tax/99-INR real-payment gates from reviewed plan remain open. No production migration/deployment/configuration action. |
| Production email/inbox/link acceptance | BLOCKED | No production request/send/reset performed. Existing authorization covers password reset only; dedicated-test-account status unconfirmed. Signup/verification/resend need separate recipient authorization. Mailbox receipt/authentication and actual working production links must be confirmed privately with owner after release; provider acceptance alone insufficient. |

Exact next action requiring approval: ONE separate 0.25-CU read_only compute on preserved recovery copy br-young-wind-axoimpov in morning-forest-29164100, for bounded read-only comparison, then suspend only that new compute. Never move/rebind original endpoints, finalize restore, alter default/primary, repair/delete data or upgrade plan. Stop if plan refuses read-only compute. Normal compute usage may apply; an owner-provided private export is an alternative. Obtain any archived incident request/audit/WAL evidence. Approval for evidence access does NOT authorize production migration/deployment or email. After recovery closure, final reviewed commit/green hosted CI, private configuration acceptance and fresh recovery readiness, present the exact 22-to-29/API-before-frontend execution approval from the linked package.
## Approved read-only incident reconciliation — 29 October 2026 IST

Latest findings supersede the 27 October recovery-copy-access blocker. [Detailed report](operations/2026-10-29-incident-reconciliation.md), [sanitized evidence](operations/2026-10-29-incident-reconciliation-evidence.json); release package/manifest and original incident record updated. Historical observations and pre-existing working-tree changes preserved.

| Check | Status | Evidence |
|---|---|---|
| Recovery identity before creation | PASS | Project morning-forest-29164100; exact branch br-young-wind-axoimpov, name recovery-rehearsal-20261026-not-preview, finalized restore from snap-little-tree-ax4fn88h, neither primary nor default, no pre-existing endpoint. Original endpoint still on original primary/default branch. |
| Approved resource | PASS | Created only ep-morning-sunset-axii59da, read_only, min/max0.25CU, bound only to recovery. Verified binding/type/size before SQL and pg_is_in_recovery=true. No rebind, data modification, copy deletion, plan upgrade, production migration, deployment or email. |
| Read-only comparison coverage | PASS | Explicit read-only transactions on original22, holding22 and recovery29. 49 common application tables; stable primary keys on all; every original application column covered. Limit1000rows/table plus sentinel, no truncation. No extra recovery columns on populated tables; all seven recovery-only schema tables empty. Hashes compared only in memory; no row identifiers/values/credentials/personal data in report. |
| Retained-state reconciliation | PASS | All49 common tables in recovery match holding. No surviving recovery-only records absent from original, changed business records, duplicate identity groups or observed incident-window timestamps. Original has two additional refresh sessions and one changed last_login_at; targeted read-only aggregate follow-up proves ALL are after the incident. No data repair indicated by these retained-state findings. |
| Historical zero-write/no-loss assurance | BLOCKED / owner review | Comparisons cannot reconstruct deleted/overwritten/transient writes or missing client acknowledgements. Earlier log investigation found no branch records and Vercel window outside retention; no archived request/audit/WAL history supplied. Do not claim proof that no writes ever occurred or automatically close incident without reviewing residual uncertainty. |
| New endpoint final state | PASS | Suspended in finally block even if checks failed. Final metadata confirms idle, compute idle/read_only, suspended_at2026-10-29T08:51:31Z (14:21:31IST); recovery binding and0.25CU limits retained. No SQL against it after suspension. Only this new endpoint explicitly suspended. |
| Existing infrastructure preserved | PASS | All five pre-existing endpoint/branch bindings unchanged; original branch remains primary/default. Exactly one new endpoint, retained suspended. All incident copies/snapshot preserved. |
| Continued safe release preparation | PASS for artifact integrity; production BLOCKED | Fresh hash/source validation passed; existing27October tests reused without full audit. HEAD still fa259574 on release/customer-first-20261026, uncommitted correction patch f070e9d32a4740cbcfd0cdbd5bb8921be1133f967e57e16d5cf9f69b81976440 unchanged. No commit/push/merge. Fresh serving aliases still old main ccd594d, same READY redeploy IDs. Production22 -> candidate29 remains required. |

Exact next action: owner review of retained-state PASS and the documented historical evidence gap; provide archived incident history if a stronger conclusion is required, or explicitly accept residual uncertainty for incident closure. No data repair is proposed. Separately authorize commit/push of preserved corrections if desired; final reviewed SHA/green exact-head CI, private settings/binding confirmation, fresh protected backup/isolated restore readiness and operator/window/RPO/RTO remain required before a separate concrete production execution request. Existing approval for this ONE completed read-only endpoint does not authorize another endpoint, data repairs, production migration/deployment or emails. Reset-only recipient authorization remains unchanged; confirm dedicated-test-account status before any future email test.

## Final candidate preparation authorized — 29 October 2026

Owner accepts the documented incident findings and historical-evidence limits; incident SIGNED OFF FOR RELEASE PREPARATION, without absolute no-loss proof. Preserve copies/snapshot; no repairs authorized. Reviewed scope: provider bid focus restoration/trip navigation, test locator and synchronization corrections, and simulated Maps CI build setup. Independent focused review found the need for synthetic VITE values AT BUILD TIME; corrected and CI-equivalent Maps build plus five browser tests passed. Other code checks from 26–27 October reused; exact-final-commit hosted CI must be fresh.

Push preflight: canonical remote release ref equals fa259574; remote and local root/backend vercel.json both explicitly disable deploymentEnabled for release/customer-first-20261026, with no overlapping true pattern or alternate vercel.ts found. Both connected projects have zero deployments for that branch. Actions contain no deployment job; production migration is workflow_dispatch only. Push only this branch, never main/merge; verify no deployments after push. No production settings changed. The final commit identity and CI/artifact attestation will be recorded by exact SHA after commit; avoid a self-referential tracked commit hash.

Google Cloud restrictions, APIs, owned JavaScript Map ID and existing billing confirmed privately by owner; this is owner evidence, not a real Maps functional test. Backend sensitive SMTP values remain pending private owner confirmation, never print them. Fresh backup checks: original project PostgreSQL18, PITR history21600seconds (6hours), empty automatic snapshot schedule. Retained incident snapshot is dated26October and unprotected; no fresh release backup/restore is claimed. Backup creation/export/destination/isolated restore/protection or paid changes need separate authorization.

Reviewed commit/push and CI are now authorized preparation only. Migration22->29, API deployment, frontend deployment, data repairs and email remain outside authorization. See release-candidate record and generated exact-SHA attestation for final evidence.


## Frozen reviewed release and completed CI — 29 October 2026

This latest status supersedes dated final-commit/CI/incident-owner-review blockers above. Source frozen at **634b41df258fa74e0e900643cc202896b3e146d3**, release/customer-first-20261026, normal authorized push to PR1; no merge. Clean source checkout after commit. The post-CI attestation documents are intentionally separate documentation-only working-tree updates and are not substituted for the frozen source at deployment. [Final attestation](operations/2026-10-29-final-release-attestation.md), [exact-SHA artifact manifest](operations/2026-10-29-final-release-artifacts.json).

| Check | Result | Evidence |
|---|---|---|
| Incident sign-off for preparation | PASS | Owner accepts retained-state findings/historical limitation; no repair indicated. Absolute historical zero-loss proof remains unavailable. Copies/snapshot preserved. |
| Commit/push safeguards | PASS | Eleven reviewed paths committed. Root/backend guards disable this branch; both Vercel projects still zero release-branch deployments after push. No main push, merge or deployment. |
| Hosted CI | PASS | Runs40858565724 and40858565740; backend430unit/72integration, frontend/build, containers and all browser stages success. PR merge4deae52d checkout tree exactly equals frozen candidate tree f301e936c0a38362913ef51989e368bb4581e170. No skipped Maps/email stage. Sourcery skipped full review due306files; independent scoped review completed. |
| Exact-source artifact integrity | PASS | Git source ZIP, backend source ZIP, frontend bundle and wheel hashed in new manifest; all64 wheel Python files equal source. Existing public Production Maps values used; explicit production API build origin. Test reports12890308105 and12890756857 bind same head. No Vercel target deployment IDs yet; staging remains unauthorized. |
| Maps private settings | PASS for configuration evidence | Owner privately confirms referrer/API restrictions, owned JavaScript Map ID and billing. Frontend Production variables present. Real Maps/Places unperformed. |
| Brevo private settings | BLOCKED for sensitive correctness | Required five backend Production entries present; exact www PUBLIC_FRONTEND_URL and active sender evidence retained. SMTP host/port/login/production key/sender confirmation pending; no secrets printed. Delivery/mailbox/authentication unperformed. |
| Frontend API setting | BLOCKED for sensitive correctness | Production VITE_API_URL present, value unreadable by connector. Owner asked to confirm exact production API origin privately; local artifact explicitly uses intended origin. |
| Backup/restore readiness | BLOCKED | Fresh metadata: PG18,6hour PITR, automatic snapshot schedule empty, only retained26October snapshot. Fresh snapshot/isolated restore/export/compute/protection not performed; additional authorization needed. Operator/window/RPO/RTO pending. Restore procedure and no-finalization safeguard in final attestation. |
| Recovery endpoint final state | PASS | Fresh endpoint metadata still idle/read_only/min=max0.25CU, suspended_at2026-10-29T08:51:31Z, correct recovery binding. Existing bindings preserved. |
| Production execution/acceptance | BLOCKED / not performed | Production last observed22, proposed29. Latest API alias now dpl_Ap8PFvvqmfxiwhkrfZZgLhLUupRu (29October10:28:05UTC redeploy/main ccd594d); frontend still dpl_APPh8etW4m7yRoC4zDSyjtkWeExi on ccd594d. No migration, deployment, configuration change, data repair or email by this preparation. |

Exact next action: private SMTP/API URL confirmation plus maintenance operator/window/RPO/RTO. Separately approve a fresh original-branch snapshot and bounded isolated restore validation/resources (explicit finalize:false; never finalize or move existing endpoints); no plan upgrade included. Then review exact source/artifacts and fresh recovery evidence for a separate production execution approval: maintenance/write hold -> one explicit Alembic20261014_22-to-20261025_29 upgrade -> compatible API -> matching frontend -> alias/version/actual-schema/health/real Maps checks. All23–29 downgrades refuse; old API/new29 rollback unapproved; prefer forward fix. Any restore/cutover/replay needs its own approval. Email stays separate: password-reset-only recipient authorization, dedicated-account status unconfirmed; verification/resend not authorized, actual receipt/production links to be privately confirmed by owner.

## Remaining production gates — 29 October 2026 IST

The owner again accepts the incident findings and historical uncertainty; retained-state comparison indicates no repair. Final source `634b41df258fa74e0e900643cc202896b3e146d3`, CI, scoped review and local artifact integrity remain complete and were not rerun.

Fresh checks of only the open gates confirm production schema `20261014_22`, original primary/default branch and endpoint identities, PostgreSQL18, six-hour history and no automatic snapshot schedule. The sole manual snapshot is still the preserved26October incident snapshot. Backup identity/procedure is prepared; a fresh snapshot and isolated restore proof have not been authorized or performed.

The only owner private configuration response received confirms Google restrictions, APIs, owned Map ID and billing. Maps values have valid provider-readable shapes. Backend `PUBLIC_FRONTEND_URL` is exact. Sensitive Vercel values are write-only through this connection, so SMTP values, frontend API origin, and runtime/direct database endpoint bindings remain pending owner status-only confirmation. Backend private entry location: team `harsh3330s-projects` -> project `trucksetu-api` (`prj_gXnKmzBiPf8TpQ5MJmZLQPg04diF`) -> Settings -> Environment Variables -> Production. Frontend location is the same team -> `trucksetu-whri` (`prj_3TQcT6qyOPBQlAguSubP2OJ5xe7w`) -> Settings -> Environment Variables -> Production. Both deploy from repository root; backend entrypoint is `backend.app.vercel:app`.

One conditional approval can cover fresh snapshot/isolated restore, migration22-to-29, staged backend and staged frontend: every later phase stops if the preceding phase fails. Still required from the owner: private value confirmations; operator and maintenance window in IST; acceptable RPO/RTO; and explicit authorization for the fresh snapshot, new isolated restored branch, bounded0.25CU compute, one production migration, two staged Production deployments and their promotions after checks. No plan upgrade, endpoint rebind/finalize, data repair, feature-gate expansion or email is included.

## Recovery execution stop — 29 October 2026 IST

Owner confirmation closed the private configuration response gate and authorized the conditional recovery/migration/deployment sequence, but supplied placeholders rather than an actual maintenance window or encrypted backup destination. Safe preparation proceeded only to the provider recovery boundary.

Preflight reconfirmed `br-polished-surf-axulzu38` as production primary/default and `ep-fragrant-surf-axkjz078` bound to it, with no proposed-name conflict. Creation of the first authorized fresh snapshot failed HTTP422 `snapshots limit exceeded`. The retained26October snapshot occupies the only available slot. Post-failure verification: exactly one snapshot, six branches, six endpoints, zero new snapshot/restore branch/compute; original bindings unchanged. No incident evidence was deleted. No restore, migration, deployment, configuration change or email occurred.

This is a material plan/cost change, so earlier approval cannot be stretched into a workaround. Choose either additional Neon snapshot capacity/plan upgrade, or explicitly approve the weaker normal production-child branch plus encrypted logical backup alternative and provide the real private destination. Deleting the preserved incident snapshot remains prohibited.

Application-write freeze also remains a production gate. Frozen source634b41df has no maintenance middleware across95 mutating routes. Celery beat can commit capacity-release writes every60seconds if deployed, and payment/connection webhooks can write state/audits. Before migration choose: (a) implement a reviewed maintenance control, producing a new commit and CI; or (b) approve a full backend traffic pause and require every worker/beat to be stopped plus an active-session check. If execution stops after schema migration, keep traffic/writers frozen and webhooks retryable; do not resume the old API on29, downgrade, or restore/cut over without separate approval.


## Admin panel audit and completion — 15 November 2026 IST

Branch `release/customer-first-20261026` at `19949f7` plus **uncommitted** changes from this work. Nothing committed, pushed, deployed or run against production. Local verification only, against the Docker test database `transivox-e2e-postgres` (port 55432).

### Audit

| # | Capability | Status | Evidence |
|---|---|---|---|
| 1 | Dashboard counts | Working and verified (extended) | `GET /admin/marketplace-health` counts customers, truck owners, drivers, trucks, KYC queues, requirements, bids, bookings, trips, disputes, paid connections. Added open connection-fee refunds, available/reserved fee credits and offline payments awaiting confirmation. Loading, forbidden and retry states exist. Tests: `test_admin_control_database`, `test_admin_console_database`, `LiveAdmin.test.tsx`. |
| 1 | Dashboard navigation | Fixed | "Open disputes" and the Disputes nav item opened the participant Trust centre, which cannot resolve anything. They now open the admin dispute queue. |
| 2 | Users: search, view, suspend/reactivate | Working and verified | Server-side search and pagination; masked phone; reason ≥10 chars; self and privileged accounts refused; suspension revokes refresh sessions and supply eligibility; audited (`test_admin_operations`, `test_admin_control_database`). |
| 2 | Users: role and status filters | Was missing, now added | `role` (allowlisted, 422 otherwise) and `account_status` filters in API and UI. Browser: Driver filter returned 31 driver-only rows. |
| 2 | Direct-API permission enforcement | Working and verified | Customer/provider tokens get 403 and unauthenticated calls get 401 on the new endpoints (integration tests; curl against the local API). |
| 3 | Provider/driver KYC review | Working; one gap fixed | Clean-scan gate before acceptance (`require_bound_clean_scan`), reasons, review events, 5-minute signed downloads with audit. **Fixed:** an admin could review their own provider application (customer KYC already refused this). Now 403. |
| 3 | Customer KYC review | Working and verified (existing tests) | Self-review refused, clean scan required, decision reasons audited. |
| 3 | Vehicle document review | Working | Clean-scan and expiry gates, audited. Self-review **not** blocked; see decisions. |
| 3 | KYC restrictions on publishing/bidding | Working | `require_customer_kyc` on publish/edit; provider and driver verification required for bids, selection and contact checkout. |
| 4 | Requirements list | Partially implemented | Search, TEST badge, bid count. No per-requirement drill-down into bids/selections in the console. |
| 4 | Bookings list | Was thin, now extended | Added status filter, truck owner(s), trip statuses, driver-assigned flag, open-dispute count and connection-fee state. No addresses, contacts or messages returned. |
| 4 | Admin actions follow the trip state machine | Working | Trip status changes go through `ensure_trip_transition`; no admin override endpoint exists. |
| 4 | Split awards / shared aggregation | Not in approved scope | Single winner per demand per the 21 Oct spec; shared-match review exists separately. |
| 5 | Connection fee separate from freight | Working and verified | Fee snapshot separate; freight settled directly; UI copy says so. |
| 5 | Orders, capture, refunds, payment events visible | Working | `/admin/connection-fees` lists selections, refund state and webhook outcomes (read-only). |
| 5 | Contact locked until payment + reveal; pre-reveal full refund; cancel blocks reveal; no refund after reveal; race protection; webhook idempotency; duplicate-payment guard | Working and verified (existing tests) | `test_connection_fee_policy_database` (5 cases), `test_demand_marketplace_database`, `test_sandbox_refund_database`. |
| 5 | Refund execution | Blocked by configuration | Executor is Razorpay Test Mode only; real refunds and `ENABLE_REAL_CONNECTION_CHECKOUT` stay off. |
| 5 | Tax configuration | Blocked by product decision | Fee policy tax is "pending confirmation"; no tax rule invented. |
| 6 | Provider-failure credit | Working and verified (existing tests) | Admin-only, reason required, independent of the customer, one credit per source selection (unique constraint plus row lock), reserved and redeemed atomically, "Platform connection fee waived" label. |
| 6 | Checkout block for unresolved waiver tax | Working (kept) | `/order` returns 503 while a credit is applied. |
| 6 | Credit expiry/transfer/refund rules | Blocked by product decision | Reported as "unresolved" by the API; nothing invented. |
| 7 | Disputes | **Was broken, now fixed** | Before: no admin list, resolve took an unbounded query string, wrote no audit event, and left the booking `disputed` forever (which also locks contact reveal). Now: `GET /admin/disputes` (status filter, pagination), `POST /admin/disputes/{id}/resolve` with a 10–2000 char JSON reason, row locks, 404/409, audit event with before/after, and the booking returns to its pre-dispute status when no other dispute is open. Raising a dispute is now audited too. Browser-verified end to end. |
| 7 | Safety reports | Missing | Reports are stored; no admin queue exists. Not built here (needs a small design: who sees reporter identity). |
| 7 | Cancellations | Working | Customer-demand cancellations go through the connection rules; legacy cancellations through the cancellation preview. |
| 7 | Audit log | Was API-only, now in the console | `/admin/audit-logs` now paged and filterable (action, entity type, entity id), returns actor name, masked actor email, reason and scalar before→after changes. Raw payloads are not returned. New "Audit log" tab. |
| 7 | Integration status | Not changed | Health/readiness endpoints exist; no credentials exposed. |
| 7 | Export / notifications | Not in approved scope | Spec excludes mass export; no admin notification requirement found. |
| 8 | No non-admin access / escalation | Working and verified | `require_roles` on every `/admin/*` route; role changes are not exposed in the console (spec's superadmin role endpoint was never built — see decisions). |
| 8 | Actor, time, reason, changes recorded | Working; dispute gap fixed | All admin mutations reviewed write audit or review events. |
| 8 | Confirmation for destructive/financial actions | Working | Reason fields, explicit confirm buttons, checkbox for refund records. |
| 8 | No false success | Working | Forms show the API error; success messages come from API responses. |
| 8 | No secrets in responses | Working | Lists omit password/token/OTP hashes; audit view drops raw payloads. |

### Changes

- `backend/app/api/operations.py`: dispute queue and resolve; paged audit log with reason/changes; user `role` filter; booking `status` filter and operational fields; dashboard refund/credit/offline-payment counts.
- `backend/app/api/trust.py`: dispute creation records the prior booking status and an audit event; old unaudited resolve removed (same path now served by operations).
- `backend/app/api/kyc.py`: admins cannot review their own provider application.
- `backend/app/models.py` + migration `20261120_33_dispute_booking_status.py`: nullable `disputes.booking_status_before`. Additive; downgrade drops the column.
- `src/components/AdminRecords.tsx/.css`: Disputes and Audit log tabs, role/status filters, richer booking rows, dispute resolve form.
- `src/components/LiveAdmin.tsx`: new counts, refund attention card, Disputes routing.
- Tests: `backend/tests/integration/test_admin_console_database.py` (new, 2 cases), `test_kyc_review_regression.py` (+1), `AdminRecords.test.tsx` (+4), `LiveAdmin.test.tsx` (+1). Each new test was seen failing before the fix.

### Verification

| Check | Result |
|---|---|
| Backend unit (`pytest tests --ignore=tests/integration`) | 483 passed, 1 failed: `test_settlement_snapshots` (already failing before this work). Two existing tests updated for this change: migration head/count now `20261120_33`/31; `test_kyc_versions` now uses a separate reviewer so it still tests the version gate rather than the new self-review refusal. |
| Backend integration (local PostgreSQL, `tests/integration`) | 83 passed, 2 failed: `test_financial_snapshots` (commission) and `test_request_creation_database`, both on the known pre-existing list. The two local email tests passed this run. New `test_admin_console_database` 2/2 passed. |
| Ruff (`app tests migrations`), mypy `app/domain.py` | Pass |
| Migrations | Single head `20261120_33`; full offline `upgrade head --sql` compiles; the new step emits only `ALTER TABLE disputes ADD COLUMN booking_status_before VARCHAR(30)`. Local test database upgraded 29→31. |
| Frontend `vitest run` | 47 files, 194 tests passed |
| Frontend `npm run build` | Pass |
| Browser (local API :18000 + Vite :5174, local test DB) | Signed in as a local-only test superadmin; control centre showed the seeded open dispute and an open connection-fee refund; "Open disputes" opened the queue; resolve form required a reason; resolving returned the booking to `booking confirmed` and emptied the queue; Audit log tab showed actor, reason and changes; Users role filter sent `role=driver` and listed drivers only; Bookings tab showed truck owner, trips, driver and fee state; no horizontal overflow at 375px. |
| Unauthorized API | Unauthenticated calls to the new endpoints returned 401 (curl); customer/provider tokens return 403 (integration tests). |
| Not verified | Hosted CI, Playwright browser suite, production or preview deployment, real Razorpay/refund behaviour, the legacy-dispute (NULL prior status) path in a browser. |

### Decisions needed

1. **Dispute outcome.** Resolving now returns the booking to its status before the dispute. If you want admins to be able to cancel or complete a booking as the outcome, that needs a rule (and possibly a refund policy for legacy bookings).
2. **Self-review of trucks.** Truck document review does not block an admin approving their own truck. Provider KYC now does. If the owner's superadmin account also owns trucks, decide whether a second reviewer is required.
3. **Provider KYC self-review block.** If the owner's superadmin account has its own provider application under review, it can no longer approve it. Revert the one line in `kyc.py` if that is not wanted.
4. **Superadmin role management** (`PUT /admin/users/{id}/roles` in the 7 Oct spec) was never built. Build only if you want role changes in the console.
5. **Safety-report queue**: decide whether admins should see reporter identity.
6. Unchanged blockers: connection-fee tax treatment, credit expiry/transfer rules, real Razorpay checkout and refunds.

### Release steps (not done)

Production needs migration `20261120_33` before the new API (additive, safe on the old API). Disputes raised before it have no recorded prior status; resolving one leaves the booking `disputed` and the API says so.

### Follow-ups noticed

- Local data shows bookings still `booking_confirmed` after every trip is `completed`; booking status may not advance with trip completion. Not investigated here.
- `ConnectionFeeReview` pages selections and events together (50 each), so "next" can be misleading.

## Exact pickup and drop for verified truck owners — 20 November 2026 IST

**Owner decision (20 Nov 2026):** every verified truck owner sees the exact pickup and delivery address, map pins and stop addresses before bidding. This reverses the 21 October design ("precise addresses excluded from public listings") and means a truck owner can find the pickup point without paying the connection fee. Uncommitted; not deployed.

| Who | Sees |
|---|---|
| Verified truck owner (active profile, KYC `verified`, account active) | Exact pickup/drop address, pickup/drop pins (with Google Maps links), stop addresses and activity — in Open loads, demand detail, and My bids. Phone numbers typed into an address are replaced with "[contact removed]". |
| Truck owner still under review | Cities, cargo, schedule and stop count only (unchanged). |
| Admin / superadmin | Full requirement via `GET /demands/{id}`, including special instructions. |
| Never shown to truck owners before payment | Customer name, phone, email, stop contact names, stop instructions, special instructions. |

Changes: `demand_view(..., exact_location=True)` in `services/demand_marketplace.py`; `sees_exact_location()` in `api/demands.py` used by `/demands`, `/demands/{id}`, `/demand-bids/mine`; new `src/components/DemandPins.tsx`. Customer wording updated in the demand form, stops editor and home page; privacy notice now discloses it and is bumped to `privacy-v5-20261120` (new signups record that version).

Migration renumbered: another session committed `20261120_32_load_road_distance` (also after `20261115_30`), so the dispute migration from 15 Nov is now `20261120_33_dispute_booking_status` after it. Single head `20261120_33`. The local test database was rolled back one step and upgraded through 32 and 33.

Verification: new `test_demand_location_sharing_database` seen failing on the old code, passing now; demand, stops, locations, milestone, connection-fee and admin integration files 36/36 after updating three tests that asserted the old privacy rule; backend unit 488 passed, 1 known failure (`test_settlement_snapshots`); frontend 49 files / 199 tests and build pass; ruff clean. Browser (local production build + local API): a verified test truck owner saw the exact addresses, both pin links (correct coordinates, new tab) and the stop address, not the stop contact name or instructions; no sideways scroll at 375px. Not verified: hosted CI, production.

Owner decision (20 Nov 2026): demands posted before this change also show their exact addresses to verified truck owners; no cut-off by posting date. Customers are not asked to tick a separate consent for address sharing; the privacy notice and form text disclose it. Legal review of the privacy wording is still needed before public launch.
