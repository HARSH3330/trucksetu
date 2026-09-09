# Deployment and recovery

Use independent local, staging and production environments. Production should use managed PostgreSQL, Redis and private S3-compatible storage with TLS and least-privilege service identities.

The CI workflow builds the web application, runs database migrations against disposable PostgreSQL, performs lint/type/test gates and builds containers only after those checks pass.

Before deployment:

1. Set `APP_ENV=production`, `DEBUG=false`, a long random `SECRET_KEY`, trusted hosts and explicit CORS origins.
2. Configure database, Redis, private storage, payment webhook, maps and selected communication credentials.
3. Run `alembic upgrade head` as a one-off release task.
4. Confirm `/health/live`, `/health`, `/health/ready`, `/version`, and `/openapi.json` with `scripts/smoke-api.ps1`.
   `/health/ready` reports PostgreSQL and Redis independently and returns a controlled 503 when required infrastructure is unavailable.
5. Run smoke tests for signup, KYC authorization, quote allocation, OTP, payments and capacity concurrency.

Back up PostgreSQL on a schedule with `scripts/backup-postgres.ps1`, encrypt the backup, copy it to a separate account or region and apply retention rules. Test restoration regularly. A backup that has never been restored is not considered verified.

Roll back containers to the prior immutable image when needed. Database migrations require an explicitly reviewed downgrade or forward-fix; never automatically destroy production data.

## Vercel environment format

List settings use comma-separated values (not JSON), for example:

```text
ALLOWED_ORIGINS=https://app.example.com,https://preview.example.com
TRUSTED_HOSTS=api.example.com,*.vercel.app
PILOT_DESTINATION_CITIES=Delhi,Gurugram,Noida
```

Set `REDIS_REQUIRED=true` for the closed pilot after managed Redis is connected. Keep it false only for liveness-only deployments where Redis-backed pilot operations are disabled.

## Database migration release step

Run migrations once, before directing traffic to a new API build:

```powershell
cd backend
python -m alembic -c alembic.ini upgrade head
```

Do not run Alembic during application startup or from every serverless instance. Before release, run `scripts/check-migrations.ps1` to verify that the history has one head and a clean PostgreSQL upgrade compiles without connecting to the configured database. Create a Neon restore point or branch before upgrading an existing environment.

## Private KYC storage

Use a private S3 bucket with public access blocked, object encryption enabled, versioning, access logging and a restricted application identity. Upload and download links expire after 10 and 5 minutes respectively. The API checks the object size, declared type and file signature before registering a document. Manual reviewers must accept every required, unexpired document before verification. Add bucket malware scanning and quarantine before expanding beyond the closed pilot.
