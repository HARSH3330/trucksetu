# Private scanner deployment proposal — not applied

23 October 2026. No AWS writes, deployment, paid activation, notifications/policy changes or production E2E. Target only the owner-confirmed personal account and transivox-kyc-harsh3330 in ap-south-1. No employer resources may be inspected/reused beyond an initial identity check; abort account mismatch.

## Verified access and storage

Tool discovery exposed no AWS S3/IAM/STS connector in this chat. Plugin search returned only an uninstalled AWS Data Analytics plugin, not the required storage/IAM controls. A bounded default-chain boto3 STS request returned NoCredentialsError. Therefore account, caller, bucket location/versioning/encryption/public-access block/CORS, upload principal, notifications, deployed scanner resources and free-tier eligibility remain UNVERIFIED. Application runtime credentials are a separate requirement from plugin access. Never paste keys into chat.

Restore the intended AWS connection in Codex Settings/Plugins, enable it for this chat, reconnect the owner's personal account if requested, then refresh tool availability. If no S3/IAM tools appear, use an owner-approved local AWS SSO/profile; do not copy an employer profile. The prepared verify_access.py requires --expected-account and optional --application-role, performs reads only, asserts STS account and bucket owner, and reports denied checks explicitly. Attached managed policy contents, permission boundaries, SCPs, resource policies and any KMS grants still require effective-permission review before approval. No application role was guessed.

## Recommended architecture

Private versioned upload -> prefix-filtered S3 notification -> SSE-SQS -> one nonroot ClamAV ECS/Fargate worker -> separate SSE/private versioned result bucket -> API reads trusted evidence. The container exposes no ports: clamd listens only on a mode-600 Unix socket. Public IPv4 is for outbound HTTPS only; security group has no inbound rules. No load balancer or NAT gateway. A dedicated VPC/subnet/route avoids employer/shared networking. Egress 443 reaches AWS APIs, image storage and official ClamAV definitions. If policy requires zero public IP, price NAT/interface endpoints and an approved signature mirror separately; do not silently add them.

The worker uses 2 vCPU/4 GB, 20 GB included ephemeral storage, one scan at a time, a private Unix daemon to avoid reloading signatures for every document, 10 MB input, 40 MB expansion, 100 embedded files, recursion 8, 45-second engine scan budget, 120-second request / 180-second parser+scan wall-clock limits. Malformed/encrypted/unsupported/limited files remain non-clean. Temporary files are deleted. Logs contain curated events/status only, not document names, keys, contents, URLs or raw errors.

Definitions refresh at startup and every 12 hours; loaded daemon evidence must be no older than 48 hours. Errors prevent receipt deletion/clean attestation. SQS visibility 600 seconds, maxReceiveCount 5, encrypted DLQ retention 14 days. Immutable conditional result writes make duplicate and out-of-order jobs harmless; replacement object versions have different identities. Permanent non-clean verdicts require a corrected new version; no force-clean overwrite. Scanner heartbeat health check and queue-age/DLQ alarms detect outage. SNS subscriber/on-call owner must be approved and confirmed; an unsubscribed topic does not deliver an alert.

## Resources proposed

scanner-stack.proposed.json creates a dedicated VPC, subnet, internet gateway/route table, no-ingress security group, private result bucket+policy, SQS/DLQ+source-scoped queue policy, ECS cluster/task/service, worker/execution roles, 14-day CloudWatch log group, SNS topic and queue/DLQ alarms. DesiredCount defaults to zero. An owner-scoped private ECR repository/image push and retention policy are additional approved release actions; ImageDigest and ImageRepositoryArn are required parameters. Source bucket is not managed/replaced by the stack. Stack results are retained on deletion. Review disposal/retention requirements before any real identity data.

Merge api-result-reader-policy.proposed.json into the actual backend principal after inspecting existing grants. API may read result objects but must not write/delete results or change scan tags. Worker can read only source kyc/ exact versions, write only result prefix, consume only its queue; no DB access, public endpoint, payment/messaging credentials, source upload/delete rights or secrets are needed. Execution role pulls only the approved image and writes only its log group. Keep API keys in the approved secret store; use ECS task roles for worker credentials, never static keys in the image.

notification-fragment.proposed.json is a MERGE fragment, not a replacement request. Read and preserve existing queue/Lambda/topic/EventBridge notifications and detect overlapping prefix/event conflicts first. Do not apply any full put-bucket-notification configuration until the exact merged diff is approved. Existing CORS/policies/versioning/encryption must be inspected, not overwritten from templates.

## Cost estimate and assumptions

AWS public Mumbai AmazonECS price feed fetched 23 October 2026, publicationDate 2026-10-19T22:43:17Z: x86 CPU US$0.04256/vCPU-hour, memory US$0.004655/GB-hour. At 730 hours/month: (2*0.04256+4*0.004655)*730 = US$75.7302 compute. One public IPv4 at US$0.005/hour adds US$3.65, giving US$79.38 base. No NAT gateway in this design. Assumes one continuously running task; deployment max100/min0 avoids a second task but causes a short queueing interruption during replacement.

