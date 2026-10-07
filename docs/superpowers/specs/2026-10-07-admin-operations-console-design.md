# TransivoX Admin Operations Console Design

**Date:** 2026-10-07  
**Status:** Approved direction; pending implementation-plan approval

## Objective

Give `admin` and `superadmin` accounts a role-appropriate operations console instead of routing them to the customer dashboard. The console must expose the records needed to operate the marketplace without weakening tenant boundaries, KYC privacy, financial controls, or auditability.

## Current Problem

The frontend treats provider and fleet-owner accounts specially but treats every other authenticated role as a customer. As a result:

- `admin` and `superadmin` accounts land on a page titled **Customer dashboard**;
- clicking the account avatar always opens that same dashboard;
- an existing access token does not restore the current user profile and role after a browser refresh;
- the existing `LiveAdmin` control centre is not reachable through normal role-aware navigation;
- the existing admin view contains aggregate metrics and review links but no consolidated user, booking, trip, payment, dispute, or audit-record browser.

## Chosen Approach

Extend the existing React and FastAPI application. Do not introduce a third-party admin framework or a separate admin deployment.

This approach preserves the current visual system, authentication model, API conventions, deployment topology, and test infrastructure. Administrative information will be exposed through focused, paginated endpoints rather than a single endpoint that returns the entire database.

## Role Routing and Session Restoration

The application will load `/api/v1/auth/me` when an access or refresh token exists. The returned roles determine the default authenticated destination:

| Role | Default destination |
| --- | --- |
| `superadmin`, `admin` | Marketplace Control Centre |
| `provider`, `fleet_owner` | Provider dashboard |
| `driver` | Trip operations |
| `customer` | Customer dashboard |

Role priority is `superadmin/admin`, then `provider/fleet_owner`, then `driver`, then `customer`. This prevents a privileged account with more than one role from being routed to a lower-privilege dashboard.

The application shell will retain the complete current-user object instead of only the display name. The account/avatar action will use the same role-aware destination. A failed session restoration will clear unusable tokens and return the interface to the signed-out state.

## Permission Model

### Admin

An `admin` may:

- view paginated users and their non-secret account metadata;
- view providers, KYC status, vehicles, drivers, bookings, trips, payments, invoices, disputes, safety reports, and audit events;
- review KYC applications and vehicle compliance records;
- confirm reported offline payments and issue invoices using existing controlled flows;
- resolve disputes and perform documented operational actions;
- suspend a customer, provider, fleet-owner, or driver account with a required reason;
- reactivate non-privileged accounts when the underlying issue has been resolved.

### Superadmin

A `superadmin` receives all admin abilities and may additionally:

- assign or remove non-superadmin roles;
- promote an eligible account to `admin`;
- suspend or reactivate administrator accounts other than their own;
- manage marketplace pricing rules;
- perform security-sensitive configuration actions added in later phases.

### Prohibited Actions

Neither role may:

- retrieve password hashes, refresh-token hashes, OTP hashes, payment secrets, or environment secrets;
- delete or edit audit-log entries;
- permanently delete bookings, payments, invoices, KYC decisions, or other regulated records from this console;
- change their own privileged role or suspend their own account;
- create another `superadmin` through the general role-management interface;
- view full KYC documents from general user or booking lists.

Creation or recovery of the first superadmin remains a separate temporary-token process.

## Console Information Architecture

The Marketplace Control Centre will contain these sections:

1. **Overview** — existing marketplace health, GMV, completion rate, funnel metrics, pending reviews, disputes, and operational alerts.
2. **Users** — searchable accounts with role, verification state, account status, creation time, and last login.
3. **Providers & KYC** — provider identity, operating status, KYC state, document-expiry warnings, and links to the existing protected review flow.
4. **Bookings & Trips** — searchable bookings with customer, provider allocations, route, value, booking state, vehicles, drivers, and trip progress.
5. **Fleet** — registered vehicles and drivers, document/approval status, expiry warnings, and the existing vehicle-review workflow.
6. **Payments** — booking totals, confirmed and pending payments, gateway/offline state, refunds, invoices, commissions, and settlement eligibility.
7. **Trust & Safety** — disputes, safety reports, cancellation records, and resolution status.
8. **Audit Logs** — chronological administrative and security events with actor, action, entity, request ID, and timestamp.

Each section will use server-side pagination, search, filters, stable ordering, loading states, empty states, retry behavior, and explicit permission-error states.

## API Design

Administrative routes remain under `/api/v1/admin` and require `admin` or `superadmin` through the existing `require_roles` dependency.

### Users

`GET /api/v1/admin/users`

Parameters:

- `page` and `page_size`;
- `query` for email, mobile, or name;
- `role`;
- `status`;
- `email_verified`;
- `sort` with an allowlist of supported fields.

Response items contain ID, name, email, masked mobile where appropriate, roles, status, verification flags, creation time, and last-login time. They never contain authentication secrets.

`PATCH /api/v1/admin/users/{user_id}/status`

