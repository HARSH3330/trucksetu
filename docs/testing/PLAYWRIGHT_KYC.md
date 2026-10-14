# TransivoX KYC Playwright tests

The default suite drives the real React and FastAPI KYC flow while replacing only S3/GuardDuty with a local test adapter. It resets **only** a PostgreSQL database named exactly `transivox_e2e`. It never falls back to the normal application database.

## Windows prerequisites

Install PostgreSQL 16 (including `psql`), Node.js, and Python 3.12. Run the following from PowerShell. Replace the password shown here with a dedicated local test password; do not reuse a production password.

```powershell
$env:Path += ";C:\Program Files\PostgreSQL\16\bin"
psql -U postgres -h 127.0.0.1 -d postgres -c "CREATE ROLE transivox_e2e_user LOGIN PASSWORD 'choose-a-local-test-password' NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;"
psql -U postgres -h 127.0.0.1 -d postgres -c "CREATE DATABASE transivox_e2e OWNER transivox_e2e_user;"
```

If the role or database already exists, do not recreate it. Confirm that the account cannot create databases or roles and owns the isolated database:

```powershell
psql -U postgres -h 127.0.0.1 -d postgres -c "\du transivox_e2e_user"
psql -U postgres -h 127.0.0.1 -d postgres -c "\l transivox_e2e"
```

## Install dependencies

```powershell
npm ci
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install . pytest pytest-asyncio
npx playwright install chromium
```

If activation is blocked, first run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.

## Required local variables

```powershell
$env:E2E_DATABASE_URL = "postgresql://transivox_e2e_user:choose-a-local-test-password@127.0.0.1:5432/transivox_e2e"
$env:E2E_ALLOWED_DATABASE_HOSTS = "127.0.0.1,localhost"
$env:E2E_WEB_URL = "http://127.0.0.1:5173"
$env:E2E_API_URL = "http://127.0.0.1:8000/api/v1"
$env:E2E_PYTHON = (Resolve-Path ".\.venv\Scripts\python.exe").Path
$env:E2E_CONTROL_TOKEN = "local-e2e-control-token-change-me"
$env:E2E_PROVIDER_EMAIL = "provider.e2e@example.com"
$env:E2E_PROVIDER_PASSWORD = "ProviderE2E123!"
$env:E2E_ADMIN_EMAIL = "admin.e2e@example.com"
$env:E2E_ADMIN_PASSWORD = "AdminE2E123!Secure"
$env:E2E_REAL_AWS = "false"
```

The setup fails before a database command unless the parsed database name is exactly `transivox_e2e`, the host is an exact member of `E2E_ALLOWED_DATABASE_HOSTS`, and local test mode is active. The Python destructive boundary repeats the same checks.

## Run and report

```powershell
npm run e2e:kyc
npm run e2e:kyc:report
```

`npm run e2e` is an alias for the local Chromium KYC journey. Run the real
async PostgreSQL serialization regression after setup has migrated the dedicated
database, using the same PowerShell session and connection variables:

```powershell
$env:APP_ENV = "test"
$env:TRANSIVOX_E2E = "true"
$env:E2E_REAL_AWS = "false"
$env:PYTHONPATH = "backend"
& $env:E2E_PYTHON -m pytest backend/tests/integration/test_kyc_serialization.py -q -p no:cacheprovider
```

This regression rolls back its own fixture data; it never resets the schema.
The default seed and browser login accounts use `provider.e2e@example.com` and
`admin.e2e@example.com`. Keep both configurable with the variables above.
Failed browser API responses report route, method, HTTP status and validation
field/type only; response values, bodies, headers and query strings are redacted.
Custom provider/admin sessions save screenshots and traces on failure. Treat all
local reports as private test artifacts and never use real identity documents.

The run resets the isolated schema, applies real Alembic migrations, seeds dedicated provider/admin accounts, starts the test API and Vite, and runs Chromium. Failure artifacts are under `test-results`; the HTML report is under `playwright-report`.

Optional cross-browser run:

```powershell
npx playwright install firefox webkit
npm run e2e:kyc:cross-browser
```

## Real AWS/GuardDuty check (explicit opt-in)

This mode does not reset or migrate a database. It must target an isolated non-production staging environment with a fresh dedicated provider account.

```powershell
$env:E2E_REAL_AWS = "true"
$env:E2E_MANAGE_SERVERS = "false"
$env:E2E_AWS_SCAN_TIMEOUT_MS = "180000"
npm run e2e:kyc:aws
```

The AWS test uses the real presigned S3 URL and waits for GuardDuty. Local green tests prove only application handling of simulated statuses; they do not prove S3, bucket CORS, IAM, event delivery, or GuardDuty configuration.
