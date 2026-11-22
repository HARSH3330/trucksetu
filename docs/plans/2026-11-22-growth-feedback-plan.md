# TransivoX growth plan from MiroFish feedback

**Date:** 22 November 2026.

**Status:** this is a plan only. Nothing has been built, and nothing starts until the owner approves.

**Ground rule:** every change is new and switched off by default. Live behaviour stays the same until each switch is approved and turned on: the ₹99 connection fee, manual verification, bidding, payments and refunds.

The MiroFish feedback came from a simulated market. It is a set of hypotheses, not customer evidence. Each phase therefore starts by measuring the problem with the funnel analytics TransivoX already records (visitor → signup → verification → load posted → bid → payment → trip).

---

## 1. The ten points at a glance

| # | Feedback point | What it needs | Touches live flows? | Owner decision needed | Effort |
|---|---|---|---|---|---|
| 8 | Make "advisory price" vs "truck owner's price" clear | Website wording and layout only | No | None (just approval) | Small |
| 6 | Simpler bid comparison for small shippers | Website only | No; same data, clearer layout | None (just approval) | Small–medium |
| 2 | 24/7 support | Help button, WhatsApp chat, call number, ticket queue | No; adds new entry points | Who answers, hours, phone number | Small to build; staffing is the real cost |
| 1a | Free trial credits | Reuses the existing single-use fee credits; one small database change | Checkout gains a "free credit applied" path | How many, who qualifies, tax treatment | Medium |
| 4 | Referral rewards | Reward = fee credits (not cash) behind the existing promotions switch | No, until switched on | Reward size, abuse limits | Medium |
| 3 | Automatic document checks (VAHAN / DigiLocker) | Licensed verification provider, behind the existing automated-KYC switch | No; manual approval stays, the check only assists the reviewer | Provider and cost; legal/privacy review | Medium–large |
| 5 | Seed guaranteed demand | Business development, not code; optional "verified business" badge | No | Which partners | Ops |
| 9 | Marketing on cost savings | Landing page and campaigns | No | Claims must be provable | Ops |
| 1b | Pay only after a successful booking | Different business model | **Yes, replaces the ₹99 upfront fee** | Major: revenue risk and collection | Large |
| 7 | Escrow and credit terms | Payment-aggregator rules and regulated escrow | **Yes, money movement** | Legal and RBI-compliance review first | Large |
| 10 | Broker mode | New account type and commission handling | **Yes, roles and money** | Product and legal decision | Large |

---

## 2. Phased plan

### Phase 1: quick, safe improvements (about 1–2 weeks of work)

These change only wording, layout and new entry points. No database change, no money change.

**8. Clear pricing language**
- On the price estimate page and on every bid: "TransivoX estimate (advisory)" next to "Truck owner's price (what you pay)", with a one-line explanation and an ⓘ tooltip.
- In bid comparison, show the advisory range beside each quote so the customer can see whether it is above or below the range.
- **Done when:** a first-time user can tell, without help, which number they actually pay. Check with 3–5 real users.

**6. Simpler bid comparison**
- Default view shows only: price, pickup and delivery times, truck type, rating and verification badge, plus a single "Choose this bid" button.
- "Show details" expands inclusions, exclusions and charges, as today.
- Sort by lowest price or earliest pickup.
- Mobile first. No data or rules change.

**2. Support entry points**
- A "Help" button on every signed-in page. It opens:
  - **WhatsApp chat** using the existing WATI integration, once its key is set;
  - a **call** link to a number the owner chooses;
  - **"Report a problem on this trip"**, which creates a ticket linked to the booking and appears in the admin console.
- Show support hours honestly. Until people are staffed around the clock, say "We reply within X hours" instead of "24/7".
- **Owner decides:** the support phone number, who answers, real hours, and whether WhatsApp (WATI) is turned on.

**Measurement (runs throughout):** a weekly funnel report in the admin console showing where people drop off. This tells us whether the fee or verification is the real barrier before Phase 2 changes anything about money.

### Phase 2: lower the cost of trying TransivoX (about 2–3 weeks, after Phase 1)

**1a. Free trial credits**
- Reuse the existing `connection_fee_credits` system. It is already single-use and reserved atomically, and checkout already shows "Platform connection fee waived".
- **Database change:** today every credit must come from a failed booking (`source_selection_id` is required). Add a `source_kind` column (`provider_failure` or `welcome`) and make the source nullable for welcome credits. The change is additive.
- **Proposed rule** (owner to confirm): one welcome credit per verified customer, issued automatically when PAN verification is approved. It is limited to one per PAN and one per phone number, to stop people creating extra accounts.
- **Switch:** `ENABLE_WELCOME_CREDIT`, off until approved.
- **Owner decides:**
  - how many credits each customer gets;
  - whether credits expire (AGENTS.md says not to invent this);
  - how a ₹0 order is taxed (needs your accountant);
  - whether truck owners get anything.

