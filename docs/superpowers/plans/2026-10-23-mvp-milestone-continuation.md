# Existing-project MVP continuation

23 October 2026 (IST). Continue the dirty candidate atop ba305778 on codex/launch-preparation-no-otp-maps. User attachment acf328c9 updates the confirmed scope; no rebuild, new project, push, deployment, production migration or paid/external action.

## Existing, partial and missing

The customer demand/draft/bid/selection/INR 1,000 captured-contact slice, contact revisit/ownership, assignment, operations ledger, mobile UI and local PostgreSQL tests already exist. Reuse saved exact-source results. Customer document-KYC rules, real gateway/scanner acceptance and tax/refund/failure/replacement rules remain undecided or unverified; never invent approval. Existing verified-account test policy remains explicitly local. OTP/Maps-dependent new workflows remain deferred; retain existing security enforcement and code.

## Narrow implementation design

1. Add an independent server flag, ENABLE_PROVIDER_FIRST_PUBLICATION=false, for public provider route creation. It must apply even when legacy allocation is explicitly enabled. Retain shared capacity accounting, reservations, concurrency, existing routes and private fleet/driver management. The new explicit instruction to disable provider-first public publishing supersedes the previous enabled-publication local evidence. Frontend reads availability from the API and gives an honest disabled message; hiding a form is not the backend control.
2. Guard settlement/percentage commission for new customer-demand bookings, and forbid new calculations while transport collection is disabled. Preserve historical commission records and retained legacy implementation. Fee accounting remains separate and exact; no migration is required.
3. Exercise remaining lifecycle requirements using isolated PostgreSQL: draft owner/version controls; demand edits expiring old bids; provider bid revision/history/withdrawal; current verification; repeat/concurrent order attempts; delayed/failed/unrelated/adverse events; trip/customer/admin boundaries. Fix only reproduced defects. Do not bypass OTP/scan enforcement.
4. Strengthen existing browser slice with failed/unrelated payments, ownership after unlock and sign-out/sign-in contact recovery without another order. Verify revised public publication gate at mobile width. Reuse existing unchanged KYC, cookie/logout, shared-capacity and restore evidence; run affected complete suites once changes settle.
5. Update handoff, exact tested dirty-source identity, changed-file list and report with simulated/blocked/not-run checks, screenshots and concrete release steps. No production action. Do not call customer document KYC complete or label fictional fixture review as a real scan.

## Tests before implementation

Observe failing contract tests for the independent publication flag and commission guard before writing product changes. Real PostgreSQL tests must use the existing exact-name/loopback/restricted-role guard and run sequentially with browser resets. Preserve all existing dirty changes and prior reports. No schema changes are planned, so the prior revision-25 restore rehearsal remains dated applicable evidence.
