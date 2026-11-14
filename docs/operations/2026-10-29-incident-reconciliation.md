# Incident reconciliation — 29 October 2026 IST

**Retained-state reconciliation: PASS. Historical zero-write/no-loss guarantee: BLOCKED by incomplete history. Production release: still BLOCKED.** No data repair is indicated by the compared retained state.

This update supersedes the 27 October release package's recovery-copy-access blocker. It does not convert absent historical logs into proof that no incident writes ever occurred. Sanitized machine-readable evidence: [reconciliation evidence](2026-10-29-incident-reconciliation-evidence.json). No row identifiers, personal values, credential values, row/column fingerprints, message bodies or tokens are included in these files.

## Approved resource and safety verification

Before creation, fresh provider metadata confirmed project `morning-forest-29164100`, branch `br-young-wind-axoimpov`, exact name `recovery-rehearsal-20261026-not-preview`, restored from `snap-little-tree-ax4fn88h` with finalized restore status, neither primary nor default, and no attached compute. The snapshot's source is the original production branch. The original endpoint `ep-fragrant-surf-axkjz078` remained attached to original production branch `br-polished-surf-axulzu38`, which remained primary/default. All previous working-tree changes were preserved; branch/HEAD still match the handoff.

Created exactly ONE approved endpoint: **`ep-morning-sunset-axii59da`**, type **read_only**, bound only to the verified recovery branch, min/max **0.25 CU**. Verified its binding/type/size before SQL. The recovery server additionally reported `pg_is_in_recovery() = true`. No endpoint was rebound, no restore was finalized, no plan was upgraded and no incident copy/snapshot was deleted.

SQL used explicit READ ONLY transactions; the main comparisons also used REPEATABLE READ, UTC timezone and a 15-second statement timeout. Follow-up aggregate checks used READ ONLY with a five-second timeout. Every target was explicit: project, branch, compute and `neondb`. Credentials were resolved inside the connector and were never exported or printed. Row/column fingerprints were calculated server-side, compared only in memory and discarded after generating aggregate evidence.

Cleanup ran through a finally block. Only the newly created endpoint was explicitly suspended. Its final metadata, checked again after the aggregate follow-up, confirms:

- `current_state = idle`; its compute is also idle/read_only.
- `suspended_at = 2026-10-29T08:51:31Z` (**14:21:31 IST, 29 October**).
- Binding still `br-young-wind-axoimpov`; min/max remain 0.25 CU.
- All five pre-existing endpoint-to-branch bindings are preserved; the original remains primary/default.
- Exactly one endpoint was added. It is retained, suspended, and not deleted. No further SQL was run against it after suspension.

## Comparison coverage

Incident window: **26 October 2026, 07:47:21–08:06:15 IST** (`02:17:21–02:36:15 UTC`), as recorded in the incident plan.

| Database | Branch / explicit endpoint | Fresh schema revision |
|---|---|---|
| Original | br-polished-surf-axulzu38 / ep-fragrant-surf-axkjz078 | 20261014_22 |
| Holding copy | br-misty-recipe-ax4djqgq / ep-wandering-credit-axfl5bss | 20261014_22 |
| Recovery copy | br-young-wind-axoimpov / ep-morning-sunset-axii59da | 20261025_29 |

Compared **49 common application tables** by stable primary-key identity and fingerprints of all original application columns. Every common table has a stable primary key; no original application column was omitted due to absence or type mismatch. Recovery-only columns were excluded from cross-schema fingerprints; none exists in a populated recovery table. The expected Alembic version difference is recorded separately, not treated as data loss.

The bound was 1,000 rows per table, with a 1,001-row sentinel to detect truncation. **No table was truncated.** This is a bounded comparison of retained current states, not a historic WAL replay or an atomic snapshot shared across three databases. Each individual comparison transaction had a consistent read-only snapshot; original production activity could continue between transactions.

Seven new-schema tables exist only in recovery and are **all empty**: connection_fee_credits, connection_fee_events, connection_fee_refund_requests, customer_kyc_applications, customer_kyc_documents, demand_drafts and demand_selections.

## Proven retained-state findings

| Finding | Result | Evidence |
|---|---|---|
| Recovery versus holding | PASS | All 49 common tables match on stable identity and every original column; no row-count or content differences |
| Recovery-only retained records absent from original | PASS: none found | Zero recovery-only stable identities across all common tables; seven additional recovery tables empty |
| Shared records changed during incident | No surviving incident-timestamped difference found | No observed creation/update/action timestamp falls inside the recorded window in the compared retained state |
| Original-only sessions | Two, both after incident | Original has 28 refresh_sessions; holding/recovery have 26. Both additional sessions have created_at strictly AFTER 02:36:15 UTC on 26 October; no identifiers or exact activity times reported |
| Other original/recovery content difference | One post-incident last-login field | All six user identities match. Only last_login_at differs for one row, and the original value is strictly AFTER the incident. All other compared user columns match |
| Other common application tables | PASS | No original-only, recovery-only or changed common records beyond the post-incident differences above |
| Duplicate primary identities | None detected | Zero duplicate identity groups in every compared table; this is not a separate global semantic-deduplication audit |

