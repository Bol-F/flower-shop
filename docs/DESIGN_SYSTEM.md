# Bloom & Petal — premium florist redesign

Direction chosen by the owner: understated premium florist, warm white, dark green, refined typography. This is an implementation specification, not a list of new business promises. See [business review](BUSINESS_AND_UX_REVIEW.md) for source-backed rules.

## Visual references

Built-in Image Gen produced coordinated 1536 × 1024 concept screenshots before implementation. The preview originals remain in `C:/Users/User/.codex/generated_images/01a08735-7555-7760-b66a-a1474a3c9cce/`:

| Surface | Reference filename | Anatomy |
| --- | --- | --- |
| Home | `exec-823a6650-961b-486e-b285-fba13350ab50.png` | 70px header, open 44/56 editorial hero, occasion rail, next catalog preview. |
| Catalog + footer | `exec-9b753c90-9393-4733-a674-87323578d3f3.png` | Text categories, visible search/city/sort, four open photo-led products, dark green footer. |
| Product | `exec-fbf0390f-034a-432f-8a16-9dfcc385f7fa.png` | Large photo and thumbnails, open product information, quantity/save/add, disclosures, reviews. |
| Checkout | `exec-9c1d9500-e633-41df-8f0e-27d804552c6b.png` | Two-column form + stone summary, separate delivery/payment, optional details disclosed. |
| Customer account | `exec-b95b5ee0-ac77-4dc6-8e56-54ba4f7c12fe.png` | Orders-first sidebar, divided order rows, separate payment/fulfilment statuses, secondary settings. |
| Staff workspace | `exec-c8e44aef-1218-43b3-a0c2-fff79d22958c.png` | Compact sidebar, searchable order table, pagination, complete detail panel and guarded actions. |

Standalone production hero: `frontend/public/images/florist-hero-v1.png`, generated separately (not cropped from a UI screenshot). Prompt: editorial cream/blush roses and pale tulips with natural greenery, neutral paper and blush ribbon, warm limestone table/plaster wall, natural side light; no text, UI, tint, logo or watermark. Built-in Image Gen, not API/CLI mode.

## Foundation lock

- Background: warm white **#FAF9F6**, not pink, a gradient, or pure white. Primary surface uses the same background; purposeful summary surfaces **#F0EFEB**.
- Primary text/action: botanical green **#203E34**; stronger text **#172E27**. Muted text **#626B65**; rules **#DCDDD5**. Muted rose **#B47A70** is optional and sparing, not the action colour.
- Error/danger remains red; cash due/warnings use muted amber. Green must not make failures look successful.
- Georgia/Times refined serif, normal weight, tight tracking for headings and product names. Sans-serif system/Inter-like controls, normal/medium weight, 14–17px. Do not use heavy uppercase labels everywhere.
- Desktop header 70px; wordmark approximately 36px. Hero heading approximately 96px at 1536px viewport with three deliberate lines; body 21px/1.45. Section headings 44–52px, account heading 80–96px, form subheadings 28–36px. Scale down fluidly on small screens.
- Main horizontal gutter 5vw (20px minimum, 76px at native reference size). Maximum outer container 1536px. Dividing rules, not nested rounded wrappers, organize content.
- Controls: 44–52px minimum height; radius 3–6px, 1px borders. Primary dark-green fill/white text, secondary outline, tertiary underlined text. No oversized pill controls or pink shadows. Focus is visible; selected states are explicit.
- Icons: existing code-native thin outline icon family, 1.7–1.8px strokes, 20–26px; no emoji branding. Filled heart only for a saved product. Arrow/chevron icons are SVG, not text glyphs.
- Photos: untinted, no overlay, stable rectangular crop, no large corner rounding. Product photos remain the actual product's API images; design-reference bouquets must not misrepresent inventory.
- Motion: subtle opacity/colour only, respect reduced motion. No decorative floating/marquee animation.

## Locked public copy and component inventory

English home first viewport: `Bloom & Petal`; `Shop flowers`; `Delivery & payment`; `Flowers for / the moments / that matter.`; `Thoughtfully chosen bouquets from local florists. Find something beautiful to send, or keep.`; `Explore the flowers`; `Delivery & payment`. No hero eyebrow, proof tiles, testimonials, fake statistics or extra promotional badges.

Next section: `Made for every occasion`, actual API categories plus `All flowers`, then `Find your bouquet`; `Search flowers`, `Delivery city`, `Sort`. Category names, prices, counts and stock are dynamic and must use actual API data. Preserve EN/RU/UZ and USD/UZS preferences.

Header has wordmark, two essential links, search, account and bag only. Mobile hides text navigation into a simple accessible menu; search moves focus to the catalog input. Bag links to the full-page checkout/review workflow. Language/currency move to the footer and account preferences.

Footer: wordmark; Explore / Shop flowers / Delivery & payment; Your account / Orders / Saved flowers / Sign in; language and currency selectors; truthful `Demo store · Test payments only`. No invented phone number, opening hours, social destinations, About or Contact links.

Product: real product name/florist/price/stock, current description, quantity, `Add to bag`, `Save`, `Bouquet details`, `Delivery & payment`, `Customer reviews`. Unknown delivery time becomes `Delivery fee and available time slots are confirmed at checkout.` No unsupported live ETA, size variants, photo-before-delivery or guarantee.

Checkout: editable bag, sign-in continuation, `Checkout`, `Back to bag`, `1. Delivery details`, labelled real zone/date/slot/contact fields, optional gift and map/notes, `2. Payment`, real configured methods and explicit test disclaimer, `Your order`, promo, server-backed totals, `Place order`, confirmation/payment continuation/retry. Real API-only zones; manual-confirmation fees are not advertised as free. Preserve current atomic stock/cart/payment safeguards.

Account: `Your account`; Orders / Saved flowers / Profile / Security & connections; Sign out. Actual order rows/details, payment recovery/cancellation eligibility/repeat order. Profile, password and provider connection flows remain usable, but secondary to shopping tasks.

Staff: Orders / Support / Catalog / Settings and Advanced Django admin. Independent permission-aware loads, searchable/paginated queues, order items and instructions, legal next fulfilment action, eligible courier assignment, audited cash collection reason/confirmation. Provider settlement remains read-only. No fake dashboard metrics or expanded staff permissions.

## Continuation and intentional dynamic differences

- Keep Next.js App Router and the existing root StoreProvider; do not replace working OAuth, payment-return or selection state contracts.
- Reference sample order numbers, dates, names, category availability, amounts and photos are illustrative. Render actual data, never seed fake customer records into the production UI.
- The generated checkout footer accidentally includes unsupported About/Contact/social links: use the shared functional footer instead. Dynamic dates cannot copy the generated 2025/2024 examples.
- Mobile: stacked hero, two-column catalog where readable, single-column product/checkout; summary follows form, account/staff navigation becomes a horizontal or wrapped rail, detail table scrolls inside its region without page overflow. No clipped actions or trapped scroll.
- Loading, empty, offline, forbidden and validation states use the same restrained system and honest copy. Existing optional assistant/support features remain available without competing with the main shopping action.
