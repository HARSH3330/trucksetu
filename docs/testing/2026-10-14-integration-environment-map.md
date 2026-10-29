# Current integration configuration — 14 October 2026

Derived from current source, not existing environment values. No credentials are included. `Frontend` means the Vercel website project; `API` means the separate FastAPI project. Configure Preview with staging/sandbox credentials and Production with only explicitly approved production credentials. Vite public values are baked into the build and require a rebuild; API changes require redeployment. Local tests use isolated fakes and must not send real SMS/email or use real storage/payments.

## Exact variables read

| Integration | Exact variable | Project | Classification | Intended environment/use |
|---|---|---|---|---|
| API boundary | `VITE_API_URL` | Frontend | Public URL | Local: `http://localhost:8000/api/v1`; Preview: approved staging API `/api/v1`; Production: approved production API `/api/v1` |
| Phone ownership widget | `VITE_MSG91_WIDGET_ID` | Frontend | Public widget configuration | Local fake browser tests or approved staging/production widget |
| Phone ownership widget | `VITE_MSG91_WIDGET_TOKEN_AUTH` | Frontend | Public widget-only token, NOT account Authkey | Widget authentication supplied to browser; restrict its allowed origins in MSG91 |
| Phone ownership widget | `MSG91_WIDGET_ENABLED` | API | Nonsecret boolean | `false` for ordinary local tests; `true` only after approved widget configuration |
| Phone verification and trip SMS | `MSG91_AUTH_KEY` | API | Secret account Authkey | Approved staging/production account only; never `VITE_*` |
| Trip OTP delivery | `MSG91_TEMPLATE_ID` | API | Nonsecret template identifier | Approved SMS Flow/DLT template for the operational environment |
| Trip OTP delivery | `MSG91_OTP_VARIABLE` | API | Nonsecret template field name | Default `OTP`; must match the template and be a valid identifier, not `mobiles` |
| OTP validity | `OTP_EXPIRE_MINUTES` | API | Nonsecret integer | Default `10`; trip and account code expiry |
| OTP limits | `OTP_MAX_ATTEMPTS` | API | Nonsecret integer | Default `3`; preserve finite attempt limits |
| OTP issue limit | `OTP_RATE_LIMIT` | API | Nonsecret integer | Default `5`; trip OTP issuance per 600-second window |
| Phone/account verification limit | `VERIFICATION_RATE_LIMIT` | API | Nonsecret integer | Default `10`; phone proof/recovery verification rate controls |
| Account email | `SMTP_HOST` | API | Nonsecret server hostname | Approved SMTP provider for staging/production; local fake sender in tests |
| Account email | `SMTP_PORT` | API | Nonsecret integer | Default `587`; current adapter explicitly uses STARTTLS, not implicit port-465 TLS |
| Account email | `SMTP_USERNAME` | API | Private account/login identifier | SMTP login when configured; not a browser value |
| Account email | `SMTP_PASSWORD` | API | Secret | SMTP password/app password for the selected environment |
| Account email | `EMAIL_FROM` | API | Public sender address | Verified sender address for the selected environment |
| Private storage | `AWS_S3_BUCKET` | API | Nonsecret bucket name | Separate private staging/production bucket; versioning required |
| Private storage | `AWS_REGION` | API | Nonsecret region | Default `ap-south-1`; match the bucket |
| Private storage | `AWS_ACCESS_KEY_ID` | API | Private credential identifier | Least-privilege deployment identity; can be omitted when an appropriate SDK identity is available |
| Private storage | `AWS_SECRET_ACCESS_KEY` | API | Secret | Corresponding credential; never frontend |
| Razorpay | `RAZORPAY_KEY_ID` | API | Public key identifier (returned by order API) | **Test key beginning `rzp_test_`** for sandbox verification; no frontend env key is read |
| Razorpay | `RAZORPAY_KEY_SECRET` | API | Secret | Matching test-mode key secret |
| Razorpay webhook | `RAZORPAY_WEBHOOK_SECRET` | API | Secret, separate from API key secret | The secret selected for the sandbox webhook endpoint |
| Browser/API boundary | `ALLOWED_ORIGINS` | API | Public comma-separated origins | Exact website origins, including approved custom domain; no wildcard |
| Browser refresh cookie | `AUTH_COOKIE_SAMESITE` | API | Public policy setting | `none` for HTTPS cross-site API (may be browser-blocked); prefer same-site API custom domain with `lax`. Local test/development uses non-Secure Lax for HTTP. Cookie is HttpOnly and finite. |
| Browser/API boundary | `TRUSTED_HOSTS` | API | Public comma-separated hostnames | API deployment/custom-domain hostnames |

