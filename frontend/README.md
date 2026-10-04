# Bloom & Petal storefront

Next.js 16 and React 19 storefront for the [Bloom & Petal marketplace](../README.md).
The Django API owns product prices, stock, checkout totals, orders, and payment
status. This app never receives merchant secrets.

## Start locally

From `frontend/`:

```powershell
npm ci
Copy-Item .env.example .env.local
npm run dev
```

Use `NEXT_PUBLIC_API_URL=http://localhost:8000` for local Django. For a
separate production API, set the variable to its HTTPS origin. Without an
explicit production value, the client uses its own origin; it does not guess an
unencrypted port-8000 API. Every `NEXT_PUBLIC_*` value is visible to browsers,
so never place a secret in one.

When Django is unavailable, the catalog shows bundled **demo** products with
an offline warning. Account, cart sync, checkout, and real payment flows still
require the API.

## Quality checks

```powershell
npm run lint
npm test
npm run format:check
npm run build
```

The main integration points are `lib/api.ts` (HTTP/auth client), `lib/catalog.ts`
(API-to-UI product mapping), `lib/store.tsx` (preferences and cart), and
`components/Header.tsx` (checkout). Payment options and the UZS conversion
rate come from `/api/orders/payment-methods/`; the payment attempt returned by
Django supplies the authoritative charge amount.

See the [API reference](../docs/API.md), [deployment guide](../docs/DEPLOYMENT.md),
and [screenshot gallery](../docs/SCREENSHOTS.md) for the full flow.
