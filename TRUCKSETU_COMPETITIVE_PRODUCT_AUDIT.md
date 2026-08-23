# TruckSetu competitive product audit

**Assessment date:** 23 August 2026  
**Market:** Delhi and NCR, with selected interstate lanes  
**Product definition:** a marketplace for full-vehicle and shared-capacity goods transport—not a taxi clone and not merely a fixed-fare delivery operator.

## Executive verdict

TruckSetu has the backend foundations of a carpool-for-goods marketplace, but the current customer experience does not yet explain or safely operate that model end to end. The product already supports demand posting, competitive carrier quotes, planned-route publication, weight-based capacity reservation, KYC review, booking allocation, OTP trip events, payments, commission, disputes and reviews. Those are meaningful strengths.

However, the booking wizard does not ask whether the customer wants a **full vehicle** or **shared capacity**; cargo volume and dimensions are absent; planned routes track remaining weight but not remaining volume; and matching does not yet prove cargo compatibility, feasible stop sequencing or delivery-window compliance. Pricing is a useful advisory FTL-like estimate, but it is not a complete landed price and there is no defensible shared-capacity formula. Therefore:

- **Today:** advanced truck-booking and quotation marketplace with an early capacity-sharing module.
- **Not yet:** dependable, customer-ready carpooling for goods.
- **Best realistic V1 differentiator:** verified Delhi/NCR carriers competing for full loads, plus genuinely compatible spare-capacity offers on selected repeat corridors.
- **Pilot readiness:** conditional. Fix the P0 items in this report, seed supply manually and launch in one corridor/zone with two vehicle categories.

### Recommended positioning

**Customer:** “Compare verified transporters for a full vehicle or save by sharing suitable spare truck capacity—with clear quotations and tracked delivery.”

**Carrier:** “Fill empty space and return routes with compatible verified loads, while keeping control of your route, price and earnings.”

Do not use “cheapest”, “safest”, “guaranteed delivery” or “live GPS” until measured evidence and the corresponding operations exist.

## Evidence and claim labels

- **[Confirmed—public]:** supported by the linked competitor’s official public website or filing.
- **[Observed—public interface]:** visible in a public webpage/interface; this is not proof of operational quality.
- **[Reported by users]:** third-party user report. No user-report claims are relied upon in this audit.
- **[Inference]:** reasoned conclusion, not a confirmed competitor capability.
- **[Unable to verify]:** not reliably established from current public material.
- **[TruckSetu—code]:** found in the repository’s models, APIs or frontend implementation.
- **[TruckSetu—UI structure]:** found in frontend source. The live browser inspection service was unavailable during this assessment, so visual-quality judgements are structural rather than a claim of completed desktop/mobile rendered QA.

Public marketing numbers remain vendor claims even when they appear on an official source.

## Market map