These are the settings read by these integrations; general application/database/security settings remain required. Boto3 can also use its standard credential-provider chain when explicit access keys are empty; that is SDK behavior, not a new TransivoX configuration field.

## Actual callbacks, endpoints and scan behavior

Use the API **origin**, without a trailing `/api/v1`, when substituting `<API_ORIGIN>` below. Production example is `https://trucksetu-api-nine.vercel.app` only if that remains the intended API deployment; a custom API domain must be approved/configured before using it.

- **MSG91 widget:** scripts load from `https://verify.msg91.com/otp-provider.js`, with fallback `https://verify.phone91.com/otp-provider.js`. `success` is a JavaScript callback, not an inbound webhook. The authenticated browser POSTs the returned proof to `<API_ORIGIN>/api/v1/auth/mobile/verify-widget`; the API verifies it with `https://api.msg91.com/api/v5/widget/verifyAccessToken`. There is **no MSG91 inbound webhook/callback URL** in this implementation. Phone ownership verification does not grant a new role, perform KYC or replace email/password login.
- **Trip OTP:** API POST `/api/v1/trips/{trip_id}/otp/{otp_type}` issues the code (`pickup` or `delivery`); POST `/api/v1/trips/{trip_id}/otp/verify` verifies the submitted `otp_type` and `code`. The SMS adapter sends to `https://control.msg91.com/api/v5/flow/`. **No delivery-report webhook exists**: an accepted provider response is reported as `accepted`, with `delivery_status: unconfirmed`, not confirmed handset delivery.
- **SMTP:** no provider callback/webhook or site-link variable is read. Account recovery emails contain a code/token for the existing recovery UI. No SMTP delivery/bounce webhook exists; SMTP acceptance is not proof the user received the email.
- **S3/scanning:** no scanner API key, scanner URL or scanner-enable variable is read. The API reads the exact-version S3 object tag **`GuardDutyMalwareScanStatus`** and accepts only **`NO_THREATS_FOUND`**. Missing/nonclean results block registration/review/download. GuardDuty tagging must be configured externally for the private, versioned bucket; do not give uploaders permission to set clean-scan tags. **No inbound scan webhook exists**. Uploads use signed S3 PUT URLs (600 seconds), downloads signed GET URLs (300 seconds), not a public bucket URL. Bucket CORS must allow the approved frontend origins, PUT, and the content-type/encryption headers generated by the actual upload code. Do not confuse signed URL expiry with document retention.
- **Razorpay webhook:** configure `<API_ORIGIN>/api/v1/payments/razorpay/webhook` for **`payment.captured`** in Razorpay test mode. The handler requires `X-Razorpay-Signature` and `X-Razorpay-Event-Id`, checks captured status/order amount/currency, and deduplicates events. Checkout uses a JavaScript handler, **not `callback_url`**. Browser success does not mark the ledger paid; the verified webhook does. The current frontend rejects keys not starting `rzp_test_`. There is **no `RAZORPAY_TEST_MODE` or `VITE_RAZORPAY_KEY_ID` variable** read by this code.

## Local and Vercel placement

Local Vite uses root `.env.local` for public `VITE_*` values. Local API settings read `.env` relative to its working directory (normally `backend/.env`) or process environment. Never commit those files. On Vercel, set public widget/API URL values on the **frontend project**, and MSG91 Authkey/template, SMTP, AWS and Razorpay variables on the **API project**, with deliberate Preview/Production selection. Keep test and live credentials separate.

No live connection/delivery/scan/payment was verified while producing this inventory. Configuration and successful builds are not runtime verification.
