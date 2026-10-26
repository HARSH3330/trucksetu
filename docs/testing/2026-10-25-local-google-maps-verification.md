# Local Google Maps verification — 25 October 2026 IST

Local Maps is WORKING. This is the preserved existing customer-first candidate, not a deployment or production acceptance. No source push, production settings, paid-service activation, billing change, new API enablement, OTP or Razorpay operation occurred during this Maps verification. The server-side Routes adapter backend/app/api/pricing.py is unchanged.

## Configuration and isolation

Actual frontend: http://127.0.0.1:5173/ ; ordinary API: http://127.0.0.1:18000/api/v1. Frontend restarted with the privately entered key. Its ignored local file now also pins VITE_API_URL to the isolated18000API so a later frontend restart cannot silently fall back to a different backend. Exact read variables: VITE_GOOGLE_MAPS_BROWSER_KEY (SDK loader) and VITE_GOOGLE_MAPS_MAP_ID (map constructor). Both present; local Map ID is DEMO_MAP_ID. Repository-root .env.local is ignored by Git, not staged, and excluded from source manifests. Key literal check passed across the changed source; key is not printed here or in screenshots/log evidence. Browser keys are necessarily sent only to Google's browser SDK; no backend/server credential was moved into frontend variables.

Database identity:127.0.0.1:55432/transivox_e2e, transivox_e2e_user with no superuser/create-db/create-role. Additive nullable private JSON columns applied ONLY here:20261023_28 ->20261025_29. No reset or existing-record repricing. Normal API has TRANSIVOX_E2E=false, CUSTOMER_KYC_TEST_SIMULATION=false, real checkout false and Razorpay sandbox false. Designated synthetic account and fictional prerequisite fixtures; no real KYC documents or production records. Customer KYC was never approved/bypassed for the real-browser journey.

## Real Google API / actual local website

| Check | Result | Actual evidence |
|---|---|---|
| Map/Map ID/key/billing/referrer/API usability | PASS | Actual Google map, tiles and marker rendered; opt-in real browser smoke1passed; sanitized Google console errors0, failed Google network requests0 |
| Pickup Places API New | PASS | Actual India Gate, New Delhi predictions appeared; keyboard selection filled private address/city and pin28.6110886,77.2345184 |
| Destination Places API New | PASS | Actual Connaught Place predictions appeared independently; selection filled New Delhi/address and pin28.630420,77.217722 (displayed precision) |
| Pin movement/confirmation | PASS | Pickup nudge changed only pickup and required confirmation; actual Google destination marker Alt+Enter, ArrowUp, Enter keyboard drag fired gmp-dragend and required confirmation |
| Manual changes | PASS | Editing pickup address removed pickup coordinates/control; destination retained its address and pin |
| Draft persistence | PASS | Save through real API/PostgreSQL, dashboard Resume draft restored both original pins/addresses; later manual pickup retained no pin while destination pin persisted |
| Review/request preservation | PASS | Review displayed chosen destination pin and independent manual pickup; real saved draft submitted with destination coordinates and pickupnull |
| Publish with missing customer KYC | BLOCKED (expected) | Actual403 Complete customer document verification before publishing; published demands0before/0after; draft/data retained; no bypass |
| Empty/no-result recovery | PASS | Empty search created no pin; a synthetic nonexistent Google query offered no selected place; clearing/Escape returned to usable manual fields without invented coordinates |
| Desktop/mobile/keyboard/attribution | PASS | Real desktop1440px smoke/screenshot; actual390px control/keyboard checks, no page horizontal overflow,20px radios, Terms attribution bounds inside mobile map. Native Google Places mobile full-screen suggestions and branding retained |

Real automated evidence outside Git: outputs/2026-10-25-real-google-network.json, outputs/2026-10-25-real-google-map-desktop.png, outputs/2026-10-25-maps-kyc-gate.json. The Google request hosts recorded were maps.googleapis.com, maps.gstatic.com, fonts.googleapis.com and fonts.gstatic.com; query strings/keys are never recorded. Manual Places selection observations above are separate from the automated map/draft/network smoke. No claim that a simulated response proved a Google API call.

