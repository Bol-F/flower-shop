# Bloom & Petal Flower Delivery Marketplace

Bloom & Petal is a full-stack flower marketplace with a Next.js storefront and
a Django REST API. Customers can browse the catalog, manage a cart, schedule a
delivery, sign in with email or OAuth, pay through a hosted provider, and track
orders. Staff can manage fulfillment, inventory, support, and audited cash
adjustments.

## Stack

| Area | Technology |
| --- | --- |
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS, Leaflet |
| Backend | Python 3.12, Django 4.2, Django REST Framework |
| Authentication | SimpleJWT plus Google, GitHub, and Microsoft OAuth/OIDC |
| Database | PostgreSQL in development/production; SQLite in isolated tests |
| Payments | Payme hosted checkout + Merchant API, Click hosted checkout + Shop API, development-only test provider, cash |
| Async-ready services | Redis, Celery, Django Channels, Daphne |
| Tests | pytest, pytest-django, Vitest, Testing Library, ESLint |

## What is implemented

- Catalog, search, filters, product details, cart synchronization, and stock
  checks under database locks during checkout.
- Delivery zones, map coordinates, recipient details, gift notes, promos,
  courier assignment, order history, and fulfillment timelines.
- Email/password JWT login and backend-owned OAuth authorization-code flows for
  Google, GitHub, and Microsoft. OAuth uses state, PKCE S256, OIDC nonce,
  signed-token verification, short-lived one-time exchange codes, and stable
  provider subject identifiers.
- Authenticated provider linking in Profile. A provider email is only used for
  automatic account matching when that provider proves it is verified;
  ambiguous matches must be linked from an already authenticated account.
- Idempotent payment initialization and persisted `PaymentAttempt` and
  append-only `PaymentEvent` records.
- Payme JSON-RPC methods: `CheckPerformTransaction`, `CreateTransaction`,
  `PerformTransaction`, `CancelTransaction`, `CheckTransaction`, and
  `GetStatement`, with Basic authentication and an optional production IP
  allowlist.
- Click prepare/complete callbacks with constant-time MD5 signature comparison,
  amount/action/service validation, duplicate handling, and cancellation.
- Provider-hosted checkout redirects. The browser return page only polls the
  backend; it never marks a payment paid. Only a verified provider callback or
  an explicit development test action can do that.
- One-time inventory release for cancelled unpaid provider orders, payment
  notifications after committed provider transitions, and staff-readable audit
  history. Manual payment mutations are restricted to authenticated staff and
  cash orders.
- Customer support, reviews, notification logs, loyalty points, and Django
  admin operations.

## Architecture

The backend is the source of truth for identities, stock, prices, orders, and
payments. The frontend renders provider capabilities returned by the backend;
no provider secret is shipped to browser JavaScript.

Important modules:

- `backend/apps/users/oauth.py` builds authorization requests, exchanges codes,
  verifies OIDC tokens, retrieves the GitHub profile, and resolves account
  linking rules.
- `backend/apps/users/models.py` stores stable social identities and hashed,
  expiring OAuth state/exchange records. Provider access/refresh tokens are not
  persisted.
- `backend/apps/orders/payments.py` owns provider selection, idempotent payment
  creation, legal state transitions, audit events, and inventory release.
- `backend/apps/orders/payment_webhooks.py` implements the Payme Merchant API
  and Click Shop API callback protocols.
- `backend/apps/orders/payment_providers/` creates hosted provider checkout
  URLs. Stripe remains an explicit, disabled placeholder.
- `frontend/lib/api.ts` is the typed API client. `frontend/components/Header.tsx`
  owns checkout, while `/auth/callback` and `/payment/return` finish browser
  redirects safely.

## Prerequisites

- Python 3.12
- Node.js 22 recommended
- PostgreSQL 15+
- Redis 7 when using Channels/Celery beyond their local fallbacks

## Local setup

Backend, from the repository root:

```powershell
cd backend
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Create `flower_shop_db` first or point the `DB_*` variables in `backend/.env`
to an existing PostgreSQL database. The API runs at `http://localhost:8000/api/`
and Django admin at `http://localhost:8000/admin/`.

Frontend, in a second terminal:

```powershell
cd frontend
npm ci
Copy-Item .env.example .env.local
npm run dev
```

