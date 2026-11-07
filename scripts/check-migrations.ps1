param([string]$Python = 'python')

$ErrorActionPreference = "Stop"

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$backendRoot = Join-Path $repositoryRoot "backend"

Push-Location $backendRoot
try {
    $heads = & $Python -m alembic -c alembic.ini heads
    if ($LASTEXITCODE -ne 0) { throw 'Alembic head inspection failed; migration check did not pass.' }
    if (@($heads | Where-Object { $_ -match ' \(head\)$' }).Count -ne 1) { throw 'Exactly one migration head is required.' }
    $heads | Write-Output
    & $Python -m alembic -c alembic.ini upgrade head --sql | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Offline migration compilation failed; migration check did not pass.' }
    Write-Host "Migration chain is linear and the clean PostgreSQL upgrade compiles successfully."
}
finally {
    Pop-Location
}
