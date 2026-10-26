# Recovery rehearsal isolation incident — 26 October 2026

Status: RELEASE BLOCKED. Original endpoint/default/name restored; possible intervening writes NOT reconciled. No new application deployment or live payment was initiated. Do not claim production was untouched.

## What happened

At02:17:21UTC, restore_snapshot was called for fresh snap-little-tree-ax4fn88h with a new branch name but WITHOUT finalize:false. The provider finalized the restore: br-young-wind-axoimpov became production/default, and original endpoint ep-fragrant-surf-axkjz078 moved to it. The original br-polished-surf-axulzu38 remained preserved at22 with a replacement endpoint. The response's initial name/state was mistakenly treated as proof of isolation; endpoint/default mapping was not verified before applying23–29to the restored copy. That SQL completed, but the copy was production-bound at that time. This was an unauthorized production configuration side effect and invalidates the claim of an isolated recovery rehearsal. It is not an approved production migration.

## Corrective action and verified state

Detected actual endpoint mapping; attempted original endpoint rebind was refused409because destination had the replacement read-write endpoint. Created no-compute holding branch br-misty-recipe-ax4djqgq, moved replacement ep-wandering-credit-axfl5bss there, and restored ORIGINAL endpoint ep-fragrant-surf-axkjz078 to ORIGINAL branch br-polished-surf-axulzu38 at02:36:15UTC. A proposed move of the extra endpoint onto recovery was rejected by automatic approval review as a further production-disruption risk. That move was stopped, with no workaround. Restored original branch name production, primary/default flags; renamed restored copy recovery-rehearsal-20261026-not-preview.

Fresh read-only endpoint-specific transaction verifies original production endpoint/branch22and6users. Default-branch lookup confirms original production identity. Public /health/live, /health/ready and /version allHTTP200. Both Vercel serving aliases remain ccd594d, no new app deployment. Endpoint binding window approximately02:17:21–02:36:15UTC(18m54s); actual user impact and intervening writes are NOT yet established. Equal aggregate user counts do not prove no data loss or no requests.

## Preserve and investigate; no further mutation

Preserve snapshot, original branch, restored copy29and holding branch22. Do not delete/rebind/restore/synchronise data automatically. The snapshot/branches are not independently protected by plan controls; protection creation was refused by plan limit. Do not call the rehearsal clean/PASS. Further incident review must compare appropriate audit/request/database evidence privately and identify any writes on the restored copy during the binding window, without exposing identity data or credentials. Any write reconciliation/endpoint cleanup needs separately reviewed approval. Neither production data copy may be used for E2E.

Future restore must explicitly set finalize:false, NEVER invoke finalization, and verify endpoints, default/primary/name and exact source/target revisions before ANY rehearsal write. Prefer a separate project and explicitly owned nonproduction connection when possible. Stop if any original endpoint/default changes. Add independent provider-specific controls/review before rerunning restoration; do not use branch names as isolation proof.

## Independent preview work

Separate preview project aged-pine-27393574 contains no production users/bookings/providers. Clean migrations through29succeeded,57tables; schema column fingerprint matches restored copy29. Runtime role has no superuser/createdb/createrole/replication/schema-CREATE or alembic_version UPDATE permission; application DML allowed. Preview uses pooled runtime/direct migration URI, unique secret, production security validation and disabled payments/simulations. Preview endpoint ep-icy-shape-b47ojbx0 now disabled to avoid idle use/accidental activation. Provider refused changing passwordless_access; do not claim that was disabled. No preview deployment; storage/scanner/Redis/URL binding remain missing.

## Current CI evidence

Commit1099527: main CI PASS:430backend unit tests,72isolated PostgreSQL tests,54frontend tests, lint/types/build and containers. Browser job still pending at record creation. Actual discovery revealed default legacy configuration collected19tests including customer/Maps/email checks requiring other server policies. Corrected discovery preserves8legacy/session/shared/vehicle cases and runs customer KYC/demand management, simulated Maps and email under their existing dedicated configurations. Real Google checks remain explicit opt-in, never CI proof. New browser outcome must be verified separately. Do not label collection listing as an executed browser PASS.
