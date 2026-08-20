# Deployment and recovery

Use independent local, staging and production environments. Production should use managed PostgreSQL, Redis and private S3-compatible storage with TLS and least-privilege service identities.

The CI workflow builds the web application, runs database migrations against disposable PostgreSQL, performs lint/type/test gates and builds containers only after those checks pass.

Before deployment:

1. Set `APP_ENV=production`, `DEBUG=false`, a long random `SECRET_KEY`, trusted hosts and explicit CORS origins.
2. Configure database, Redis, private storage, payment webhook, maps and selected communication credentials.
3. Run `alembic upgrade head` as a one-off release task.
4. Confirm `/health` and `/ready`; `/ready` must verify PostgreSQL and Redis.
5. Run smoke tests for signup, KYC authorization, quote allocation, OTP, payments and capacity concurrency.

Back up PostgreSQL on a schedule with `scripts/backup-postgres.ps1`, encrypt the backup, copy it to a separate account or region and apply retention rules. Test restoration regularly. A backup that has never been restored is not considered verified.

Roll back containers to the prior immutable image when needed. Database migrations require an explicitly reviewed downgrade or forward-fix; never automatically destroy production data.
