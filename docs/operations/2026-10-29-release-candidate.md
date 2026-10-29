# Final release candidate — 29 October 2026

Incident signed off by owner for release preparation with the documented historical-evidence limitation accepted. This is not absolute proof of no historical loss. Copies and snapshot remain preserved, new reconciliation endpoint suspended; no data repair is proposed.

## Reviewed source and push boundary

This candidate is the commit introducing this record on release/customer-first-20261026, parent fa2595741d261cf15d2c0849b13e446d1eaffd20. The exact resulting SHA must be copied from Git and used in hosted CI and generated artifacts; no floating branch may be substituted at deployment. Post-commit attestation belongs outside the commit to avoid self-referential hashes.

Scoped independent review of DemandWorkspace.tsx, customerJourney.ts, release-demand-management.spec.ts and playwright.yml found one CI build-environment issue, now fixed with synthetic Maps values on the Vite build step. CI-equivalent harness build and five simulated browser checks passed. Earlier focused database-backed browser/migration and unit checks are retained as evidence; final exact-head hosted CI is still required.

Remote root and backend vercel.json were fetched on the release branch and explicitly disable automatic deployments for this exact branch. No alternate vercel.ts or overlapping true pattern is present. Current Vercel Git context links only trucksetu-api and trucksetu-whri for this repository; both list zero release-branch deployments. Actions: CI on PR/main/develop; browser on PR/manual dispatch; production migration manual-only; no deployment job. Native Git read confirms remote release head fa259574. Use a normal fast-forward push only to the release branch, then recheck both deployment lists and serving aliases. No cloud guard change was made. Provider semantics: [Vercel Git configuration](https://vercel.com/docs/project-configuration/git-configuration).

The connector omits project root/Git-setting detail and the dashboard session is signed out. The push decision relies on both supported-root guards, official provider semantics, matching connected projects, remote-source verification and the no-deployment branch history. Do not interpret it as proof about arbitrary unknown external automation. Never push main, merge, dispatch migrate-production or invoke a deployment in this task.

## Configuration and functional evidence

Production frontend Maps entries were present, nonempty and non-demo; the owner now privately confirms www referrer restriction, Maps JavaScript API/Places API(New), owned JavaScript Map ID and existing billing. This is private owner confirmation; no real Maps request was run.

Production backend requires SMTP_HOST=smtp-relay.brevo.com, SMTP_PORT=587/STARTTLS, SMTP_USERNAME=actual Brevo SMTP Login, SMTP_PASSWORD=separate production SMTP key, EMAIL_FROM=active sender; EMAIL_REPLY_TO optional. PUBLIC_FRONTEND_URL=https://www.transivox.in verified. Sensitive-value correctness requires private owner confirmation because the API will not return those values. Sender active evidence does not prove runtime credential correctness or mailbox delivery. No email is authorized here.

## Backup readiness and restore procedure — no execution

Read-only provider checks: project morning-forest-29164100, PostgreSQL18, PITR history21600seconds, original production branch br-polished-surf-axulzu38, automatic snapshot schedule empty. Retained manual snap-little-tree-ax4fn88h is from26October, not a fresh release recovery point. Existing branches are unprotected under the recorded plan limitation. A stopped local Docker backup is not a Neon production backup; scripts/backup-postgres.ps1 must not be pointed at production.

Additional authorization is needed for a fresh source-branch snapshot, any encrypted logical export and approved private destination/key custody, creating an isolated restore destination/compute, any protection/retention change and any paid plan change. Current task performs none of these. Choose window/operator and record RPO/RTO; history retention alone is not backup/restore proof.

Proposed restore rehearsal after separate approval: capture source branch/endpoint/default identity and schema22; create a named fresh snapshot on the exact original branch; record snapshot ID/time/expiry and approved vault evidence. Restore to a NEW separately named isolated branch with explicit finalize:false and NO existing target_branch_id. NEVER call finalize_branch_restore. Verify source/default/primary/endpoint mapping unchanged before any further action. If no compute exists on the restore, seek the approved separate compute scope; never move an existing endpoint to get access. Read-only compare schema, constraints, stable identities and business/audit/financial state. Rehearse only in the isolated destination; preserve all incident evidence. Any real cutover or replay needs its own approval and measured data-loss decision. Suspend only new rehearsal compute when done; no automatic deletion.

## Exact production sequence to approve later

Current production schema20261014_22 -> target20261025_29; all23–29 migrations inspected. New API is incompatible with22. Maintenance/write control and webhook retention first; fresh approved backup/restore readiness next; one exact frozen-source Alembic upgrade to20261025_29 under direct migration identity; verify head29; stage/promote compatible API on trucksetu-api; health/readiness/version/schema checks; matching frontend on trucksetu-whri; verify canonical www/API origin, real Maps/Places and only separately authorized email flows. Keep checkout/tax/test/unsafe capabilities disabled as reviewed.

No target Vercel deployment IDs exist before an authorized deployment; do not invent them. Local source/frontend/backend artifacts and their exact-SHA digests will be generated after committing, then frozen with CI run/job/artifact IDs in the external release attestation. Staging with --skip-domain is still a deployment and remains unauthorized here.

Rollback: no destructive downgrade23–29; old API/new29 compatibility is not approved. Prefer reviewed forward fix, maintain write controls on failure, and preserve financial/audit/version history. Frontend rollback requires a compatible API/schema. Database restore/cutover/replay requires separate explicit approval; no automatic original-endpoint move or snapshot finalization.

Post-release checks: both aliases must identify the exact approved source/deployment IDs; API liveness/readiness/version and actual bound schema29; canonical www, API origin, Maps/Places behavior and manual fallback. Email authorization is reset-only and dedicated-test-account status is still unconfirmed; signup/verification/resend need separate authorization. Owner privately confirms actual receipt, SPF/DKIM/DMARC and production links; provider acceptance alone is insufficient. Never print/store credentials or token-bearing links.
