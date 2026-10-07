param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^https://')]
    [string]$ApiBase,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[^@\s]+@[^@\s]+\.[^@\s]+$')]
    [string]$Email
)

$ErrorActionPreference = 'Stop'
$tokenPointer = [IntPtr]::Zero
$passwordPointer = [IntPtr]::Zero
$confirmPointer = [IntPtr]::Zero
$token = $null
$password = $null
$confirmation = $null

try {
    $secureToken = Read-Host 'Temporary ADMIN_BOOTSTRAP_TOKEN' -AsSecureString
    $securePassword = Read-Host 'New administrator password' -AsSecureString
    $confirmPassword = Read-Host 'Confirm administrator password' -AsSecureString

    $tokenPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureToken)
    $passwordPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
    $confirmPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($confirmPassword)
    $token = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($tokenPointer)
    $password = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($passwordPointer)
    $confirmation = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($confirmPointer)

    if ($password -cne $confirmation) {
        throw 'The administrator passwords do not match.'
    }

    $body = @{
        email = $Email
        password = $password
    } | ConvertTo-Json

    $endpoint = "$($ApiBase.TrimEnd('/'))/api/v1/auth/recover-admin"
    $result = Invoke-RestMethod -Uri $endpoint -Method Post -ContentType 'application/json' `
        -Headers @{ 'X-Bootstrap-Token' = $token } -Body $body

    Write-Host "Recovered administrator account for $($result.email)." -ForegroundColor Green
    Write-Host 'All existing refresh sessions were revoked.' -ForegroundColor Green
    Write-Host 'Sign in, then remove ADMIN_BOOTSTRAP_TOKEN from Vercel and redeploy the API.' -ForegroundColor Yellow
}
finally {
    if ($tokenPointer -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($tokenPointer)
    }
    if ($passwordPointer -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($passwordPointer)
    }
    if ($confirmPointer -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($confirmPointer)
    }
    $token = $null
    $password = $null
    $confirmation = $null
}
