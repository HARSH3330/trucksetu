param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^https://')]
    [string]$ApiBase,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[^@\s]+@[^@\s]+\.[^@\s]+$')]
    [string]$Email,

    [Parameter(Mandatory = $true)]
    [ValidateLength(2, 120)]
    [string]$FullName
)

$ErrorActionPreference = 'Stop'
$tokenPointer = [IntPtr]::Zero
$passwordPointer = [IntPtr]::Zero
$token = $null
$password = $null

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
        full_name = $FullName
        email = $Email
        password = $password
    } | ConvertTo-Json

    $endpoint = "$($ApiBase.TrimEnd('/'))/api/v1/auth/bootstrap-admin"
    $result = Invoke-RestMethod -Uri $endpoint -Method Post -ContentType 'application/json' `
        -Headers @{ 'X-Bootstrap-Token' = $token } -Body $body

    Write-Host "Created $($result.role) account for $($result.email)." -ForegroundColor Green
    Write-Host 'Now remove ADMIN_BOOTSTRAP_TOKEN from Vercel and redeploy the API.' -ForegroundColor Yellow
}
finally {
    if ($tokenPointer -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($tokenPointer)
    }
    if ($passwordPointer -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($passwordPointer)
    }
    if ($confirmPointer -and $confirmPointer -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($confirmPointer)
    }
    $token = $null
    $password = $null
    $confirmation = $null
}
