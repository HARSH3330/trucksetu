# TransivoX UI design guide

## Product and visual direction

TransivoX connects Indian shippers with independent transport providers. A provider's quotation, explicitly accepted by the customer, sets the final price. The interface must make route entry, quote comparison and operational decisions easier, not imply instant guaranteed capacity or regulated escrow.

Preserve the ink (`#102f2c`), teal (`#0f766e`) and lime (`#c9f04d`) brand, DM Sans typography and existing React/Vite architecture. White work surfaces sit against a restrained green-grey frame. Use 8px corners, no resting shadows, a consistent 16/24/32px spacing rhythm, readable labels and tabular financial figures. Lime identifies the primary action; status requires text as well as colour.

### Taste-skill direction record

The approved restyle uses **design-taste-frontend**, not Sites. Public-page direction: **Quiet instrument**, seed `1212209395`; app direction: **Framed sheet**, seed `1605944390`. The route form is the demonstration, rather than a stock photograph of a truck. Operational screens emphasize the next task and actual records rather than decorative KPI icon tiles.

Subject inventory: pickup and destination; full-truck or shared-space requests; cargo weight; provider quotations; explicit customer acceptance; temporary capacity holds; immutable booking totals; private identity/vehicle review; pickup/delivery confirmation; distinct customer/provider/driver/admin permissions. These constraints are the visual material, not invented shipment statistics.

The homepage argument is: enter a route → choose the appropriate marketplace workflow → inspect actual published requirements → understand quotation and delivery steps → find policy/support answers. Its first action remains **Get transport quotes**. No claim of guaranteed prices, availability or successful verification is added.

Deliberate adaptations: retain existing navigation and FAQ interactions, the brand palette/type and 8px corners; do not replace architecture with a sidebar. No unrelated stock photographs, fabricated proof, decorative motion quota or 30%-viewport empty hero. These would conflict with the approved restrained logistics UI and mobile action visibility. The labelled route diagram is illustrative, never live tracking; hide it on narrow screens so it cannot displace the form.

## Icons: Phosphor only

- Use `@phosphor-icons/react` for **every functional UI icon**. No Lucide, mixed icon libraries, emoji icons or new hand-drawn substitute UI glyphs.
- Use named imports so unused icons are tree-shaken. Existing semantic aliases are allowed; the rendered implementation must be Phosphor.
- Default to `regular`, 20px, `currentColor`; use explicit sizes only for a deliberate hierarchy. The root `IconContext` sets these defaults.
- Decorative icons are `aria-hidden` and not focusable. Keep visible button text; icon-only controls need an explicit accessible name on the button. Never rely on an icon or colour alone for status.
- A branded illustration/route diagram is not a UI icon; keep it separately labelled and do not use it as a substitute button glyph.
- Do not reintroduce `lucide-react` or a second functional icon dependency.

## Layout and interaction rules

- At 390px width, the primary homepage quote action must fit above fixed bottom navigation, including the dependency-unavailable banner.
- Keep 44px minimum interactive targets, keyboard-visible focus and explicit field labels. Do not remove focus outlines to achieve a cleaner look.
- Dashboard metric strips show real API numbers, honest zeroes and unavailable values. Remove decorative metric icon squares; do not hide operational records/actions.
- Keep dashboard panels intrinsically sized rather than stretching an empty summary to the height of an action list. Let tables scroll locally, not the whole page.
- The signed-in navigation may use the explicitly labelled menu to avoid cramming role-specific destinations into the desktop header. All destinations remain available.
- Preserve dialog names, focus containment/restoration, Escape dismissal and scroll locking. External OTP widgets retain their independent lifecycle.
- Respect reduced motion. No animation is required for data to become visible.

## Data and safety

Every API screen needs loading, empty, retryable-error, forbidden/signed-out and populated states. Never disguise unavailable data as zero or show demonstration records as live. Preserve server authorization, malware-scan gates, immutable financial snapshots and finite sessions. Public widget configuration is not a place for backend secrets.

## Verification

Run `npm test`, `npm run build`, and `npx playwright test --config playwright.design.config.ts`. The design suite uses synthetic API responses only, checks the mobile first action, overflow and sign-in focus behavior at 390/768/1440px, and retains failure screenshots/traces with an HTML report. It does not prove real authentication, storage, payments or SMS delivery.

For broader browser coverage use the existing public suite and the guarded local PostgreSQL journey suite. Inspect screenshots at desktop, tablet and mobile sizes; do not report a taste-inspector score as a substitute for functional tests. Design review must explicitly record justified brand/functionality deviations from generic gallery-site rules.