Allow an additional provisional US$3-10/month for small-volume SQS/S3/results/ECR/logs/alarms/SNS, giving a planning envelope around US$83-90/month before tax, exchange rate, data-transfer spikes or larger retention. This is a budget allowance, not a verified line-item quote. S3 requests/storage scale with each version and result; queue retries and scans consume runtime. Internet transfer and signature/image downloads vary; confirm AWS Calculator ap-south-1 quote before approval. No free tier/credit eligibility is assumed or verified.

Lambda alternative: 4 GB x86, 1 GB /tmp, reserved concurrency1, 900-second timeout and SQS partial-batch handling could reduce idle compute. At 1,000 scans/month and 30-120 billed seconds/scan, 120,000-480,000 GB-seconds is approximately US$2-8 at an illustrative US$0.0000166667/GB-second, excluding requests/storage/other costs; regional quote and measured cold-start/signature-update time are still needed. The current poller is not a Lambda handler. Do not deploy it as one. Private EFS/signature mirror adds networking/storage cost. Choose this alternative only after implementing/benchmarking the handler, cached-signature freshness and retries. A small VM is another option but transfers OS patching/backups/availability duties to the owner.

Create an explicitly approved monthly budget (suggested review threshold US$90, owner must choose), actual/forecast alerts at 50/80/100 percent, and scan/queue/definition-age alarms. Budget alerts are NOT a hard spending cap. No account upgrades, GuardDuty enablement or paid services are authorized by this proposal.

Sources: https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonECS/current/ap-south-1/index.json ; https://aws.amazon.com/fargate/pricing/ ; https://aws.amazon.com/vpc/pricing/ ; https://docs.clamav.net/Introduction.html ; https://docs.clamav.net/manual/Usage/Scanning.html ; https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html ; https://aws.amazon.com/lambda/pricing/ .

## Deployment order after separate approval

1. Confirm personal account, bucket owner/region and actual runtime principal; read effective IAM, versioning, encryption, public block, CORS and notification configuration. Confirm account services/quotas/billing eligibility. Stop mismatches. Approve exact cost/budget, networking and policy diffs.
2. Validate CloudFormation with AWS validate-template/change-set plus IAM/security review. Local JSON parsing alone is not service validation. Build/push the reviewed scanner image to approved private ECR and pin digest. Create reviewed resources with desired count zero; attach result read/anti-forgery policy only to the intended API principal.
3. Deploy isolated preview API/DB/storage/scanner first. Apply additive migrations through 27 exactly once. Keep real checkout disabled, scanner/provider/configuration fail closed, customer policy unset until reviewed.
4. Approve and merge the non-overwriting upload notification patch. Start one worker; require fresh daemon evidence/healthy heartbeat, empty DLQ, working alerts. Test a harmless designated upload. Never upload EICAR into production. Local EICAR is sufficient for engine detection; an approved isolated staging EICAR check would be a separate action.
5. Designated fictional website account uploads harmless document -> scanner reads exact S3 VersionId -> immutable result -> backend finalization -> authorized admin reviews every required document -> customer/provider eligibility updates. Test unauthorized access, pending/error state, replacement version, role isolation and no public read. Record app source SHA, image digest, versions and result identity without document contents.
6. Production scanner remains blocked until that real workflow is verified. Apply separately approved production migration/API/frontend plan; do not enable live payment collection during scanner activation.

## Historical versions and recovery

Enabling notifications does not scan old objects. Query recorded bucket/key/storage_version_id metadata from provider, vehicle and customer documents in a protected operator export; include pending registered evidence and any separately recorded unfinished upload. Do not export document contents or identifiers. prepare_backfill.py creates deduplicated S3-shaped jobs without sending anything. Review manifest/counts, then separately approve SQS sends under an operator-only scoped identity. Missing/null VersionId means resubmission, never scan latest as a substitute. Existing terminal non-clean evidence requires corrected reupload, not overwrite.

On outage leave uploads private and all KYC gates blocked; inspect heartbeat/definitions/IAM/DLQ using metadata only. Fix cause, review affected jobs and approve bounded redrive. Do not purge queues, overwrite results or downgrade clean requirements. Retain results/history. Roll back to a compatible API/image with scanner disabled if needed; disabling means blocked KYC, not clean. Never switch to GuardDuty unless an actual approved scanner exists.

Subsequent fee-policy implementation adds migration27 after26; use the current exact release plan and keep all live payment/refund actions blocked.

Optional template budget alerts use an account-wide monthly cost budget (not a scanner-only hard cap). BudgetLimitUSD=0 and AlertEmail empty create no budget/subscription; owner must approve both values, and SNS email subscriptions require confirmation. Account eligibility/permissions and service validation remain unverified.