- accepts `active` or `suspended` plus a required reason;
- prevents self-suspension;
- prevents an ordinary admin from changing a privileged account;
- revokes active refresh sessions when an account is suspended;
- creates an audit event.

`PUT /api/v1/admin/users/{user_id}/roles`

- restricted to `superadmin`;
- accepts only an allowlisted set of roles;
- cannot assign `superadmin`;
- cannot modify the caller's own privileged roles;
- creates an audit event with before and after values.

### Bookings and Operations

`GET /api/v1/admin/bookings`

Supports pagination and filters for booking ID, customer, provider, status, route, and creation date. Items include customer identity, route snapshot, booking value, allocations, provider identity, vehicle/driver references, latest trip states, payment summary, and dispute indicator.

Detailed KYC files, chat bodies, password data, OTP values, payment credentials, and full card information are excluded.

Existing focused endpoints remain authoritative for KYC review, vehicle review, payment confirmation, invoice issue, refunds, disputes, pricing rules, analytics, and audit logs. The console links to these workflows instead of duplicating their mutation logic.

## Privacy and Security

- Every new endpoint enforces authorization on the server; hidden frontend buttons are not security controls.
- Lists return the minimum fields necessary for operations.
- Aadhaar, PAN and licence files remain in the existing private-storage workflow and require explicit document-review access.
- KYC download requests remain time limited and audit logged.
- Mutation endpoints require a reason and write before/after values to `audit_logs`.
- Account suspension revokes existing refresh sessions.
- Search parameters are bounded and used through SQLAlchemy expressions, not interpolated SQL.
- Page sizes are capped to prevent bulk extraction and expensive unbounded queries.
- Administrative responses inherit the existing `Cache-Control: no-store` security header.
- The console will not provide mass export in the initial implementation. Any future export requires separate authorization, audit logging, and privacy review.

## Frontend Components

- A pure role-routing helper determines the default destination and is unit tested.
- `App` restores the current account on startup and stores the complete account object.
- `Header` receives roles and opens the appropriate dashboard.
- `AuthModal` returns the authenticated user object to the application shell.
- `LiveAdmin` becomes the tabbed operations shell.
- Focused child components render users, bookings, operations links, and audit logs.
- Existing KYC and vehicle-review screens remain separate protected workflows and are opened from the console.

The responsive layout will preserve the existing TransivoX design. On small screens, the section navigation becomes horizontally scrollable or a compact selector, and tabular results become stacked record cards.

## Error Handling

- `401`: clear the invalid session and show sign-in state.
- `403`: show an administrator-access-required state without leaking record existence.
- `404`: show a record-not-found message after an item changes or is removed from a queue.
- `409`: preserve the current view and explain the conflicting state change.
- `422`: display field-specific validation details where available.
- `429`: show a retry-later message without automatically repeating mutations.
- transient `502`, `503`, or `504`: retain existing one-time retry behavior for safe GET requests.

## Testing Strategy

### Backend

- non-admin users receive `403` from every new admin endpoint;
- user search, role/status filters, stable pagination, and page-size limits work;
- responses never expose password, token, OTP, or secret fields;
- ordinary admins cannot modify privileged accounts;
- only superadmins can change roles;
- callers cannot modify their own privileged role or suspend themselves;
- suspending an account revokes active refresh sessions;
- all mutations create correct audit records;
- booking results include operational relationships without protected document or message contents.

### Frontend

- each role resolves to the expected default destination;
- a superadmin is never labelled as a customer;
- login and page refresh both restore the same privileged destination;
- the avatar returns an administrator to the control centre;
- each section handles loading, empty, forbidden, failure, and populated states;
- searches and filters send bounded server-side parameters;
- high-risk actions require confirmation and a reason.

### Verification

- run the complete backend test suite;
- run the frontend type check and production build;
- run focused role-routing/component tests;
- manually verify customer, provider, driver, admin, and superadmin navigation;
- manually verify that a customer token cannot call an admin endpoint.

## Delivery Sequence

1. Add failing role-routing and authorization tests.
2. Implement session restoration and role-aware navigation.
3. Add paginated users API and user-management controls.
4. Add paginated booking-operations API and console section.
5. Integrate existing KYC, fleet, payment, dispute, and audit workflows into the console navigation.
6. Run full verification and security boundary checks.
7. Commit and push only after verification succeeds or with any unresolved test limitation explicitly reported.

## Out of Scope

- permanent deletion of regulated operational records;
- unrestricted CSV/database export;
- direct editing of KYC documents, financial records, chat messages, or audit logs;
- creation of additional superadmins through the console;
- infrastructure hosting changes;
- full legal-policy implementation;
- automated KYC decision making.

## Success Criteria

- An existing admin or superadmin lands on the Marketplace Control Centre after login and refresh.
- The customer-dashboard label never appears for a solely privileged account.
- Authorized operators can find users and bookings and reach all existing review workflows from the console.
- Sensitive records remain minimized, protected, and audit logged.
- Non-admin accounts cannot access administrative data or mutations.
- Existing customer, provider, fleet-owner, and driver workflows continue to function.
