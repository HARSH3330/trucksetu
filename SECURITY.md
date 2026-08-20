# TruckSetu security baseline

## Implemented controls

- Environment-only secrets and production startup validation
- Password hashing, signed tokens, secure OTP generation and hashed OTP storage
- Request IDs, structured request logs, trusted hosts, restricted CORS, security headers and rate limiting
- Database transactions and row locking for allocation, capacity, payment and workflow changes
- Participant checks for quotes, bookings, chat, reviews and disputes
- Payment success only after verified provider evidence; no full card storage
- Private object-storage architecture with signed URLs for sensitive documents
- Immutable financial, quotation, booking, cancellation and audit snapshots

## Required before public launch

Commission an independent penetration test and Indian privacy/legal review. Configure production secrets in a managed secret store, TLS at the load balancer, restricted database networking, encrypted backups, alerting, dependency scanning and tested disaster recovery. Rotate any credential suspected of exposure.

Report suspected vulnerabilities privately to the platform administrators. Do not include Aadhaar, payment credentials or other sensitive personal data in an ordinary support message.
