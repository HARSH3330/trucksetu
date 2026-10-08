# Terms acceptance

New bookings require authenticated account acceptance of the current Terms version.
The quotation confirmation flow loads a popup with an unchecked checkbox. Cancelling
does not create a booking. Acceptance is stored in PostgreSQL and applies across
devices; the server independently checks acceptance for every booking.

The initial document is the owner's supplied draft, branded TransivoX. It retains
unconfirmed entity/contact/jurisdiction placeholders and is explicitly marked draft
pending legal review. Resolve these and obtain legal review before public launch.
The Terms refer to a Privacy Policy; that policy must also be supplied and published.

Apply Alembic migration `20261008_19` before deploying the backend. Frontend and API
must both be deployed. No production migration or deployment is run by this change.

Content lives in `backend/app/legal/terms-v1.txt`, served by `/api/v1/legal/terms`.
For every revision, preserve the old document, add a new document, and update
`TERMS_VERSION` and the document path in `backend/app/api/terms.py`. Never edit a
published version in place: acceptance is tied to the exact SHA-256 content hash.

Acceptance stores user ID, policy version, content hash and UTC timestamp. Audit
events record acceptance; booking customer snapshots reference its ID and version.
No IP address or user agent is retained for this feature.

Verify locally: unauthenticated acceptance is denied; unchecked acceptance cannot
continue; cancel creates no booking; acceptance survives a new session; repeat
acceptance is idempotent; outdated versions are rejected; booking API calls without
acceptance return 409. Real PostgreSQL transaction/concurrency and browser flow
checks remain necessary before production rollout.