## Simulated / isolated verification

| Check | Result | Evidence |
|---|---|---|
| Desktop1440/mobile390 autocomplete, map selection, nudge confirmation, draft payload, full demand submission | PASS (SIMULATED Google/account/API) |2browser cases; synthetic addresses and mocked endpoints; Google requests blocked |
| Billing/API denial and stale-pin clearing | PASS (SIMULATED) | Widget gmp-error, readable recovery, manual submission, coordinatesnull |
| SDK/network outage | PASS (SIMULATED) | Script request deliberately aborted locally; retry/manual entry work; no fabricated coordinates or distance |
| Late Places/manual-edit race | PASS (SIMULATED) | Observed failing regression overwrote Gurugram with stale Delhi, then fixed; final guard rejects changes to address/city/coordinates/confirmation made while details load |
| Focused browser total | PASS |5simulated +1real opt-in automated check; separate configurations/evidence |
| Coordinate state units | PASS |4cases; includes zero, partial/NaN/out-of-range, clearing and confirmation |
| Frontend regression suite | PASS |52tests earlier in this Maps work; final affected state tests4passed; unchanged suites not repeatedly rerun |
| Frontend/browser TS + production build | PASS |Final checks after race fix; existing >500kB main-chunk warning remains nonfatal |
| Backend focused policy/privacy/migration checks | PASS |15tests; includes bounds, private-only serialization and complete linear chain/offline SQL |
| Isolated PostgreSQL draft/publish/edit/privacy | PASS |1case on generated migrated schema; simulated compliance prerequisite explicitly marked; nonempty provider discovery/detail omit both precise location fields |
| Migration checker, Ruff and diff whitespace | PASS |single head29 and full offline PostgreSQL SQL compilation; no production migration |

Browser simulations use a separate static Vite harness with a placeholder browser key, not the owner's key. This resolved dev-server/HMR/cache interference. Initial failures and corrected fixture403 expectation were not counted as passes. Real publication success remains untested because required customer document review is intentionally enforced.

## Changes and fixes

- Optional lazy browser Maps/Places New SDK loader and demand location panel; minimal place fields formattedAddress/location/addressComponents, country-limited search, selectable/keyboard-adjustable/draggable endpoints, explicit address confirmation, manual fallback/retry and attribution.
- Draft/edit/review/submission now carry validated optional private coordinates. Manual city/address edits invalidate stale pins; late place results cannot overwrite subsequent manual edits. No reverse-geocoding, route/freight distance estimate or fabricated coordinates.
- Nullable additive migration29, private owner serialization, bounded numeric input, non-owner/public omission; no booking/bid/KYC/payment rule relaxed.
- Fixed radio sizing, map-container overflow, initial-load retry exposure and UTF8 labels. Preserved existing brand/components.
- Added focused unit, PostgreSQL, simulated browser and opt-in real browser tests; test artifacts/private env ignored. Changed-source manifest lists exact files and hashes.

## Remaining owner/production actions

No Google billing/API/referrer blocker was reproduced locally. Dashboard key restriction scope was not independently inspected: confirm this browser key is website-restricted to the actually used http://127.0.0.1:5173/* and API-restricted to Maps JavaScript API plus Places API(New). Add http://localhost:5173/* only if that separate origin is actually used. The5175simulation origin uses only a fake key and needs no authorization. Do not authorize production or wildcard origins for the local key. No Routes, Geocoding, legacy Places or other API is required by this frontend.

Before any separately authorized production release: use a project-owned Map ID instead of DEMO_MAP_ID, a separately reviewed production browser key/origin restrictions, approved privacy/Google data-storage treatment, reviewed migration29/API-first/frontend compatibility and isolated preview/release gates. DEMO_MAP_ID is local testing only. Existing unrelated launch blockers and payment/OTP restrictions remain unchanged. No public-launch-ready claim.

References: https://developers.google.com/maps/api-security-best-practices ; https://developers.google.com/maps/documentation/javascript/place-autocomplete-new ; https://developers.google.com/maps/documentation/javascript/reference/advanced-markers .
