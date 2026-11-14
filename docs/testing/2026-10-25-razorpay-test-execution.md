# Razorpay Test Mode execution — 25 October 2026 IST

Status: PARTIAL; user checkout handoff required. No live operation or production setting changed.

Private DPAPI Test credentials loaded without printing values; Test API read-only authentication200. Restricted database127.0.0.1:55432/transivox_e2e and role transivox_e2e_user, head20261023_28 reverified. Same webhook-only HTTPS tunnel retained. Synthetic fixture KYC prerequisites are local simulations, not scanner or identity verification evidence. Live checkout/tax confirmation false; fee1000+illustrative200=1200, waiver blocked.

Actual Test Mode orders:
- Reveal journey: order_Ts2RrPfZtZ857Y, selection76174888-ff97-4345-9ce4-e77bca5bd3c9. First app order attempt returned503/unknown; read-only provider lookup found no orders. One controlled exact-receipt request succeeded; original local selection reconciled after provider GET verified exact receipt/amount/currency, with audit connection.sandbox_order_reconciled. This exception recovery is not an ordinary-path checkout pass. No duplicate order.
- Refund journey: order_Ts2YgcfB8SZScP, selection27705d17-e8aa-4c15-95d6-282df9dd957f. Normal running API order creation passed,120000paise INR. Contact locked.

Actual mock-netbanking attempt pay_Ts2WZq2dS98ujR was cancelled after the in-app browser did not expose the mock-bank authorization page. Provider GET confirms failed, capturedfalse. Genuine signed provider payment.failed event Ts2Y65VqAeGgbd reached local API through relay/tunnel; stored outcome failed_no_unlock. Customer contact endpoint reports locked. No synthetic captured event used in this journey.

Test card browser entry was rejected by automatic approval review: financial checkout requires user handoff even for authorized Test Mode. No workaround attempted. User must complete the two existing orders at http://127.0.0.1:18113/ using the reveal/refund checkout buttons, official Test Mode instruments and mock success page. Do not use real bank/card data; do not save a payment method. No need to reenter credentials or modify webhook. Both synthetic booking contacts remain hidden. API18110, relay18111, tunnel18112 and loopback checkout18113 retained for handoff; URL expires if tunnel restarts.

Captured verification, explicit reveal, repeat purchased contact access and executed full pre-reveal refund: BLOCKED on user completion of test checkouts, not passed. No refund request/execution yet. Provider-failure credit retains prior local simulation evidence only. Original failed delivery actual, duplicate replay separately labelled local reconstruction/re-signing with actual IDs. See outputs/2026-10-25-razorpay-actual-test-state.json and outputs/2026-10-25-razorpay-replay-ownership.json outside Git for sanitized evidence. No keys, tokens or real personal data in this report.
