# Phase B — role navigation implementation

The application shell retains the complete API-returned CurrentUser. Login, startup restoration and the account avatar share defaultDestination in src/lib/navigation.ts. Priority is admin/superadmin, provider/fleet_owner, driver, customer; unknown/empty roles or a signed-out user resolve to home. No token decoding or new authorization grant is involved.

Startup migrates the legacy refresh token before checking session storage, including refresh-only sessions. A cancelled restoration cannot update the shell after cleanup. Avatar access now has a descriptive accessible label.

Changes: src/main.tsx, src/lib/navigation.ts, src/lib/navigation.test.ts and e2e/fixtures/api.ts. The E2E helper's successful login destination assertion follows the actual API-returned role; no E2E run was performed.

Focused evidence: the role regression failed for admin/superadmin/driver and mixed/unknown role cases against the old dashboard-only rule; after implementation all 24 frontend unit tests passed, and tsc -b passed. These results prove role selection/type consistency, not browser interaction, refresh delivery or production deployment. E2E, external-service and manual browser verification remain paused.

Backend role/ownership checks, existing KYC tests/assertions, provider documents and admin console business operations were not changed. Full admin users/bookings console functionality remains a separate gap.

No commit, push or deployment authorized or performed.
