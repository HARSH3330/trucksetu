# S3 document-storage probe — 14 October 2026

## Actual result in this workspace

Local process environment has no AWS access key/secret/session token/profile, and the SDK finds no credentials. Default local AWS credentials/config files are absent. No application principal was authenticated. Vercel variables are not available locally. No credentials, signed URLs, document contents or cloud account identifiers were printed.

The default target preflight initially refused missing bucket configuration. A second **no-write** preflight supplied only the confirmed nonsecret `AWS_S3_BUCKET=transivox-kyc-harsh3330` and `AWS_REGION=ap-south-1` and returned:

`BLOCKED — NoCredentials: no local application credentials available`

No S3 object was created; retained keys/version IDs: **none**.

| Check | Actual status | Evidence/limitation |
|---|---|---|
| Local credential availability | BLOCKED | SDK source `none`; no authenticated AWS principal |
| Real harmless signed upload | BLOCKED | No credentials; not executed |
| Returned non-null VersionId | BLOCKED | No real upload |
| Exact-version SSE-S3/AES256 metadata | BLOCKED | No real object inspected |
| Exact-version tag read | BLOCKED | Not executed against S3 |
| Unsigned GET denied | BLOCKED | No real object request |
| Unique-key overwrite/original bytes preserved | BLOCKED | No real writes/version reads |
| Actual object's missing/nonclean scan gate | BLOCKED | Real S3 tag read unavailable; no clean tag created |
| Real application registration/approval/download authorization | BLOCKED | No live API sessions or DB records used/changed |
| Successful scan/full KYC approval | BLOCKED | Scanner unavailable; enforcement remains enabled |

Local fake-storage regression results are separate evidence, not AWS verification. The existing routes reject missing/nonclean scan evidence and unversioned files in local tests; this does not prove the deployed application has the same build/configuration or IAM grants.

## Secure local execution

Open a **new PowerShell window** in the repository. Use the same least-privilege application identity configured on the API, not AWS root credentials. Enter values privately through masked prompts; never paste them in chat. This standalone probe does not reset a database, use E2E scan controls or change the Vercel configuration.

```powershell
cd 'C:\Users\harsh\OneDrive\Desktop\english learning\logistic\trucksetu'
$env:PYTHONPATH='backend'
$env:APP_ENV='test'
$env:AWS_S3_BUCKET='transivox-kyc-harsh3330'
$env:AWS_REGION='ap-south-1'
$keyInput=Read-Host 'Application AWS access key ID (private)' -AsSecureString
$secretInput=Read-Host 'Application AWS secret access key (private)' -AsSecureString
try {
  $env:AWS_ACCESS_KEY_ID=[Net.NetworkCredential]::new('', $keyInput).Password
  $env:AWS_SECRET_ACCESS_KEY=[Net.NetworkCredential]::new('', $secretInput).Password
  $keyInput=$null; $secretInput=$null
  & .\.venv\Scripts\python.exe -m s3_integration_check --run
} finally {
  Remove-Item Env:AWS_ACCESS_KEY_ID,Env:AWS_SECRET_ACCESS_KEY -ErrorAction SilentlyContinue
  $keyInput=$null; $secretInput=$null
}
```

`--run` checks credentials and the exact target before writing anything. It exits nonzero while application/scanner checks remain blocked: that is an honest incomplete integration result, not necessarily failed S3 operations. Read the individual JSON PASS/FAIL/BLOCKED checks. Omitting `--run` performs preflight only and never creates objects.

If using an already configured SDK profile instead of explicit keys, leave the API's explicit key settings empty. The current adapter does not explicitly pass `AWS_SESSION_TOKEN` when access/secret keys are supplied; do not assume temporary-token support through those explicit settings. No additional IAM grants are requested here.

## Runner boundaries

`backend/s3_integration_check.py --run` creates one random key under `kyc/test/` and uploads two tiny harmless versions. The PDF is visibly marked TEST DOCUMENT — NOT A REAL ID. It uses `PrivateDocumentStorage`'s configured client and confirmation/signature/tag/scan methods. Signed PUT generation uses that same client directly to enforce the test prefix rather than manufacture a provider-id key. It never uses a production provider or vehicle record.

It checks returned PUT VersionIds, exact-version encryption, exact-version tag access, the adapter's real missing/nonclean scan refusal, anonymous GET denial and original-version byte preservation after overwrite. It does not write any tags or delete objects. The JSON report includes only allowed test keys/version IDs for later cleanup. A failure after upload can leave retained versions, which is intentional. It never prints a signed URL or raw provider error body.

Direct `get_object(VersionId=...)` is explicitly labelled storage-level evidence. Actual application registration, approval and download authorization remain BLOCKED without separate authenticated API/database verification. No scanner is simulated against the real bucket. If the test object unexpectedly has a clean scan tag, the runner refuses to claim missing-scan verification.
