# Local demand Maps configuration

Use repository-root .env.local (ignored):
```
VITE_GOOGLE_MAPS_BROWSER_KEY=<enter privately in your editor>
VITE_GOOGLE_MAPS_MAP_ID=DEMO_MAP_ID
VITE_API_URL=http://127.0.0.1:18000/api/v1
```
Do not use GOOGLE_MAPS_API_KEY (the existing server Routes adapter) as a VITE variable. Never commit the actual key. Browser-key usage is public by design and must be restricted by website referrer and required APIs.

Actual verified frontend origin http://127.0.0.1:5173/ with isolated API18000. Start local-only Vite with `npm run dev -- --host 127.0.0.1 --port 5173 --strictPort` and ensure VITE_API_URL points only to an approved isolated API. Restart after editing the env file. Website restrictions: http://127.0.0.1:5173/* ; optionally localhost5173 only if used. APIs: Maps JavaScript API and Places API(New). No Routes/Geocoding/legacy Places required. Do not change billing/API enablement without owner approval.

Load the optional map explicitly, search and select a prediction, review private city/address fields. Address/city edits clear stale coordinates. Tap selected endpoint or drag/keyboard-nudge marker; confirm address matches changed pin before publishing, or remove pin. No reverse geocoding or route distance. Map center before selection is only a viewport, never saved as shipment coordinates.

Migration29 adds nullable private pickup_location/destination_location JSON. API must have this additive migration before models query those columns. Owner-only demand responses/editing retain points; discovery omits them. Draft JSON retains optional values and confirmation. Current KYC/ownership/revision checks remain mandatory.

Reproducible simulations: use VITE_GOOGLE_MAPS_BROWSER_KEY=local-simulated-browser-test-key, VITE_API_URL=http://127.0.0.1:8000/api/v1 to build `vite build --config vite.maps-harness.config.ts`, then `playwright test --config playwright.maps.config.ts`. This static test harness has no real auth/KYC/Google/payment integration. Real check is opt-in `E2E_REAL_GOOGLE_MAPS=true` with `playwright test --config playwright.maps-real.config.ts`, running only with the guarded ordinary local API and designated private synthetic account fixture. Never run real Google checks automatically in CI. Tracing/HAR are off; evidence stores no URL query strings or keys.

Before production use a project-owned Map ID, approved production-only key/origins, privacy/storage review and separately authorized migration/API/frontend release. DEMO_MAP_ID is local only. See ../testing/2026-10-25-local-google-maps-verification.md for exact passed/blocked/simulated evidence.
