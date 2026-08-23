# TruckSetu

TruckSetu is a mobile-first marketplace for heavy-vehicle logistics in India. It supports both sides of the market: customers can publish transport requirements and compare quotes, while verified transporters can publish routes with spare capacity.

## Included in this working foundation

- Responsive customer landing experience and multi-step requirement wizard
- Live-load discovery and available-capacity marketplace
- Booking and manual trip-status timeline
- Customer/business dashboard and admin operations overview
- FastAPI health endpoints, safe vehicle recommendation, and enforced trip transitions
- Secure OTP generation, JWT helpers, PostgreSQL/Redis configuration, and decimal money settings
- Domain tests for vehicle safety, trip transitions, and multi-provider allocation limits
- Phase 2 persistence models and migration for requests, ordered stops, cargo, and configurable vehicle categories
- Versioned create/list request APIs with route filtering and server-side capacity enforcement
- Phase 3 verified-provider job marketplace, final-price quotations, immutable quote versions, competitor price comparison, and counter-offers
- Phase 4 transactional multi-provider allocation, immutable booking snapshots, driver assignment, trip state enforcement, and secure pickup/delivery OTP records
- Phase 5 configurable advances, Razorpay abstraction, verified webhook processing, offline confirmation, commission/tax snapshots, delivery-gated settlement, and GST invoice records
- Phase 6 verified-provider spare-capacity publishing, ordered-route matching, cargo compatibility, idempotent reservations, and row-locked capacity protection
- Phase 7 verified-trip reviews, participant-only disputes, evidence history, configurable cancellation snapshots, refunds, and safety reports
- Phase 8 in-app notifications, channel preferences, external SMS/WhatsApp adapters, booking-scoped chat, unread tracking, and contact-privacy enforcement
- Phase 9 optional Gemini extraction with deterministic fallback, safe vehicle logic, explainable match ranking, fair-price estimates, and human-reviewed risk flags
- Phase 10 request tracing, structured logs, security headers, rate limits, real readiness probes, audit logs, event analytics, CI gates, migrations, container health and backup tooling
- Phase 11 persistent accounts, public-role controls, email verification, lockout protection, typed access tokens, rotating refresh sessions, protected admin analytics, and a live API-backed sign-in experience
- Phase 12 provider KYC applications, private direct-to-storage uploads, role-scoped document access, admin decision history, resubmission/suspension handling, and expiry monitoring
- Phase 13 manual driver/owner KYC policy and Google Routes-based advisory trip pricing with separately itemised loading, unloading, waiting, extra-stop and night charges; providers continue to set the final quotation
- Environment template with no committed credentials

The visual marketplace uses realistic demonstration records so the product can be evaluated without third-party credentials. They are clearly presented as interface data; the API does not fake successful bookings or payments.

## Local setup

### Web application

```bash
npm install
npm run dev
```

Open the URL shown by the development server. A production build is created with `npm run build`.

### API

Python 3.12, PostgreSQL, and Redis are expected.

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Copy `.env.example` to `.env` and replace every production-sensitive placeholder. API documentation is available at `http://localhost:8000/docs`; service probes are `/health` and `/ready`.

### Docker

After creating `.env`, run `docker compose up --build`. The website is served on port 3000 and the API on port 8000.

## Architecture direction

- `src/` — responsive marketplace experience
- `backend/app/core/` — configuration, database, Redis, and security infrastructure
- `backend/app/domain.py` — framework-independent business invariants
- `backend/app/main.py` — versioned REST application boundary
- `backend/tests/` — critical domain-rule tests

PostgreSQL remains the source of truth for bookings, financial snapshots, quote versions, capacity reservations, refresh sessions, and audit records. Redis is reserved for rate limits, cache, and background coordination. Capacity, truck allocation, and refresh-token rotation writes use database transactions with row locks.

## Production handoff

Before accepting real transactions, complete malware scanning for uploaded documents, notification workers, delivery-provider integration for account verification, and full role/permission integration tests. Payment gateway and GST flows must also pass sandbox and reconciliation testing. Legal pages and tax configuration require review by qualified Indian legal and tax advisers. Do not describe payments as escrow unless that regulated arrangement is actually implemented.

## Phase status

- Phase 1 foundation: present
- Phase 2 customer marketplace: implemented
- Phase 3 provider marketplace: implemented
- Phase 4 booking and trip workflow: implemented
- Phase 5 payments and financial architecture: implemented
- Phase 6 capacity marketplace: implemented
- Phase 7 trust and safety: implemented
- Phase 8 communications: implemented
- Phase 9 AI service layer: implemented
- Phase 10 production-hardening foundation: implemented
- Phase 11 identity and launch-readiness integration: implemented
- Phase 12 provider verification and document compliance: implemented
- Phase 13 marketplace trip suggestions and launch KYC policy: implemented

The technical production-hardening foundation is present, but this does not constitute a penetration test, legal certification or operational readiness approval. See `SECURITY.md` and `DEPLOYMENT.md` for the mandatory launch checklist.