The storefront runs at `http://localhost:3000`. For local development:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SITE_URL=http://localhost:3000
```

Only the backend receives OAuth client secrets, payment secrets, SMTP
credentials, or Django secrets. Every `NEXT_PUBLIC_*` value is public.

## OAuth provider setup

OAuth is optional per provider. The UI disables any provider without both a
client ID and client secret.

### Google

1. In Google Cloud Console, configure the OAuth consent screen.
2. Create a Web application OAuth client.
3. Add the exact authorized redirect URI
   `http://localhost:8000/api/auth/oauth/google/callback/` locally and its HTTPS
   backend equivalent in production.
4. Set `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`, and
   `GOOGLE_OAUTH_REDIRECT_URI` on the backend.

The backend requests `openid profile email`, verifies the ID-token signature
against Google's JWKS, and validates audience, expiry, issuer, subject, and
nonce. The Google `sub`, not email, is the persistent identity key.

### GitHub

1. In GitHub **Settings → Developer settings → OAuth Apps**, create an OAuth
   App.
2. Use the storefront as the homepage URL.
3. Set the authorization callback URL to
   `http://localhost:8000/api/auth/oauth/github/callback/` locally or the exact
   HTTPS backend URL in production.
4. Set `GITHUB_OAUTH_CLIENT_ID`, `GITHUB_OAUTH_CLIENT_SECRET`, and
   `GITHUB_OAUTH_REDIRECT_URI` on the backend.

The backend requests `read:user user:email`, retrieves `/user` and
`/user/emails`, accepts only a verified email, and keys the identity by the
stable numeric GitHub user ID.

### Microsoft

1. In Microsoft Entra admin center, create an App registration.
2. Add a **Web** redirect URI at
   `http://localhost:8000/api/auth/oauth/microsoft/callback/` locally and the
   exact HTTPS backend URI in production.
3. Create a client secret and choose a tenant policy (`common`,
   `organizations`, `consumers`, or a tenant ID).
4. Set `MICROSOFT_OAUTH_CLIENT_ID`, `MICROSOFT_OAUTH_CLIENT_SECRET`,
   `MICROSOFT_OAUTH_REDIRECT_URI`, and `MICROSOFT_OAUTH_TENANT`.

Microsoft's signed `sub` is used as the identity key. Email and
`preferred_username` are treated as mutable and therefore cannot silently link
an existing local account; use Profile → Connected accounts for that case.

OAuth redirects always terminate at the Django callback. Django then sends an
opaque, single-use code to `OAUTH_FRONTEND_CALLBACK_URL`; the frontend exchanges
it for the same SimpleJWT access/refresh pair used by password login. JWTs and
provider tokens are never put in redirect URLs.

## Payment provider setup

Set exactly one backend `PAYMENT_PROVIDER`: `payme`, `click`, or `test` for
local development. Production settings reject `test` and incomplete real
provider configuration.

Shared variables:

```env
PAYMENT_PROVIDER=payme
PAYMENT_TEST_MODE_ENABLED=false
PAYMENT_FRONTEND_RETURN_URL=https://shop.example.com/payment/return
PAYMENT_UZS_PER_PRICE_UNIT=12650
```

`PAYMENT_UZS_PER_PRICE_UNIT` converts this repository's existing price unit to
UZS at payment initialization. The resulting amount is snapshotted on the
payment and must match every callback exactly.

### Payme

```env
PAYME_MERCHANT_ID=<merchant-id>
PAYME_LOGIN=Paycom
PAYME_SECRET_KEY=<merchant-api-password>
PAYME_CHECKOUT_URL=https://checkout.paycom.uz
PAYME_ALLOWED_IPS=185.234.113.1,...,185.234.113.15
```

In the Payme merchant cabinet, configure the Merchant API endpoint as:

```text
https://api.example.com/api/orders/payments/payme/webhook/
```

Configure Basic authentication to match `PAYME_LOGIN` and
`PAYME_SECRET_KEY`. The hosted checkout account field is `payment_id`. Keep the
official Paycom address range in `PAYME_ALLOWED_IPS`; production checks both IP
and credentials. Sandbox and production credentials must be kept separate.

### Click

