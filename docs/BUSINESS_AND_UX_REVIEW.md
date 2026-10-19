# Business logic and UX review

Audit date: 19 October 2026. Scope: repository business rules and shopper/staff workflows before the redesign. Findings below describe the inspected implementation; recommendations are not claims that fixes have shipped. No live orders, external writes, credentials, or environment files were used. Existing tests were read as evidence, not executed for this review.

The shop already supports a substantial ordering workflow. The redesign should make its real capabilities easier to understand, while preserving stock, payment, permissions, and account-linking rules. The chosen visual direction is premium warm white with dark green: editorial flower photography, restrained typography, readable surfaces, and clear actions.

## Verified business flow

| Stage | Existing behavior and rules to preserve | Source |
| --- | --- | --- |
| Discover | Public products filter by city, category, vendor, price, and search. Products have one price and finished-bouquet stock count. Unavailable products are hidden from public API reads; out-of-stock products can remain visible. | [Product model](../backend/apps/products/models.py#L13), [public queryset](../backend/apps/products/views.py#L40), [filters](../backend/apps/products/filters.py#L6) |
| Save selections | Guests keep local cart/favourites. Sign-in merges selections into the account with an idempotent receipt, stock clamping, and unavailable-item reporting. Checkout blocks while cart synchronization is unresolved. | [Guest merge](../backend/apps/cart/services.py#L97), [store synchronization](../frontend/lib/store.tsx#L460) |
| Configure delivery | Checkout requires sign-in, delivery address/contact phone, a nonpast date, and a three-hour time slot. Gift recipient, gift note, call preference, courier note, and optional map coordinates are supported. Zones can require manual confirmation. | [Checkout validation](../backend/apps/orders/serializers.py#L229), [delivery zones](../backend/apps/orders/models.py#L194) |
| Price and reserve | Atomic checkout locks cart/products, rechecks availability/stock, snapshots product names/prices, rejects multiple identified florists, validates promo, computes delivery/discount, reserves stock, and clears the server cart. Noncash provider initialization is inside the transaction. | [Order service](../backend/apps/orders/services.py#L27), [atomic checkout test](../backend/apps/orders/tests.py#L178) |
| Pay | Cash starts unpaid. Card/online uses one configured provider: explicit no-charge test, Payme, or Click. Amounts are snapshotted in UZS using the published conversion rate. Active attempts are reused across retry keys. Verified callbacks establish payment; a browser return does not. | [Capabilities and retries](../backend/apps/orders/payments.py#L97), [payment return](../frontend/app/payment/return/PaymentReturnClient.tsx#L32) |
| Fulfil | Pending → confirmed → preparing → courier picked up → delivered. Staff may skip forward for recovery; terminal orders cannot reopen. Online payment must be verified before preparing onward. Courier eligibility depends on active/on-duty status and city. | [Guarded fulfillment](../backend/apps/orders/fulfillment.py#L17) |
| Cancel or repeat | Unpaid pending/confirmed orders can be cancelled unless provider confirmation is in progress; inventory releases once. Paid orders require refund handling. Repeating an order adds currently available products using current prices/stock and reports skips. | [Cancellation](../backend/apps/orders/payments.py#L382), [repeat order](../backend/apps/marketplace/services.py#L119) |
| Account and support | Email/password and configured social providers use the same application session. Existing-email collisions require sign-in then explicit provider connection in Profile. Customer support saves messages/replies; notification channels are optional. | [Social identity resolution](../backend/apps/users/oauth.py#L414), [link exchange](../backend/apps/users/views.py#L356), [support model](../backend/apps/contact/models.py) |

Additional invariants:

- Server totals are authoritative. Free delivery uses merchandise subtotal before promo discount. Fees and free-delivery thresholds come from the selected zone's city; with no zone, pricing uses its fallback defaults. Keep the same payment-capabilities rate in UZS displays. [Delivery pricing](../backend/apps/orders/pricing.py#L21), [payment amount](../backend/apps/orders/payments.py#L97).
- Order status and payment status are separate. Provider payments cannot be manually marked paid; reasoned manual adjustments are for cash and produce audit events. [Cash adjustment](../backend/apps/orders/payments.py#L450).
- After successful checkout, clear only the frontend snapshot: server order creation already cleared its cart. A delayed remote DELETE could erase newer items from another tab. [Existing checkout safeguard](../frontend/components/Header.tsx#L351).
- Preserve OAuth provider discovery, browser-bound state, single-use exchange/link codes, and explicit linking. Google/GitHub must remain available when configured; matching email alone must never grant access. [OAuth flow](../backend/apps/users/views.py#L194), [collision rule](../backend/apps/users/oauth.py#L453).
- `is_staff` permits admin entry, not all data/actions. Backend model permissions remain authoritative. [Permission helper](../backend/apps/common/permissions.py#L4).

## Prioritized fixes

### P0 — Delivery shown can differ from delivery submitted

Zone loading retains fallback/previous zones on empty responses and uses bundled fallback zones on errors. Bundled Outer/Outside City zones have nonpositive IDs, so checkout submits `delivery_zone_id: null`. The server then uses default delivery pricing and does not retain the displayed manual-confirmation flag. A shopper can therefore see a different fee/confirmation promise from the order created. [Zone loading](../frontend/components/Header.tsx#L178), [fallback zones](../frontend/lib/delivery.ts#L27), [submission](../frontend/components/Header.tsx#L341), [server pricing/flag](../backend/apps/orders/services.py#L94).

Required behavior: use actual API zone IDs for purchasable zone choices; clear stale choices when city changes; distinguish loading, empty, and error states; allow retry. Do not submit a bundled zone as if it were verified. A manual-confirmation zone with a provisional zero fee should say “Fee to be confirmed,” not “Free.” Do not imply that selecting a map point verifies serviceability: checkout does not perform polygon validation.

### P0 — One denied staff capability hides otherwise accessible work

The staff page loads orders, dashboard, and couriers in one `Promise.all`. Dashboard requires both order and product read permissions; couriers require a separate courier permission. A permitted order response is discarded if either other request fails. The frontend auth profile exposes `is_staff`, not a complete capability set. [Coupled loading](../frontend/components/ProfileSettings.tsx#L369), [dashboard permissions](../backend/apps/orders/views.py#L318), [courier permissions](../backend/apps/marketplace/views.py#L33), [auth type](../frontend/lib/api.ts#L35).

Required behavior: independent panel loading/errors; preserve successful results; treat 403 as unavailable capability; show only permitted mutations. Do not solve this by granting every staff user broader permissions. An explicit capability payload would be additive backend work if needed for precise action visibility.

### P1 — Queues hide work and order details omit assembly instructions

Orders fetch the first 100 records and then render only eight without pagination. Support likewise discards pagination after 100 messages across customers, which can omit conversations and distort unread counts. The dashboard queue takes ten active orders without explicit delivery-date/slot priority. Staff order cards omit bouquet items/quantities and courier notes that already exist in the API. [Order fetch](../frontend/lib/api.ts#L993), [eight-order cap](../frontend/components/ProfileSettings.tsx#L754), [support fetch](../frontend/lib/api.ts#L800), [dashboard queue](../backend/apps/orders/views.py#L330), [order fields](../backend/apps/orders/serializers.py#L93).

Required behavior: reachable pagination/search, visible result counts, delivery-date/slot ordering and attention filters, plus an expandable order detail with products, quantities, recipient, slot, address, payment, gift note, and courier instructions. Backend/API changes should be scoped explicitly where complete search or queue ordering is required.

### P1 — Action controls do not reflect legal transitions

Staff see backward/terminal fulfillment buttons and courier assignment after pickup; customers see cancellation during payment confirmation even though the server rejects it. Cash collection is supported by an audited API and Django admin, but absent from the main staff screen. [Staff controls](../frontend/components/ProfileSettings.tsx#L874), [customer cancel](../frontend/components/ProfileSettings.tsx#L1920), [fulfillment rules](../backend/apps/orders/fulfillment.py#L31), [cancellation guard](../backend/apps/orders/payments.py#L404), [cash API](../backend/apps/orders/payments.py#L450).

Required behavior: a clear next action, eligibility-aware courier choices, permission/state-aware controls, and an explanation when blocked. Expose “Record cash received” with a reason and review step; keep provider settlement read-only.

### P1 — Shopper navigation does not expose existing capabilities clearly

Catalog search exists in state but lacks a visible input; footer labels share a catalog fragment regardless of intent; checkout expands inside the header dropdown; account settings precede order history; staff operations are split between Profile, a support-only frontend `/admin`, and Django admin. Multi-florist carts are rejected only at submission, while cart rows omit florist context. [Catalog state](../frontend/components/Catalog.tsx#L31), [cart/checkout container](../frontend/components/Header.tsx#L401), [cart rows](../frontend/components/Header.tsx#L582), [staff support route](../frontend/app/admin/page.tsx#L10), [florist restriction](../backend/apps/orders/services.py#L76).

Required behavior: visible search, accurate destinations, florist context before checkout, a bounded checkout surface, and clear shopper/staff navigation. Preserve Django admin as the advanced management destination until intentionally replaced.

## Redesign information architecture

Six screen groups should share the chosen warm-white/dark-green design system:

| Screen group | Primary purpose and content |
| --- | --- |
| Home | Editorial flower image, concise value proposition, shop/search entry, real categories and delivery context. |
| Catalog | Visible search, category and sort controls, selected city, readable price/stock evidence, loading/empty/offline states. |
| Product | Real photographs, name/florist, description/composition, current price/availability, quantity, save/add actions, reviews. |
| Cart and checkout | Florist/item review, sign-in handoff, delivery/recipient details, verified zone/payment choices, clear total, confirmation and payment recovery. A side panel on desktop/full-screen mobile sheet is a presentation choice, not a new business flow. |
| Customer account | Orders and saved flowers first; delivery/payment states and available actions; profile/security/connected accounts in secondary navigation. |
| Staff workspace | Orders, Support, Catalog, Settings; independent permission-aware panels; complete queues; order detail and guarded actions; explicit advanced-admin link. |

Use fewer competing pills/shadows, strong heading/body contrast, clear field labels, visible focus, adequate touch targets, and responsive layouts. Preserve EN/RU/UZ and USD/UZS behavior, reduced-motion support, cart/favourite persistence, and the existing OAuth/payment callback routes. Concept imagery should illustrate these real flows rather than introduce unsupported controls.

## Existing capabilities versus future work

**Already implemented:** city/category/vendor catalog; one-price products and stock; guest selection merge; favourites; reviews; authenticated checkout; gift/courier notes; optional coordinates; promo validation; cash/test/Payme/Click architecture; payment retries/status polling; fulfillment/courier assignment; guarded cancellation; repeat order; earned loyalty points; support replies; Django inventory/delivery/payment administration. The demo seed creates Tashkent and one florist; enabled cities/providers must come from API capabilities. [Demo setup](../backend/apps/orders/management/commands/seed_demo.py#L278).

**Demo-only or unimplemented:** bundled offline products and their size/sale/ETA data; no-charge test payment; Stripe checkout/webhooks (stub); programmatic provider refund initiation; loyalty redemption; live courier/GPS tracking; route optimization; florist account/settlement portal; stem-level inventory/procurement; support assignment/SLA. Product “photo before delivery” copy has no corresponding implemented photo workflow and must not be presented as verified functionality. [Live product mapping](../frontend/lib/catalog.ts#L106), [Stripe stub](../backend/apps/orders/payment_providers/stripe_provider.py#L14), [photo copy](../frontend/components/ProductDetail.tsx#L200).

Unpaid reservation expiry exists as a scheduled task, but does not run merely because the API starts. Provider status reads local records rather than independently reconciling remote settlement. These are operational limits to preserve in copy and recovery flows, not reasons to weaken payment verification. [Expiry task](../backend/apps/orders/tasks.py#L13), [documented limitations](../README.md#current-limitations).

## Completion checks for implementation

- Verify shopper browsing/search, stock states, guest-to-account cart/favourite merge, and cart sync recovery.
- Check checkout totals and submitted zone IDs against API responses, including city changes, empty/error zone responses, manual confirmation, promo, and gifts.
- Exercise cash versus explicit no-charge test flow; retain secure-provider continuation and callback/polling tests without creating live payments.
- Verify Google/GitHub sign-in and explicit account connection retain their existing contracts and routes.
- Check restricted staff permissions, independent panel errors, complete queue navigation, assembly details, and legal actions.
- Review all six screen groups on desktop/mobile for keyboard access, contrast, overflow, language expansion, and clear error/empty states. Run the existing relevant frontend checks after implementation; do not replace behavior tests with visual inspection alone.