The preserved recovery copy contains no surviving incident-window record that is missing from the original, and no surviving extra business record indicating duplication or stranding. The two newer sessions and newer last-login value are **proven post-incident differences**; their legitimacy or request origin is not asserted by this reconciliation. No password or other user-state difference was found in the compared common columns.

**Data loss, duplication or stranding attributable to the incident was not detected in the retained database states. No data repair, row merge, restore or endpoint switch is proposed.** This statement is narrower than proving that no historical write ever occurred.

## Remaining historical uncertainty

The original and holding copies were not databases that served the original endpoint throughout the incident; recovery was. Their agreement with recovery now closes the previously missing retained-state comparison, but cannot reveal a write later deleted or overwritten, a mutation lacking a useful timestamp, a transaction outside the inspected retained state, or a client acknowledgement whose resulting record is no longer present.

Reuse of the earlier bounded log investigation is explicit: branch database-log requests returned no records, and Vercel refused the incident window because Hobby runtime-log retention had expired. No archived request/audit/WAL evidence was supplied to this task. This does not prove that no archives exist elsewhere. No repeated full audit or futile old-window polling was performed.

Accordingly:

- **PASS:** retained-state reconciliation, with no surviving recovery-only records and only proven post-incident differences in original.
- **BLOCKED:** a definitive historical zero-write/no-loss claim and full incident closure without owner review of these evidence limits or additional archived evidence.
- **No repair approval requested:** there are no identified rows requiring reconciliation writes. If new evidence identifies missing writes, any repair must be proposed separately with exact source/target, affected predicates/counts, validation and rollback; this approval does not cover it.

## Continued safe release preparation

The exact local source base remains `fa2595741d261cf15d2c0849b13e446d1eaffd20` on `release/customer-first-20261026`. The preserved uncommitted correction patch remains SHA-256 `f070e9d32a4740cbcfd0cdbd5bb8921be1133f967e57e16d5cf9f69b81976440`. Existing corrections and handoff changes were preserved. No commit, push or merge occurred.

Fresh artifact-integrity verification passed, including all recorded artifact hashes, 64 backend Python files matching the pinned base, frontend entry/API origin and the corrected source changed-path set. Existing local test evidence from 26–27 October is reused; application tests were not repeated without a code change. No artifact was deployed. The metadata-only reconciliation status update does not change artifact bytes or source provenance.

Fresh 29 October serving-alias lookups still identify old `main` SHA `ccd594df8a78f56041876c058b522e0624db4fb6`, source redeploy, READY Production: frontend `dpl_APPh8etW4m7yRoC4zDSyjtkWeExi`; backend `dpl_7pdmUXDmaY9bjQZFRxbPX8n3wyGe`.

Production still has schema **22**; candidate requires **29**. The reviewed sequence remains maintenance/write control and fresh recovery preparation, explicit 22-to-29 migration, compatible API first, matching frontend second, then separately authorized post-release checks. All destructive downgrades 23–29 refuse rollback; old-code/new-schema rollback is not approved. Incident copies are retained evidence, not an automatically approved fresh protected backup or a test environment.

Production execution remains BLOCKED on owner review of residual incident uncertainty, a reviewed immutable commit containing local corrections with green exact-head hosted CI, private production binding/settings confirmation, Google acceptance, fresh protected backup/isolated restore proof and the operator/window/RPO/RTO. Other paid/scanner/consent/tax/refund launch gates in the reviewed plan remain open. No production migration, deployment, production data repair, plan upgrade, real Maps operation or email was performed.

The existing email authorization remains password-reset only; dedicated-test-account status must be confirmed first. Verification/resend require separate recipient authorization. Real mailbox receipt/authentication and working production links must be confirmed privately after a separately approved release; provider acceptance is not receipt.

**Next action:** owner review of the retained-state PASS and historical evidence gap; supply archived incident history if a stronger conclusion is required, or explicitly accept the documented residual uncertainty for incident closure. Separately authorize committing/pushing the preserved corrections if desired, then use exact-head CI and the existing release package to finish the remaining gates. A production execution request must name the final corrected SHA, exact deployment artifacts/IDs, 22-to-29 window/operator, fresh recovery point/RPO/RTO and post-release scope. No production execution approval is implied by this reconciliation.


## Owner sign-off for release preparation — 29 October 2026

The owner explicitly accepted the documented retained-state reconciliation and historical-evidence limitation, and signed off the incident for release preparation. This is NOT a claim of absolute proof of no historical data loss. Preserve all incident copies and snap-little-tree-ax4fn88h. The one approved recovery read-only endpoint remains suspended. No data repair is indicated or authorized.

Incident sign-off removes the incident-owner-review preparation gate. Production execution remains separate: final exact-head CI, private settings confirmation, fresh backup/isolated restore readiness and a reviewed migration/deployment window are still required. No migration, deployment, data repair, plan upgrade or email is authorized by this sign-off.
