# Private documents: proposed AWS changes, not applied

Known target: `transivox-kyc-harsh3330`, `ap-south-1`, `kyc/`. Current session has
neither a usable AWS Core tool nor application AWS keys/bucket configuration.
No current AWS IAM/CORS/scanner read was possible. Do not overwrite existing
policies based on these examples; inspect/merge the exact reviewed diff first.

## Current application contract

Provider KYC and vehicle routes use `PrivateDocumentStorage`. After upload the
server captures a non-null immutable VersionId; signature detection, clean-tag
lookup and signed download bind to that exact version. Only
`GuardDutyMalwareScanStatus=NO_THREATS_FOUND` permits registration/review/download.
Missing tags, THREATS_FOUND, UNSUPPORTED, ACCESS_DENIED, FAILED and service errors
remain blocked. No browser API can write a clean result.

The API reads `AWS_S3_BUCKET`, `AWS_REGION`, `AWS_ACCESS_KEY_ID`,
`AWS_SECRET_ACCESS_KEY`; key values are backend-only. Provider and vehicle files
stay private; no public bucket policy, wildcard CORS or ACL is proposed.

## Proposed deployment diff requiring separate approval

1. Inspect the actual application principal and bucket: block-public-access,
   owner-enforced ownership, SSE-S3, Versioning Enabled, merged CORS and policies.
2. Merge `ops/aws/application-document-policy.example.json` into only the API
   identity. Explicit deny of tag mutation prevents that identity/presigned
   clients forging scan proof. It is NOT a bucket-wide deny against GuardDuty.
   Audit other writers/grants too: a broad unrelated IAM grant must not enable
   a client to tag objects. Do not attach this API deny to the scanner role.
3. Review `document-cors.example.json` for the two actual production origins.
   Add staging only after its isolated API/database binding is approved. Do not
   add arbitrary Vercel origins. PUT signs Content-Type and AES256 encryption;
   no client tag header is permitted. Signed downloads open server-authorized
   URLs in a separate tab and do not require public GET CORS.
4. Create a separate scanner role using the trust/policy examples, substitute
   the privately checked account ID, and review confused-deputy restrictions
   supported by GuardDuty before activation. S3 reads/tags are limited to kyc/;
   the exact validation-object write is the service setup exception. ListBucket
   is service validation for this bucket only, never ListAllMyBuckets. No KMS
   grants are proposed because the confirmed design is SSE-S3.
5. Create the plan from `scanner-plan.example.json` in ap-south-1 with tagging
   ENABLED and only kyc/. Enabling it changes bucket/EventBridge configuration
   and can create a validation object: this requires explicit approval.
6. Connect reviewed alerts for nonclean results, plan Warning/Error and tag
   write failures. The supplied scan-result pattern is only a template, not a
   deployed alert. Target, permissions, retention and on-call owner are missing.

## Events, retries and timeouts

No new public callback writes document status. GuardDuty writes authoritative
version tags; the API rechecks them. Duplicate/out-of-order EventBridge messages
must not accept documents or update the latest key without a VersionId. An old
version becoming clean cannot authorize a newer version. Result events are for
monitoring only; exclude original filenames, keys, signed URLs and full event
payloads from alert bodies. Use event ID, status, counts and restricted operator
correlation. Dedupe alerts by bucket/version/event reference in the chosen alert
platform, not by accepting client claims.

No tag after 15 minutes: alert operations and keep blocked; this is a proposed
operational threshold, not an auto-clean timeout. Operator checks plan state,
version read/tag permissions and scan metrics. Re-upload a corrected harmless
file if required; never fabricate a clean tag. Errors and tag failures must page
the owner even if the scan-result event itself indicated clean.

## Cost and account-plan decision

AWS documents standalone Malware Protection for S3 without full GuardDuty.
Eligibility under this particular account's Free plan is NOT verified. Ask AWS
to confirm whether a paid-plan upgrade is required. Monthly cost basis is scanned
GB plus objects evaluated, S3 requests/tagging/storage and selected monitoring
targets. The documented allowance is 1GB/1,000 requests per month; do not promise
zero cost or apply another region's rate to Mumbai. Obtain the ap-south-1 quote
and a budget ceiling before approval. Alternative managed/self-hosted scanners
require an authenticated exact-version attestation design, patching, isolation
and ongoing costs; they are not a config-only replacement for this tag contract.

Sources (checked 20 October 2026):
- [AWS role permissions](https://docs.aws.amazon.com/guardduty/latest/ug/malware-protection-s3-iam-policy-prerequisite.html)
- [Standalone scanner and tags](https://docs.aws.amazon.com/guardduty/latest/ug/gdu-malware-protection-s3.html)
- [Scan events](https://docs.aws.amazon.com/guardduty/latest/ug/monitor-with-eventbridge-s3-malware-protection.html)
- [Usage/pricing](https://docs.aws.amazon.com/guardduty/latest/ug/pricing-malware-protection-for-s3-guardduty.html)

## Controlled website verification after approval

Use designated fictional provider/admin accounts and a marked harmless PDF, not
real identity data. Record only test record IDs and object/version references in
a restricted cleanup ledger. Confirm browser direct upload succeeds, VersionId
is retained, public requests fail, other providers cannot obtain URLs, missing
scan blocks registration, actual scan completion gates registration, every
required current document needs manual acceptance, and approval persists through
reload. Repeat for all five vehicle files (RC, insurance, fitness, pollution,
permit), reject/replace one and verify history. No scanner => no real approval.
Historical standalone S3 checks are not repeated or confused with website proof.
