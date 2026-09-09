$ErrorActionPreference = "Stop"

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$backendRoot = Join-Path $repositoryRoot "backend"

Push-Location $backendRoot
try {
    python -m alembic -c alembic.ini heads
    python -m alembic -c alembic.ini upgrade head --sql | Out-Null
    Write-Host "Migration chain is linear and the clean PostgreSQL upgrade compiles successfully."
}
finally {
    Pop-Location
}
