# Release implementation checklist

Authority: owner implementation request, release-review.md and AGENTS.md. Work remains local/uncommitted; no production or provider operations.

- [x] 1. Driver assigned-trip UI/read/action permissions — focused regressions pass; real DB journey blocked, not completed verification.
- [x] 2. OTP acceptance-truthful delivery and issue/verify UI — local fake + authorization/state/failed-send/replay regressions pass; real delivery and receipts unverified.
- [ ] 3. Real isolated DB failure-counter regression — blocked until E2E_DATABASE_URL is configured; no fallback.
- [x] 4. Authenticate anonymous/invalid protected requests before DB work — reproduced route security regression passes.
- [x] 5. Stored settlement snapshots — regression passes, historical values not recalculated; PostgreSQL concurrency unverified.
- [x] 6. Dedicated CI database/job configuration and YAML parsing complete; GitHub execution/real database gates still blocked/unverified.
- [x] 7. Vehicle files/review implemented against existing five expiry rules; local adapter/API regression passes. Legacy backfill policy, DB/browser and real AWS blocked/unverified.
- [x] 8. Account recovery/resend/delivery/UI implemented; focused regressions pass. Real DB/browser/SMTP and automatic signup dispatch remain incomplete/unverified.
- [x] 9. Minimum searched users/bookings/status operations and existing workflow links implemented. Full admin console and supply-reactivation lifecycle still partial.
- [x] 10. API-backed homepage and logo navigation; two fresh Chromium tests pass.
- [x] 11. Shared-capacity assessment recorded in release review; Model B preserved, publication/reservation/shared-booking UI and integration journey still missing.

Follow-up: MSG91 saved-phone widget integration and server-side proof validation implemented. Public widget token is environment-only, account Authkey backend-only. Local fake browser/provider tests pass; real provider and PostgreSQL checks remain blocked/unverified. Owner approved verified-only phone exclusivity: canonical inputs, verified-only ownership check/index, safe migration 22, and unchanged-phone verification preservation implemented; real migration/concurrency regressions remain blocked. New vehicle evidence is pinned to immutable S3 versions; provider KYC still needs equivalent immutable-reference handling. Safety rejection/suspension no longer needs storage construction. See the 2026-10-14 handoff and widget configuration guide.

Implementation approach: reuse the existing assigned-driver API rather than widen general booking visibility. Do not expose full booking financials to drivers. Delivery acknowledgement means accepted, not confirmed delivered. Database-dependent results remain blocked, not passed. User authorization overrides skill defaults to commit, create separate worktrees or pause for every design stage; preserve the current dirty checkout and use focused red/green tests. No delegated workers are used.
