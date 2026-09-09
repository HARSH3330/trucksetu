param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^https?://')]
    [string]$BaseUrl
)

$ErrorActionPreference = 'Stop'
$base = $BaseUrl.TrimEnd('/')
$failed = $false

foreach ($path in @('/health/live', '/health', '/health/ready', '/version', '/openapi.json')) {
    try {
        $response = Invoke-WebRequest -Uri "$base$path" -UseBasicParsing -TimeoutSec 20
        Write-Host ("{0,-20} {1}" -f $path, [int]$response.StatusCode)
    }
    catch {
        $status = 'NO_RESPONSE'
        if ($_.Exception.Response -and $_.Exception.Response.StatusCode) {
            $status = [int]$_.Exception.Response.StatusCode
        }
        Write-Host ("{0,-20} {1}" -f $path, $status)
        $failed = $true
    }
}

if ($failed) {
    throw 'One or more API smoke checks failed. Review runtime logs; no secrets were printed.'
}