**4. Referral rewards**
- Each verified customer gets a referral link. When a referred customer completes their **first paid booking**, the referrer gets one fee credit.
- Rewards are fee credits, not cash. That avoids cashback becoming money movement (payouts, tax, RBI rules).
- **Abuse limits:** no self-referral (same PAN, phone or device), a monthly cap, and admin review in the console.
- Behind the existing `ENABLE_PROMOTIONS` switch, off until approved.
- **Owner decides:** reward size, monthly cap, and whether truck owners can refer too.

### Phase 3: faster verification (about 3–5 weeks, partly waiting on a vendor)

**3. Automatic document checks**
- **Step 1, vehicle and licence lookup:** connect a licensed verification provider (for example Surepass, Signzy or IDfy, all of which offer VAHAN RC and Sarathi DL lookups). When a truck owner uploads an RC or a driving licence, the server looks up the number and shows the reviewer whether the owner name, expiry and vehicle class match.
- **Manual approval stays.** The lookup only helps the reviewer, so approvals take minutes instead of hours. That keeps to the AGENTS.md rule: a submitted or scan-clean document is never treated as verified without a review.
- **Step 2 (later), DigiLocker:** DigiLocker needs partner onboarding and handles Aadhaar-linked data, so it needs a legal and privacy review before any build.
- Behind the existing `ENABLE_AUTOMATED_KYC` switch, off until approved.
- **Owner decides:**
  - which provider, and the cost per check (usually ₹2–10);
  - signing the data-processing agreement;
  - the privacy notice update;
  - legal review.

### Phase 4: business-model changes (decide first, build later)

These change who pays, when, or who holds money. Nothing here should be built until the owner, an accountant and a lawyer have agreed the rules.

**1b. Pay after a successful booking**
- **Risk:** the ₹99 buys the contact. If contact is free up front, customer and truck owner can settle off-platform and never pay.
- **Safer middle ground:** keep ₹99 up front, but make the existing pre-reveal refund and provider-failure credit very visible ("Truck owner didn't show up? Your fee comes back as a credit"). Phase 2 welcome credits cover the first-try barrier.

**7. Escrow and credit terms**
- TransivoX must not call anything "escrow" without a regulated escrow arrangement (AGENTS.md).
- Holding freight money needs payment-aggregator rules (RBI) or a partner-bank escrow.
- 15–30 day credit means lending, or an NBFC or invoice-financing partner.
- **Recommendation:** first talk to Razorpay about Route or escrow products and to an invoice-financing partner. Not a code task yet.

**10. Broker mode**
- Needs a new account type, rules on who owns the customer relationship, commission disclosure, and invoicing.
- **Recommendation:** first interview 5–10 brokers and decide whether they should simply be "fleet owners with partner trucks", which TransivoX mostly supports already. Only then design anything new.

### Not code (can run alongside any phase)

**5. Seeding demand**
- Sign 3–5 anchor shippers in one corridor (for example Delhi NCR ↔ Jaipur) and onboard their regular loads yourself.
- Optional code: a "Verified business" badge on loads from customers with GST verified. This is a small change.

**9. Marketing**
- A landing page and regional campaigns about direct price control.
- Any savings claim ("save X%") needs real data from completed bookings first. Until then, say "set your own price, no broker in between", which is true today.

---

## 3. How each change stays away from live features

- Every feature ships **switched off**, and you turn each one on separately after approval.
- Database changes are **additive only** (new nullable columns or tables), with a backup branch first, as in the last four releases.
- The existing ₹99 fee, refunds, provider-failure credits and manual verification stay exactly as they are. New code only adds paths next to them.
- Each phase is its own commit and deploy. Phase 2 does not start until Phase 1 has been live and measured for at least a week.
- Each phase gets tests for permissions, credits (no double use, no self-referral) and the switched-off state. Payment and verification code keeps its current tests.

---

## 4. Decisions needed from the owner

1. **Approve Phase 1:** pricing wording, simpler comparison, Help button.
2. **Support:** the phone number, who answers, real hours, and whether to turn on WhatsApp (WATI).
3. **Welcome credits:** how many, expiry or none, and how a ₹0 order is taxed (accountant).
4. **Referrals:** reward size, monthly cap, and whether truck owners can refer.
5. **Automated checks:** which provider and the budget per check; a lawyer reviews the privacy notice.
6. **Phase 4:** decide whether to pursue the success fee, escrow or credit terms, or broker mode at all, after advice.

**Recommended start:** approve Phase 1 (no money or database change), answer decision 2, and start the measurement report. That gives real evidence before changing the fee.