| Category | Platforms | What the public evidence supports |
|---|---|---|
| Direct on-demand intracity | Porter | [Confirmed—public] Delhi mini-trucks, public starting prices, vehicle selection and route-based booking. Porter publicly lists Tata Ace from ₹350 and 3-wheeler from ₹250, but the same page contains inconsistent lower-page starting figures, so only a live identical quote is suitable for price comparison. [Source](https://porter.in/trucks/delhi?landing_page=ow) |
| On-demand parcel, adjacent | Borzo | [Confirmed—public] Same-day/express/scheduled parcel delivery; Delhi page publicly advertises a ₹50 start and ₹9/km for zone 1. This is a courier benchmark, not a truck benchmark. [Delhi](https://borzodelivery.com/in/cities/new-delhi) · [Small business](https://borzodelivery.com/in/for_small_business) |
| Freight marketplace / part load | Vahak | [Confirmed—public] Load posting, transporter offers, FTL and part-load booking, and space/route language. Operational effectiveness and quote quality are not independently verified. [Home](https://www.vahak.in/) · [Part load](https://www.vahak.in/part-load-booking) |
| Fleet-owner ecosystem / load marketplace | BlackBuck | [Confirmed—public] Loads marketplace plus FASTag, GPS/telematics, payments and fleet services. Primarily carrier/fleet oriented rather than a Porter-style household booking flow. [About](https://www.blackbuck.in/about-us.html) · [Products](https://www.blackbuck.com/company-products.html) |
| Load/truck matching portal | TruckSuvidha | [Confirmed—public] Posts are matched using truck/load type, origin, destination and availability; notifications may be email/SMS/call. [FAQ](https://trucksuvidha.com/FAQ.aspx) |
| Managed enterprise logistics | LetsTransport | [Confirmed—public] Enterprise first/mid/last-mile managed logistics and per-packet/tonne/unit approaches. Public Delhi/Gurugram presence exists; self-serve consumer equivalence is [Unable to verify]. [Home](https://letstransport.in/) · [Contact](https://letstransport.in/contact-us/) |
| Integrated PTL/FTL, adjacent | Delhivery | [Confirmed—public] FTL real-time freight rates, tracking and verified vehicles/drivers; PTL consolidates loads and supports ePOD. Fleet owners can find/recommended loads, bid, and receive advertised payout terms through Axle. [FTL](https://www.delhivery.com/services/truckload-freight) · [FY25 report](https://www.delhivery.com/uploads/2025/08/Annual_Report_FY25.pdf) · [Axle](https://www.delhivery.com/partner/fleet-owner) |
| Local Delhi operators | Fragmented operators and brokers | [Unable to verify] Public offerings commonly resolve to phone/WhatsApp inquiry pages; service quality, current price, KYC, tracking and refunds cannot be generalized without a controlled mystery-shop exercise. |

Porter is the convenience benchmark. Vahak and TruckSuvidha are marketplace benchmarks. Delhivery PTL/Axle is a useful operational benchmark for consolidation, proof of delivery and carrier liquidity. Borzo is relevant to small parcel speed and price presentation, not heavy-truck economics.

## Capability comparison

| Capability | My application | Porter | Other relevant competitors | Industry expectation | Gap | Recommended action |
|---|---|---|---|---|---|---|
| Customer registration | [TruckSetu—code] Persistent auth exists | [Confirmed—public] digital booking | Borzo [Observed—public interface] web ordering; others vary | OTP/mobile-first, low friction | Production identity/OTP and recovery need deployment validation | Mobile OTP, consent, recovery, duplicate-account controls |
| Driver/carrier registration | [TruckSetu—code] roles and provider profile | [Confirmed—public] partner onboarding | Vahak/Delhivery Axle [Confirmed—public] | Separate owner, driver, fleet roles | Role hand-off and assisted onboarding unclear | Guided role-specific onboarding and WhatsApp fallback |
| KYC | [TruckSetu—code] manual queue, documents and review events | [Confirmed—public] DL, PAN, address/bank and commercial vehicle documents listed [source](https://porter.in/partners) | Axle [Confirmed—public] basic details + KYC | Manual approval, expiry, audit trail | Malware scan, production storage and document authenticity checks | Keep manual approval; add secure object storage, scan, expiry jobs, four-eye review for overrides |
| Vehicle onboarding | [TruckSetu—code] provider/vehicle concepts, approval UI | [Confirmed—public] RC, fitness, insurance, PUC | Other marketplaces support truck attachment [Confirmed—public] | Vehicle type, body, dimensions, payload, docs | Capacity dimensions/body/permit coverage insufficient | Add internal dimensions, body type, axle/payload, permits, service area and expiry blocks |
| Booking process | [TruckSetu—UI structure] 4-step demand wizard then quotes | Porter [Observed—public interface] pickup/drop/stops/receiver/vehicle/goods | Borzo simple order; freight markets post-and-bid | Short path with progressive detail | Mode choice missing at start | Begin with “Full vehicle” / “Shared capacity”; preserve details across steps |
| Immediate booking | Not explicit | Porter Spot [Confirmed—public] on-demand; FAQ says no advance Spot booking [source](https://porter.in/spot-faq) | Borzo express [Confirmed—public] | “Now” with supply/ETA | Missing | Add Now/Schedule; only offer Now when eligible supply is online |
| Scheduled booking | Date/time exists | Porter Spot advance booking [Confirmed—public: unavailable] | Borzo scheduled [Confirmed—public] | Time window, not a brittle single minute | No pickup window or deadline | Add earliest/latest pickup and required delivery-by |
| Full-vehicle booking | Implicit default | [Confirmed—public] core mini-truck flow | Delhivery FTL [Confirmed—public] | Dedicated vehicle clearly labelled | Customer cannot explicitly select it | Add mode field persisted through quote, booking, invoice |
| Shared-capacity booking | Route/capacity module exists | [Unable to verify] comparable public consumer shared-truck mode | Vahak part load and Delhivery PTL [Confirmed—public] | Weight + volume + SLA + consolidation rules | Not complete/safe | Limit V1 to approved corridors and cargo classes; build compatibility and volume controls |
| Planned-route posting | [TruckSetu—code] available routes | [Unable to verify] | Vahak/Axle use lane/load concepts [Confirmed—public] | Route, departure window, deviation, capacity | Deviation/volume/stop schedule incomplete | Add route polyline, departure window, max deviation and remaining volume |
| Demand posting | Implemented | Porter is direct request [Observed—public interface] | Vahak/TruckSuvidha [Confirmed—public] | Complete shipment requirement | Missing dimensional and legal fields | Add fields specified in matching section |
| Carrier quotations | Implemented with versions/counteroffers | [Unable to verify] consumer carrier bidding | Vahak/Axle [Confirmed—public] offers/bids | All-in comparable quote and expiry | Quote components/conditions can vary | Enforce quote schema and “all-in except…” declaration |
| Fixed pricing | Advisory range, not final | [Confirmed—public] estimate/upfront pricing approach | Delhivery FTL rate lookup [Confirmed—public] | Label estimated, quoted or final | Current mode semantics unclear | Use three explicit price states and lock final snapshot |
| Price comparison | Multi-quote comparison exists | Not carrier comparison [Inference] | Freight markets support bids [Confirmed—public] | Normalize total, ETA, rating and inclusions | Cheapest quote can appear best without scope normalization | Rank by value/reliability; show fee/terms differences |
| Vehicle categories | Category model/recommendation | [Confirmed—public] multiple Delhi categories | Delhivery lists 14/17/20/32ft [Confirmed—public] | Payload and dimensions | Recommendation uses weight more than dimensions | Vehicle fit engine using weight, volume, body, cargo class |
| Fare breakdown | Advisory breakdown exists | Porter says upfront estimate [Confirmed—public] | Delhivery rate cards use weight/zone/overheads [Confirmed—public] | Landed payable price | Tolls, permits, taxes, allowance and platform fee absent from estimate | Adopt final-price card below |
| Live tracking | Manual status/timeline; no GPS | Porter/Delhivery [Confirmed—public] advertise tracking | BlackBuck GPS [Confirmed—public] | Map only when GPS fresh; fallback status | Do not imply live tracking | Integrate GPS later; show “last updated” and source now |
| Multiple stops | Stops plus charges | Porter booking includes stops [Confirmed—public] | Delhivery intracity terms define routed multi-stop pricing [Confirmed—public] [source](https://www.delhivery.com/tnc-direct-intracity) | Sequenced route and per-stop proof | Feasibility and stop-level status missing | Route sequence, contacts, OTP/POD and price per extra stop |
| Loading/unloading | Optional; **₹100 base + ₹7/parcel for each selected service** | [Unable to verify] exact current public charge | Local terms vary [Unable to verify] | Define labour scope, floors, weight and maximum pieces | Per-parcel rule ignores weight/floor/labour complexity | Pilot cap: ordinary packaged goods only; manual quote for heavy/bulky/floor carry |
| Pickup/delivery OTP | Implemented | [Unable to verify] exact public flow | Contactless/POD common; Delhivery confirms ePOD [Confirmed—public] | Event-specific proof | Need recipient identity and retries | Separate pickup/delivery OTP, expiry, masked number, override audit |
| Proof of delivery | Delivery OTP, no clear file POD | [Unable to verify] | Delhivery ePOD [Confirmed—public] | Photo/signature/document with timestamp | Missing | Add photo/signature/POD document and consent/retention policy |
| Payments | Payment/events and offline confirmation | [Confirmed—public] digital payment options exist | Borzo lists card/balance/cash [Confirmed—public] | Gateway, webhook, reconciliation | Production gateway/reconciliation must be validated | Use gateway-hosted checkout, signed webhooks, idempotency and ledger |
| Cancellation/refunds | Models/policies exist | [Confirmed—public] terms exist | Delhivery publishes conditions [Confirmed—public] | Quote-before-confirm and status-based refund | Customer-readable summary weak | Show fee before pay; automate eligible refund and SLA |
| Driver payouts | Provider payable computed | Axle [Confirmed—public] advertises advance and balance within two days of POD | BlackBuck payment tools [Confirmed—public] | Ledger, payout status, disputes | No complete payout rail/UI | Payout ledger, bank verification, T+N SLA and reconciliation |
| Ratings/reviews | Implemented | [Unable to verify] precise public flow | Common expectation | Verified-trip reviews and moderation | Sparse trust presentation | Show rating count, completed trips, recent service metrics |
| Support | Communication/chat concepts | Porter publishes support paths [Confirmed—public] | Axle calling team [Confirmed—public] | Human escalation with case ID | No support-ticket operations | In-app case + call/WhatsApp pilot desk, response SLA |
| Business accounts | Roles/provider flows; limited business tooling | Porter Enterprise [Confirmed—public] [source](https://porter.in/enterprise-faq) | LetsTransport/Delhivery enterprise [Confirmed—public] | GST profile, teams, credit, reports | Team/approval/credit absent | Postpone credit; pilot saved addresses, repeat loads and monthly statement |
| Invoice/GST | Models exist | [Unable to verify] exact current flow | Delhivery automated billing [Confirmed—public] | Tax invoice/download and identity | Downloadable artifact/numbering uncertain | GST validation, immutable invoice numbers, PDF/download |
| Promotions/referrals | Missing | [Unable to verify] current offer | Common growth pattern | Guardrails and attribution | Missing but not P0 | Add only after unit economics and fraud controls |
| Notifications | Notification/communication models | Porter/Borzo communications [Confirmed—public at service level] | TruckSuvidha email/SMS/call [Confirmed—public] | Push/SMS/WhatsApp critical events | Delivery channel reliability unproven | Event matrix, preferences, retry/dead-letter monitoring |
| Safety | KYC, OTP, disputes, audit | Porter says verified drivers [Confirmed—public] | Delhivery says verified vehicles/drivers [Confirmed—public] | Verification, SOS/contact, incident flow | Emergency and insurance responsibility unclear | Emergency contact, share-trip, incident runbook, prohibited goods |
| Website/mobile | Responsive CSS and large SPA | Porter/Borzo have focused mobile booking [Observed—public interface] | Vahak/Axle app-led [Confirmed—public] | Fast, resilient, accessible | Demo data and dense single bundle reduce confidence | Replace demo metrics, split role navigation, test 360px/slow 4G |
| Delhi availability | Product content targets Delhi/NCR | Porter/Borzo [Confirmed—public] Delhi | LetsTransport has Delhi/Gurugram contact [Confirmed—public] | Exact service boundary and hours | Operational supply not proven by software | Publish served zones/categories only after seeded coverage |

## Pricing audit

### What exists now

The advisory engine currently calculates:

```text
max(minimum fare, distance × configured per-km rate × vehicle count)
+ loading: ₹100 + ₹7 × parcel count, if selected
+ unloading: ₹100 + ₹7 × parcel count, if selected
+ ₹500 for every stop after the first two
+ ₹500 night charge
+ ₹500 per waiting hour after the first included hour
```

It returns a ±10% advisory range and explicitly says carriers set the final quote. That is a good anti-misrepresentation choice. The implementation validates parcel count when handling is selected.

### Coverage matrix

| Price input | Current support | Required decision |
|---|---|---|
| Full vehicle | Partial—implicit | Persist explicit booking mode and vehicle-specific rate card |
| Shared capacity/PTL | Provider route rate modes, but no platform formula | Build incremental-cost floor + value/risk allocation, not simple weight division |
| Immediate / scheduled | Same treatment | Add supply scarcity and operational scheduling rules; do not hide surge |
| Carrier quotation | Yes | Normalize included/excluded fees and expiry |
| Planned-route match | Carrier rate exists | Add deviation, remaining volume, stop work and minimum incremental earning |
| Multiple stops | First two included, then ₹500 each | Clarify whether pickup/drop count; price route distance as well as service work |
| Waiting | First hour free, then ₹500/hour | Define when timer starts, rounding, evidence and approval |
| Loading/unloading | ₹100 + ₹7/parcel each | Define parcel, maximum weight, stairs/floor carry and labour included |
| Tolls/parking | No complete estimate | Pass through actual with receipt or include known tolls before payment |
| Interstate permits | Missing | Quote line item and vehicle eligibility gate |
| Driver allowance | Missing | Add for long/interstate/overnight assignments |
| Night/restricted entry | Night ₹500; restricted-entry logic missing | Separate customer night service from Delhi vehicle-entry compliance |
| Tax/platform fee | Commission exists after booking; user estimate incomplete | Show customer tax/fee and carrier commission separately before acceptance |
| Advance | 20% concept exists | Show exact advance, balance trigger and refundability |
| Cancellation | Policy snapshot exists | Show status-dependent fee before confirmation |
| Insurance/handling | Missing | Do not imply coverage; disclose liability and optional cover when available |
| Promotion | Missing | Add later with a funded-discount ledger |

### Required full-vehicle formula

```text
Vehicle/category base or minimum
+ loaded kilometres × lane/category rate
+ empty pickup kilometres × deadhead rate (after free radius)
+ estimated service-time charge
+ known tolls/parking
+ permits/restricted-entry cost
+ loading/unloading/waiting/stops
+ driver allowance/overnight
+ cargo risk or optional insurance
+ applicable tax
+ disclosed customer platform fee
- funded discount
= customer payable
```

The carrier quote should separately snapshot carrier gross, platform commission, GST on platform service where applicable, adjustments and provider payable. Do not calculate platform profitability from GMV alone.

### Required shared-capacity price floor

For each compatible candidate, calculate:

```text
incremental carrier cost
= deviation distance fuel/maintenance
 + incremental drive/service time
 + pickup/drop labour and waiting
 + toll/permit increment
 + handling/risk allowance

carrier floor
= max(incremental carrier cost + minimum contribution,
      carrier's declared minimum earning)

customer shared quote
= carrier floor + platform cost/commission + tax + optional cover
```

Then check that the customer shared quote is meaningfully below a comparable dedicated quote. Weight, volume and capacity percentage can allocate common line-haul value, but **must not be the sole formula**. Reject the match if its stop order, deadline, cargo combination, permits or remaining weight/volume fail.

### Ten illustrative Delhi cases

These are **planning examples, not market quotes**. Assumptions: route distances are illustrative; no toll/permit/tax unless noted; handling uses ₹100 + ₹7/parcel separately for loading and unloading; platform commission illustration is 8% of the customer transport amount; “driver earning” is gross carrier payable after that commission, **not profit after fuel/wages**. Shared estimates are hypothetical outputs of the proposed incremental-cost model and must be validated with carriers. Exact competitor quotes must be collected as described below.

| Scenario | Vehicle | Full-load estimate | Shared-load estimate | Competitor/public benchmark if available | Driver earning* | Platform commission | Customer saving |
|---|---:|---:|---:|---|---:|---:|---:|
| Small household goods, 8 km, 10 parcels, both handling | 3-wheeler | ₹1,040 | ₹760 | Porter 3-wheeler starts ₹250 [Confirmed—public], exact identical quote required | ₹699 shared | ₹61 | ₹280 / 27% |
| Furniture, 18 km, 6 pieces, both handling | Tata Ace | ₹1,484 | ₹1,080 | Porter Tata Ace starts ₹350 [Confirmed—public], exact quote required | ₹994 | ₹86 | ₹404 / 27% |
| Retail inventory, 25 km, 30 cartons, unload only | Pickup 8ft | ₹2,160 | ₹1,520 | Price check required | ₹1,398 | ₹122 | ₹640 / 30% |
| Construction material, 22 km, no handling | Tata 407 | ₹2,500 | ₹1,850 | Price check required; shared only if packaging/cargo compatibility passes | ₹1,702 | ₹148 | ₹650 / 26% |
| E-commerce cartons, 30 km, 50 cartons, both handling | Pickup 8ft | ₹3,100 | ₹2,200 | Borzo is parcel-adjacent, not vehicle-equivalent; price check required | ₹2,024 | ₹176 | ₹900 / 29% |
| Dedicated mini-truck, 35 km | Tata Ace | ₹2,500 | Not applicable | Price check required | ₹2,300 | ₹200 | — |
| 400 kg part load, 45 km, route-aligned | 14ft shared | ₹2,500 comparable dedicated floor | ₹1,650 | Vahak/Delhivery PTL capability confirmed; public identical price unavailable | ₹1,518 | ₹132 | ₹850 / 34% |
| Business multi-stop, 40 km, 4 intermediate stops | Pickup 8ft | ₹3,500 (includes ₹1,000 stop fees) | ₹2,850 | Price check required | ₹2,622 | ₹228 | ₹650 / 19% |
| Delhi to Gurugram/Noida, 55 km | 14ft | ₹2,750 | ₹2,050 | Price check required; toll/entry charges excluded | ₹1,886 | ₹164 | ₹700 / 25% |
| Delhi to Jaipur, 280 km, overnight/interstate | 17ft | ₹14,500 + toll/permit/allowance | ₹10,800 + toll/permit/allowance | Porter publicly lists Delhi–Alwar 185 km from ₹3,800 and Delhi–Agra 207 km from ₹5,500, but vehicle/conditions differ; no valid direct comparison | ₹9,936 before pass-throughs | ₹864 | ₹3,700 / 26% |

\*For the full-only row, earnings use the full estimate. All other earnings use the illustrative shared amount.

These examples expose a present weakness: a generic per-kilometre/minimum rule cannot price all Delhi vehicle classes rationally. Configure rate cards by vehicle, city, operating window and lane; then use observed acceptance and completed-trip cost data. The cheapest headline price is unsustainable if it does not cover deadhead, wait time, failed pickup risk, support, payment cost, refunds and carrier retention.

### Lawful competitor quote collection

For each weekly benchmark:

1. Use a founder-controlled test account and identical pickup/drop pins, cargo, vehicle, stops, assistance and schedule.
2. Quote at the same timestamp on each eligible service; record normal and peak/restricted-entry periods.
3. Capture vehicle class, distance, ETA, base, taxes, tolls, add-ons, discount, cancellation terms and final payable.
4. Repeat at least three times per scenario over multiple days; record whether supply was unavailable.
5. Compare median landed price and successful fulfillment, not the lowest screenshot.
6. Store only public or manually and lawfully collected information. Do not scrape, automate competitor apps or bypass controls.
7. Track carrier payable and TruckSetu contribution margin beside customer price.

## Final price presentation

Before “Pay advance” or “Confirm booking”, show one immutable summary:

```text
Shared capacity • 400 kg / 2.2 m³ reserved in 14-ft truck
Rohini → Gurugram • 45 km estimated • pickup 10:00–11:00

Carrier transport quote                 ₹1,420
Loading (₹100 + 20 × ₹7)                  ₹240
Unloading                                Not selected
Known tolls                               ₹120
Platform/customer fee                      ₹80
Tax                                        ₹xx
Discount                                  -₹xx
                                         ──────
Final payable                            ₹x,xxx

Pay now (20%)                              ₹xxx
Balance after pickup/POD                  ₹x,xxx
```

Beside the total, show exactly one state: **Estimated**, **Carrier quote—expires at…**, or **Final price**. List exclusions (“parking at actual with receipt”, for example), cancellation/refund rule and who provides loading labour. Persist the accepted quote snapshot into booking, payment and invoice; later changes require a reason and both-party approval. Never show a crossed-out discount unless it is a genuine prior price.

## Matching and capacity-sharing audit

### Data readiness

| Required data | Current state | P0 change |
|---|---|---|
| Pickup, destination, stops, date/time | Present | Geocode/pin; add pickup window and delivery deadline |
| Weight, parcel count, cargo category, fragile/perishable/temp | Present | Validate total versus per-truck semantics |
| Dimensions and volume | Missing | Add L×W×H per item or total m³; compute chargeable volume |
| Hazardous/restricted status | Incomplete | Prohibited/restricted goods taxonomy and document gate |
| Full/shared preference | Missing | Mandatory booking mode; permit “either—show savings” |
| Max acceptable deviation | Missing | Customer max added time and carrier max km/minutes |
| Assistance/vehicle/budget | Mostly present | Add floors/lift, handling unit, body type and expected price type |
| Planned origin/destination/departure | Present in route module | Store route geometry and time window |
| Vehicle max/remaining weight | Present | Clarify gross/payload and update from all confirmed loads |
| Remaining volume | Missing | Required; protect transactionally like weight |
| Existing loads | Reservation concepts present | Persist stop sequence and compatibility state |
| Permits/service areas | KYC docs partially present | Machine-readable validity/territory and hard assignment gate |
| Minimum earning | Rate exists, explicit floor incomplete | Carrier minimum incremental earning per booking/route |

### V1 rules-based matcher

1. **Eligibility gate:** verified provider, active driver, approved vehicle, unexpired DL/RC/fitness/insurance/PUC/permit as applicable.
2. **Cargo gate:** allowed category; no prohibited combination; body/temperature/handling requirements match.
3. **Capacity gate:** requested weight ≤ remaining payload and requested volume ≤ remaining volume, including safety buffer.
4. **Time gate:** insertion into the current stop sequence satisfies every pickup window and delivery deadline.
5. **Route gate:** pickup and drop insertion adds no more than both parties’ maximum deviation.
6. **Economics gate:** resulting quote ≥ incremental-cost/carrier floor and shared customer price < comparable dedicated price by a meaningful threshold (suggest pilot target ≥10%).
7. **Rank:** normalized route fit 25%, time fit 20%, price/value 20%, verified reliability 15%, rating with minimum-count confidence 10%, empty-capacity utilization 10%.
8. **Reserve atomically:** lock route capacity; recheck weight, volume, time and document validity; create expiring hold; confirm after payment. Idempotency must prevent duplicate booking.
9. **Manual review:** hazardous, high-value, temperature-controlled, interstate permit ambiguity, excessive deviation or complex multi-stop cases.

Do not introduce machine learning until enough completed outcomes exist. The first model needs reliable labels: quote response, acceptance, arrival punctuality, cancellation, damage/dispute, actual deviation, driver incremental earning and contribution margin.

### Failure prevention

- Weight double-booking has a promising transactional reservation foundation [TruckSetu—code]; extend the same lock to volume and time-slot feasibility.
- Never mix food/pharma with chemicals, odorous/contaminating cargo, loose construction goods or other incompatible classes.
- Re-run sequence feasibility after every reservation/cancellation.
- Block assignment when provider, driver or vehicle status is not verified/active or any required document expires before trip completion.
- Store every override with admin, reason, timestamp and customer/carrier disclosure.

## Screen-level UI/UX audit

| Screen | Current quality | Competitor expectation | Working | Confusing / missing | Priority | Exact improvement |
|---|---|---|---|---|---|---|
| Landing | Medium structurally | Immediate city/service/value clarity | Marketplace value is present | Full/shared advantage and actual service boundary not dominant; demo metrics risk mistrust | P0 | Hero: mode choice + pickup/drop; three proof points; replace synthetic metrics with “pilot” truth |
| Login/registration | Medium | Phone OTP in seconds | Roles/auth foundations | Too much role complexity for new customer | P0 | Customer phone OTP first; ask business/owner/driver role only when relevant |
| Location and schedule | Medium | Pin, map, address validation, Now/Schedule | Stops/date/time exist | Text location, no pickup window/deadline/Now | P0 | Map pin + saved address + Now/Schedule + earliest/latest windows |
| Cargo details | Medium | Minimum questions with safe fit | Weight, parcels and flags | No dimensions/volume/hazard class; “weight per truck” presumes assignment | P0 | Total weight + dimensions/volume; prohibited goods help; move truck split later |
| Vehicle/mode | Low for differentiation | Clear vehicle capacity and price trade-off | Weight recommendation | No Full/Shared selector; recommendation lacks volume | P0 | Cards: Full, Shared, Either; vehicle payload/body/dimensions; savings/ETA trade-off |
| Estimate/review | Medium | Landed total and conditions | Advisory label and breakdown | Missing toll/permit/tax/fee/advance/refund; generic price model | P0 | Use immutable price card; explicitly label unknown/pass-through charges |
| Demand posted | Medium | Confirmation, expected response and fallback | Can share to verified providers | No service-level promise or supply state | P1 | Show matching progress, expected first response, edit/cancel and assisted-support option |
| Quotes/comparison | Strong foundation | Comparable totals, reliability, ETA | Versioning/counteroffers/multi-provider allocation | Scope and exclusions can be apples-to-oranges | P0 | Standardize line items; show verified badge, trips, on-time %, quote expiry and why recommended |
| Booking/payment | Medium | Minimal confirmation, secure payment, policy | Advance/payment architecture | Final-versus-estimated state and adjustment consent | P0 | One final snapshot, gateway trust marks, cancellation summary, downloadable receipt |
| Tracking | Low until telemetry | Map, ETA, contacts, issue help | Timeline/OTP | “Live” would be misleading without GPS | P0 | Rename “Trip status” until GPS; show last update, driver contact, share link, delay/incident action |
| Delivery/rating | Medium | POD, issue/damage flow then review | Delivery OTP/reviews/disputes | No photo/signature POD | P1 | Add POD upload, receiver name, exception reason and dispute window |
| History/profile/KYC | Medium | Clear statuses and reusable data | KYC workspace is unusually detailed | Customer KYC need may feel excessive; document expiry visibility | P1 | Separate identity profile from carrier compliance; show renewal timeline |
| Carrier onboarding | Medium | Assisted, vernacular, save/resume | Manual review and document set | Dense forms and uncertain approval SLA | P0 | Camera-first upload, OCR assist, examples, save/resume, Hindi labels, review SLA |
| Vehicle addition | Medium-low | Payload/body/dimensions/docs | Document concepts | Operational specs/permit territory insufficient | P0 | Vehicle-spec template by category and hard document eligibility status |
| Availability/planned route | Strong concept | Quick repeat route setup | Planned route/capacity/rate | No map deviation/volume/existing-load timeline | P0 | Route map, repeat schedule, remaining kg/m³, max deviation and stop timeline |
| Nearby demands/matches | Medium | Ranked actionable loads | Marketplace load list | Cannot explain compatibility or net earning | P0 | “Why matched”, added km/time, cargo compatibility, gross/net and accept/quote |
| Carrier trip/OTP | Medium | Huge touch targets, offline tolerance | Status and OTP foundations | Navigation/GPS, poor-network resilience not proven | P1 | One primary action per stage, cached trip data, call support, Hindi, retry queue |
| Earnings/payout | Low | Ledger and payout date | Commission math exists | No complete payout experience | P0 for supply trust | Gross, deductions, adjustments, payable, bank, expected payout, downloadable statement |
| Admin KYC | Strong prototype | Secure viewer, reasoned decisions, audit | Queue, decisions, review history concept | Demo records; authenticity/malware/four-eye controls | P0 | Production storage, masking, scan, document comparison, override approval |
| Admin operations | Medium prototype | Real exception queue and map | Funnel/market health concepts | Hard-coded metrics can mislead; support/refund consoles incomplete | P0 | Connect only real events; label data freshness; cases/refunds/payout exceptions |
| Admin pricing/commission | Backend-ready | Versioned rules and simulation | Settings architecture | No safe simulation/approval UI | P1 | Effective dates, corridor/category rules, test quote, maker-checker and rollback |

Across all screens add: field-level validation, useful empty/loading/error states, keyboard focus, 44px touch targets, sufficient contrast, plain Hindi-ready strings, retry-safe submissions and a persistent support route. First-time carrier UI should avoid terms like “allocation” and “capacity reservation”; use “space left”, “added distance”, “you receive” and “pickup before”.

## Brand and trust

### Present strengths

- Verification is deeper than a decorative badge: document review events and expiry concepts exist.
- Quotes, OTP events, payment events, disputes and audit records can become a coherent chain of custody.
- Advisory pricing is correctly described as guidance rather than pretending a carrier quote is fixed.

### Missing trust layer before taking real payments

1. Legal company name, operating address, support number/email and grievance route.
2. Terms, privacy, cancellation/refund, prohibited goods and damage/liability policies.
3. Plain explanation of what “verified” checks and what it does not guarantee.
4. Carrier card with verified vehicle, document validity, rating count, completed trips and recent reliability.
5. Payment provider/secure-checkout indication without unsupported “100% secure” claims.
6. Service-zone/category/hours clarity and what happens when no carrier responds.
7. Insurance coverage or an explicit statement that coverage is unavailable; never leave ambiguity.
8. Real operational photos and genuine testimonials only after consent; no stock image presented as a provider.

Use consistent colours/typography and reserve badges for facts. “Verified” must link to an explanation; “Top carrier” needs a published calculation; savings must compare like-for-like quotes.

## Liquidity and Delhi pilot

### Cold-start diagnosis

Marketplace features do not create marketplace liquidity. A shared-capacity promise is especially fragile: customer cargo, route, time and capacity must coincide. Launching all Delhi, all vehicle types and all cargo types would produce slow first quotes and unreliable shared matches.

### Smallest competitive pilot

- **Geography:** one dense origin cluster and two repeat lanes, for example North/West Delhi wholesale clusters to Gurugram and Noida. Validate restricted-entry rules operationally before naming the exact boundary.
- **Categories:** Tata Ace/pickup and 14-ft only.
- **Customers:** repeat retailers/wholesalers, furniture/appliance sellers and packaged e-commerce/B2B cartons; exclude hazardous, loose bulk and temperature control initially.
- **Supply starting hypothesis:** 25–40 manually verified, genuinely responsive vehicles across the two categories, with at least 8–12 plausibly active in each operating window. This is a test threshold, not an industry fact.
- **Demand starting hypothesis:** 8–15 qualified requirements/day concentrated in the pilot lanes; do not expand until median qualified quotes per demand ≥3 and time to first qualified quote ≤15 minutes during service hours.
- **Operations:** founder-assisted booking, manual match fallback, WhatsApp/call support, human price/permit review, daily payout reconciliation.

### Pilot scorecard

Measure by mode, lane, vehicle and customer segment:

- eligible/active carriers per hour; response rate; time to first and third qualified quote;
- quotes per demand; quote acceptance; no-supply rate; cancellation by party/reason;
- pickup punctuality, completion, delivery-window success, support contacts and disputes/damage;
- repeat customer rate at 30/60/90 days and repeat active carrier rate;
- shared requests, match rate, confirmed utilization by weight **and volume**;
- dedicated-price benchmark, actual customer shared saving and carrier incremental earning;
- GMV, commission, payment/support/refund/incentive costs and contribution margin per completed booking.

### Launch offers with guardrails

| Offer | Who funds it | Cap/duration | Fraud risk/control | Success metric / stop rule |
|---|---|---|---|---|
| 0% carrier commission | TruckSetu foregone revenue | First 10 completed trips or 30 days; max ₹2,000/carrier | Duplicate carriers/collusion; KYC, vehicle uniqueness, completed paid trip only | Retained active supply; stop if response/retention does not improve |
| Fast payout | Working capital/operations | T+1 after valid POD for low-risk trips | Fake POD/refund exposure; reserve, POD and anomaly review | Carrier retention and response; stop/limit after elevated disputes |
| First-booking customer credit | Marketing budget | min(10%, ₹300), one verified business/mobile/payment identity | Multi-account/self-dealing; device/payment/address controls | Second paid booking within 30 days; stop channel if CAC exceeds contribution target |
| Referral | Marketing budget | Pay after referred party’s second completed trip; ₹250–₹500 cap | Ring fraud; relationship/device/payment checks | Incremental retained users, not registrations |
| Shared-capacity discount | TruckSetu or carrier explicitly | Up to ₹300 and 20 pilot bookings/route | Relabeling FTL, fake matches; require route/capacity record | Match rate, saving, repeat; stop if post-incentive margin or reliability fails |
| Guaranteed carrier earning | TruckSetu | Avoid initially; if tested, one shift/zone with written cap | Idle/collusive check-ins | Incremental completed GMV per guarantee rupee; stop rapidly if uneconomic |

## Differentiation

1. **Competitors already do well:** Porter sets the on-demand convenience and Delhi vehicle-choice expectation [Confirmed—public]. Vahak/TruckSuvidha make load posting and carrier discovery familiar [Confirmed—public]. Delhivery demonstrates PTL/FTL, ePOD, tracking and a carrier load exchange at scale [Confirmed—public]. BlackBuck offers a broader fleet ecosystem [Confirmed—public].
2. **TruckSetu currently does better in its product blueprint:** one architecture combines multi-carrier quote comparison, counteroffers, planned spare-capacity routes, booking allocations, manual KYC review and configurable marketplace commission.
3. **It currently does worse:** supply certainty, instant fulfillment, GPS tracking, operational proof, payout experience, dimensional capacity safety, price completeness, legal/trust content and mobile-tested simplicity.
4. **Equal, not differentiated:** registration, generic truck categories, demand posting, ratings, OTP, notifications and a low headline price.
5. **Customers will value:** qualified choices, a genuinely lower shared price, predictable arrival, no surprise fees, verified carrier/vehicle and fast problem resolution.
6. **Carriers will value:** profitable route-fit loads, clear net earnings, control over quote, fast reliable payout, low deadhead and fewer wasted calls.
7. **Unlikely to matter in V1:** AI branding, broad analytics, complex loyalty, nationwide category breadth, dynamic surge sophistication and fully automated multi-load optimization before liquidity.
8. **Strongest realistic V1 differentiator:** “Compare verified full-load quotes or take a cheaper compatible spare-capacity option on selected Delhi/NCR lanes.”
9. **Customer value proposition:** “Move goods with verified transporters—compare full-truck quotes or save with suitable shared capacity, with every charge shown before you confirm.”
10. **Carrier value proposition:** “Turn spare capacity and return routes into extra earnings with route-matched loads, transparent deductions and dependable payout.”

Copy only industry-standard interaction patterns: short address entry, vehicle cards, clear step progress, OTP verification, map/timeline conventions, transparent checkout and accessible mobile controls. Do **not** copy competitor branding, text, illustrations, screen composition, proprietary pricing/matching rules, data or misleading claims.

## Five biggest mistakes now

1. The differentiating Full/Shared choice is absent from the main booking flow.
2. Shared capacity is protected by weight but not volume, full stop sequencing, time windows or cargo compatibility.
3. Advisory pricing omits major landed-cost components and lacks vehicle/city/lane specificity.
4. Prototype/demo operational numbers and incomplete trust/legal/support surfaces can create false confidence.
5. “Tracking”, provider payout and proof of delivery are not yet at the operational standard implied by a production marketplace.

## Five strongest parts

1. Quote versioning, counteroffers, comparison and multi-provider allocation.
2. Planned-route and atomic capacity-reservation foundation.
3. Manual KYC review with documents, decisions, history and expiry concepts.
4. Booking/trip OTP, payment-event, commission, dispute and review domain coverage.
5. Honest advisory-price wording and now-correct handling rule: ₹100 base + ₹7 per parcel for loading and independently for unloading.

## P0 before Delhi pilot

1. Add Full / Shared / Either and Now / Schedule at the start; persist through request, quote, booking, payment and invoice.
2. Add dimensions/volume, pickup window, delivery deadline, max deviation, cargo compatibility and prohibited-goods checks.
3. Upgrade route supply with remaining kg and m³, stop schedule, existing loads, route deviation, permits and minimum earning.
4. Implement the rules matcher and atomic weight+volume+time reservation; hard-block unverified/expired assignments.
5. Replace the price card with landed-price states, standardized carrier quote breakdown and immutable accepted snapshot.
6. Finish production payment/payout reconciliation, POD, cancellation/refund and support-case flows.
7. Add legal/trust/service-area content and remove or label all demo metrics/data.
8. Perform actual rendered QA at desktop and 360/390px mobile, keyboard/accessibility checks and slow-network/error testing before launch.

## Final answers

- **Is it actually carpooling for goods?** Partly in architecture, no in the complete customer/operational experience. It is presently a sophisticated booking/quotation marketplace with an incomplete shared-capacity path.
- **Can customers understand full versus shared?** No; the booking wizard does not make the choice explicit.
- **Is pricing competitive, transparent and sustainable?** Competitiveness is unproven without controlled quotes. Transparency is partial. Sustainability cannot be established until deadhead, tolls/permits, time, payout, refunds/support and contribution margin are measured. The current handling rule is implemented correctly.
- **Does the UI meet Porter-like trust/convenience?** Not yet. The structure is promising, but supply certainty, mobile rendered proof, final-price clarity, tracking, support and public trust evidence lag the benchmark.
- **What do established competitors do better?** Liquidity, fulfillment certainty, app familiarity, live operational networks, tracking/POD and public service clarity.
- **What can TruckSetu do better?** Give customers transparent carrier choice plus a verifiably compatible, economically fair shared-capacity alternative while improving carrier return-route earnings.
- **What must be copied only as a pattern?** Familiar booking steps, map/address interactions, vehicle capacity cards, OTP, tracking timelines and transparent checkout.
- **What must not be copied?** Branding, wording, visual identity, proprietary rate/matching logic, competitor data or unsupported superlatives.
- **What should be redesigned before the pilot?** Mode/schedule selection, dimensional cargo capture, price confirmation, quote normalization, carrier match cards, route capacity view, payout ledger and support/POD.
- **What must be measured?** Liquidity, response, acceptance, punctuality, completion, retention, shared utilization/saving, carrier incremental earning, disputes and contribution margin.
- **Smallest competitive launch:** two Delhi/NCR lanes, two vehicle categories, ordinary packaged goods, 25–40 verified vehicles, founder-assisted operations, full-load quotes plus manually supervised shared matches.
- **Postpone:** ML matching, broad interstate automation, hazardous/temperature cargo, nationwide launch, promotions engine, credit, elaborate loyalty and fully dynamic pricing until real repeat demand and reliable economics exist.

## Source list

All competitor claims above are attributed inline. Principal official sources accessed for this assessment:

- [Porter Delhi trucks](https://porter.in/trucks/delhi?landing_page=ow), [Spot FAQ](https://porter.in/spot-faq), [Partner onboarding](https://porter.in/partners), [Enterprise FAQ](https://porter.in/enterprise-faq), [About](https://porter.in/about-us?gads=search)
- [Borzo Delhi](https://borzodelivery.com/in/cities/new-delhi), [Borzo small business](https://borzodelivery.com/in/for_small_business), [Borzo India](https://borzodelivery.com/in)
- [Vahak](https://www.vahak.in/), [Vahak part-load booking](https://www.vahak.in/part-load-booking), [How Vahak helps](https://www.vahak.in/how-vahak-helps)
- [BlackBuck about](https://www.blackbuck.in/about-us.html), [BlackBuck products](https://www.blackbuck.com/company-products.html), [BlackBuck Fleet](https://blackbuck.com/boss)
- [TruckSuvidha FAQ](https://trucksuvidha.com/FAQ.aspx), [TruckSuvidha registration](https://trucksuvidha.com/Register)
- [LetsTransport](https://letstransport.in/), [LetsTransport contact](https://letstransport.in/contact-us/), [LetsTransport about](https://letstransport.in/about-us/)
- [Delhivery truckload freight](https://www.delhivery.com/services/truckload-freight), [FY25 annual report](https://www.delhivery.com/uploads/2025/08/Annual_Report_FY25.pdf), [Axle fleet-owner app](https://www.delhivery.com/partner/fleet-owner), [Rate-card guidance](https://help.delhivery.com/home/docs/rate-card)

Public pages and offers change. Revalidate all external facts and prices immediately before launch or investor/customer publication.
