# Actual website integration settings — 26 October 2026

Status: PREPARATION ONLY. Keep draft PR1 blocked. Existing values inspected by metadata; sensitive Vercel values cannot be compared with tested private values, so do not overwrite them blindly. No application deployment is authorized. Read the recovery-isolation incident before any database action.

## Frontend project trucksetu-whri → Production

| Variable | Inspected state | Required action |
|---|---|---|
| VITE_GOOGLE_MAPS_BROWSER_KEY | Missing | Privately add a production browser key; never use server/service credentials |
| VITE_GOOGLE_MAPS_MAP_ID | Missing | Add project-owned JavaScript Map ID; DEMO_MAP_ID is local only |
| VITE_API_URL | Present, sensitive value not readable | Verify privately: https://trucksetu-api-nine.vercel.app/api/v1; change only if different |

Google Cloud: Website/HTTP-referrer restrictions https://www.transivox.in/*; add https://transivox.in/* only if it serves the app rather than merely redirecting. API allowlist Maps JavaScript API and Places API(New). No Routes API needed or enabled. Use a separate local key for actual localhost origins; do not wildcard all vercel.app previews. API enablement/billing/restriction evidence and owned Map ID remain owner actions. VITE changes require a separately approved frontend rebuild/deployment; saving variables alone does not change the website.

## Backend project trucksetu-api → Production

| Variable | Inspected state / required value |
|---|---|
| SMTP_HOST | Present; privately verify smtp-relay.brevo.com |
| SMTP_PORT | Present; privately verify587/STARTTLS |
| SMTP_USERNAME | Present; retain matching Brevo SMTP Login privately |
| SMTP_PASSWORD | Present; retain matching Brevo SMTP key privately |
| EMAIL_FROM | Present; requested noreply@transivox.in confirmed ACTIVE in Brevo sender API |
| EMAIL_REPLY_TO | Missing/optional; leave blank unless a monitored mailbox is approved |
| PUBLIC_FRONTEND_URL | Prepared as https://www.transivox.in; not deployed |
| RAZORPAY_KEY_ID | Present; existing production mode unreadable. Live activation would require matching intended merchant rzp_live key; do not replace verified local rzp_test credentials |
| RAZORPAY_KEY_SECRET | Present; must match intended mode/key privately before any future live approval |
| RAZORPAY_WEBHOOK_SECRET | Present; dedicated secret must match the same mode's webhook, not the API secret |
| ENABLE_REAL_CONNECTION_CHECKOUT | Explicit false safety gate prepared; keep false |
| ENABLE_RAZORPAY_SANDBOX | Explicit false in Production; local Test Mode stays separate |
| CONNECTION_FEE_TAX_CONFIRMED | Explicit false; do not assert approval from research |
| DATABASE_URL / MIGRATION_DATABASE_URL | Present; preserve original production binding. Runtime pooled/direct migration separation and private runtime-to-branch verification still required. Never copy local/preview URI into Production |
| ALLOWED_ORIGINS | Present; privately verify https://www.transivox.in, plus apex only if served |
| AUTH_COOKIE_SAMESITE | Source default none; explicit cross-site API deployment requires none with Secure/HttpOnly/HTTPS. Do not relax CSRF |
| APP_ENV / DEBUG / TRUSTED_HOSTS / SECRET_KEY | Preserve existing values; verify production/false/exact API host/strong private secret before deployment |

Email uses BREVO SMTP; Gmail is only the designated recipient mailbox. Brevo read-only account API confirms transactional relay enabled; requested sender active. No new mail sent. Local587STARTTLS/auth evidence is retained; this does not prove sensitive production SMTP credentials match it. Receiving/reply mailboxes are separate from SMTP sending; no new mailbox or DNS change performed.

## Correct future connection-fee webhook

After separately approved matching API release, single URL:
https://trucksetu-api-nine.vercel.app/api/v1/connection-fees/webhook

Supported events: payment.captured, payment.failed, refund.created, refund.processed, refund.failed, payment.dispute.created. This differs from the retained legacy payments webhook. Do not edit another integration's webhook blindly or enable Live checkout now. Ensure raw-body signature validation and Razorpay event-ID header survive transport. Current serving old API may not expose this handler yet; saving the URL is not a successful delivery test.

## Intended price / tax units

The customer TOTAL remains INR99 =9900paise. Gateway orders convert validated rupee policy totals to paise; never set a rupee amount variable to9900. CONNECTION_FEE_POLICY is structured JSON with amount/tax_amount/tax_treatment and approved terms/version. For an approved tax-inclusive policy, amount99.00 with tax_treatment=included keeps total99; tax_amount still needs approved allocation. CONNECTION_FEE_AMOUNT is a RUPEE base in the proposed fallback, not gateway paise; CONNECTION_FEE_TAX_RATE is a fraction, not20or18.

Research: official GST Council services schedule lists residual support services under9985at18percent, not20percent. This is a CANDIDATE classification only; Transivox's exact SAC, GST registration/applicability, place of supply, invoice requirements and waived-fee treatment need qualified confirmation. If18percent applies within99, illustrative rounded taxable value83.90and tax15.10total99; do not configure this as confirmed production tax automatically. Do not enable old1200fallback or invent zero tax. Keep checkout blocked until a matching approved policy is recorded. Source: https://www.gstcouncil.gov.in/sites/default/files/2024-02/gstservicerates.pdf (published schedule; later amendments/applicability require review).

## KYC/scanner and recovery

Existing AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_S3_BUCKET, AWS_REGION and AWS_S3_KYC_PREFIX entries are present but values/readiness unverified. Missing scanner/customer-policy settings include KYC_SCAN_PROVIDER, KYC_SCAN_RESULTS_BUCKET, CUSTOMER_KYC_REQUIRED_DOCUMENTS, CUSTOMER_KYC_POLICY_VERSION and CUSTOMER_KYC_CONSENT_TEXT. Use reviewed scanner architecture and consent/retention only, exact-VersionId clean scanning plus manual review, CUSTOMER_KYC_TEST_SIMULATION=false. Local AWS credentials/profiles unavailable. Do not turn on GuardDuty/paid resources or publication to bypass this.

No branch is currently protected. Neon Free does not include protected branches; deleting old unused branches cannot create that entitlement. Preserve original, fresh snapshot and incident copies; old15October recovery copies have not been retired because incident reconciliation is incomplete. No upgrade/deletion performed. Official plan reference: https://github.com/neondatabase/website/blob/main/content/docs/introduction/plans.md . A separate no-upgrade encrypted/exported recovery design needs review; the failed protection request is not a protected backup.

## Latest actual payment/browser evidence

Owner reported yesterday's payment/refund journey without IDs. Bounded GET-only Test merchant query for25October IST recovered one1200captured payment pay_Ts2uOdSiLQ370Z with zero refunds, and two failed1200payments including refund-purpose checkout pay_Ts2vf4p8kHTihw. Both fresh99orders order_TsMz68U269CDhW/order_TsMzAGzBpgt6gz have zero payments. Thus99capture/fullrefund is BLOCKED, not PASS; no external mutation made during reconciliation. Saved local callbacks agree: old capture and failed refund-purpose checkout. No need to ask owner for credentials/IDs again; fresh controlled99interaction is still needed after local services are ready.

Latest CI d4efac5: main CI PASS; legacy/session/shared/vehicle browser8PASS, customer/fee/session6PASS, two missing-policy browser cases FAIL only because they expected status role while current accessible error is alert. Corrected role assertion preserves heading/no-start-button/mobile checks and server publication gates; new browser run is required before PASS. Remaining dedicated suites were skipped after the failure, not passed.
