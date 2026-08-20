param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$resolved=[System.IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Force -Path $resolved | Out-Null
$stamp=Get-Date -Format 'yyyyMMdd-HHmmss'
$target=Join-Path $resolved "trucksetu-$stamp.dump"
docker compose exec -T postgres pg_dump -U trucksetu -Fc trucksetu --file=/tmp/trucksetu-backup.dump
if ($LASTEXITCODE -ne 0) { throw "Database backup failed" }
docker compose cp postgres:/tmp/trucksetu-backup.dump $target
if ($LASTEXITCODE -ne 0) { throw "Could not copy database backup" }
Write-Output $target