```env
CLICK_SERVICE_ID=<service-id>
CLICK_MERCHANT_ID=<merchant-id>
CLICK_SECRET_KEY=<secret-key>
CLICK_CHECKOUT_URL=https://my.click.uz/services/pay
```

In the Click merchant dashboard, configure:

```text
Prepare URL:  https://api.example.com/api/orders/payments/click/prepare/
Complete URL: https://api.example.com/api/orders/payments/click/complete/
```

The checkout `transaction_param` is the public payment UUID. Callback
signatures and amounts are verified before a state transition. Use Click test
credentials first, then rotate to production credentials in the deployment
secret store.

### Development test provider

```env
PAYMENT_PROVIDER=test
PAYMENT_TEST_MODE_ENABLED=true
```

This produces a visible “Pay test order” action and never charges money.
`config.settings.production` forces this mode off even if an environment value
is accidentally supplied.

## Payment state and retry behavior

1. Checkout creates an order and reserves inventory.
2. `POST /api/orders/{order_id}/payments/` creates one payment for a supplied
   idempotency key and returns a hosted checkout URL.
3. Retrying the same key returns the original attempt. A browser refresh can
   continue an active attempt from order history.
4. Payme/Click calls the backend callback; only a verified, legal transition is
   persisted.
5. The provider returns the browser to `/payment/return`, which polls
   `GET /api/orders/{order_id}/payments/{payment_id}/` until a terminal state.
6. Duplicate callbacks return deterministic provider responses and do not
   create duplicate payment events. Cancelling an unpaid order releases stock
   once.

## Environment variables

See `backend/.env.example` and `frontend/.env.example`. The main backend groups
are:

- Django/database: `SECRET_KEY`, `ALLOWED_HOSTS`, `DATABASE_URL` or `DB_*`.
- Browser origins: `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`,
  `FRONTEND_URL`.
- OAuth: provider client ID/secret/redirect URI plus
  `OAUTH_FRONTEND_CALLBACK_URL`.
- Payments: shared `PAYMENT_*` settings plus the chosen Payme or Click group.
- Notifications: SMTP and Telegram settings; missing optional channels do not
  block checkout.

## Migrations and tests

```powershell
cd backend
python manage.py makemigrations --check
python manage.py migrate
python -m pytest -q

cd ..\frontend
npm run lint
npm test -- --run
npm run build
```

OAuth and payment tests mock external provider responses but exercise state,
PKCE/nonce handling, account collisions, invalid/duplicate callbacks,
idempotency, signatures, wrong amounts, cancellation, inventory release, and
illegal payment transitions. Live Payme/Click sandbox and live OAuth consent
screens require credentials supplied by the project owner.

## Security notes

- OAuth state and frontend exchange codes are random, hashed at rest, expiring,
  and consumed under a database lock. PKCE verifier and nonce are cleared after
  the callback attempt.
- OIDC signatures use a strict RS256 allowlist and provider JWKS. Audience,
  expiry, nonce, issuer, and subject are required.
- Provider tokens are used only for the immediate backend profile request and
  are not logged or stored.
- Payment callbacks use provider authentication/signatures, exact amount and
  account checks, constant-time comparisons, row locks, legal state machines,
  unique external IDs, and append-only audit events.
- Provider-backed payments cannot be marked paid from staff UI/API. Staff can
  make reasoned, audited adjustments only for cash orders.
- The browser return URL is informational. Query parameters are not proof of
  payment.

## Deployment and API reference

- [API reference](docs/API.md)
- [Deployment guide](docs/DEPLOYMENT.md)
- [Screenshot checklist](docs/SCREENSHOTS.md)

Recommended production topology remains Vercel for the frontend, Render for
the Django service, and PostgreSQL/Supabase for the database. Run migrations
before exposing provider callbacks and use HTTPS for every production OAuth,
payment, frontend, and API URL.

## Current limitations

- Real provider credentials were not included in the repository, so live OAuth
  consent and Payme/Click sandbox transactions cannot be verified by automated
  tests here.
- One payment provider is enabled per backend deployment.
- Programmatic provider refunds are not initiated by this app; Payme reversal
  callbacks are recorded, while Click refunds remain an operational provider
  workflow.
- Stripe has no checkout/webhook implementation and is rejected in production.
- Uploaded production media still needs an external storage integration.
