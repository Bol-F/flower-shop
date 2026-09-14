# Bloom & Petal API Reference

Example base URL: `https://api.example.com`

JSON endpoints use `Content-Type: application/json`. Authenticated endpoints
expect `Authorization: Bearer <access-token>`. Password and OAuth login both
issue the same SimpleJWT access/refresh pair.

## Authentication

| Method | Endpoint | Auth | Purpose |
| --- | --- | --- | --- |
| `POST` | `/api/auth/register/` | No | Create an email/password account |
| `POST` | `/api/auth/login/` | No | Issue JWTs and return the profile |
| `POST` | `/api/auth/token/refresh/` | No | Refresh an access token |
| `GET/PATCH` | `/api/auth/profile/` | JWT | Read/update profile and connected providers |
| `POST` | `/api/auth/profile/password/` | JWT | Change password |
| `GET` | `/api/auth/oauth/providers/` | No | Provider capability list |
| `GET` | `/api/auth/oauth/{provider}/start/` | No | Begin OAuth login with a backend redirect |
| `POST` | `/api/auth/oauth/{provider}/link/` | JWT | Begin authenticated account linking |
| `GET` | `/api/auth/oauth/{provider}/callback/` | Provider | Backend callback registered with the provider |
| `POST` | `/api/auth/oauth/exchange/` | No | Consume the one-time frontend code and issue JWTs |
| `POST` | `/api/auth/oauth/link/exchange/` | JWT | Finalize a one-time account-link code for its initiating user |

Supported provider path values are `google`, `github`, and `microsoft`.

### Provider capabilities

```http
GET /api/auth/oauth/providers/
```

```json
{
  "providers": [
    {"id": "google", "enabled": true},
    {"id": "github", "enabled": false},
    {"id": "microsoft", "enabled": true}
  ]
}
```

### Browser OAuth login

Navigate the browser to:

```text
GET /api/auth/oauth/google/start/?next=/profile
```

`next` must be a relative same-site path; unsafe values are replaced with
`/profile`. Django creates an expiring one-time attempt, binds its hashed state
to the initiating browser's HttpOnly/SameSite session, and redirects to the
provider with PKCE S256 and (for OIDC providers) nonce. The provider returns to
Django, not directly to Next.js. A valid state copied to another browser is
rejected.

After provider verification Django redirects to:

```text
https://shop.example.com/auth/callback#code=<opaque-one-time-code>&next=%2Fprofile
```

The fragment is not sent in the frontend HTTP request or referrer. Client code
removes it before exchanging the opaque code, which is not a JWT and expires
after 60 seconds by default. Exchange it once:

```http
POST /api/auth/oauth/exchange/
Content-Type: application/json

{"code": "opaque-one-time-code"}
```

```json
{
  "access": "<simplejwt-access>",
  "refresh": "<simplejwt-refresh>",
  "user": {
    "id": 42,
    "username": "flower-friend",
    "email": "friend@example.com",
    "social_identities": [
      {"provider": "google", "email": "friend@example.com", "email_verified": true}
    ]
  }
}
```

Invalid, expired, or already-used codes return `400` with code
`invalid_exchange`.

### Authenticated provider linking

```http
POST /api/auth/oauth/microsoft/link/
Authorization: Bearer <access-token>

{}
```

```json
{"authorization_url": "https://login.microsoftonline.com/..."}
```

Navigate to that URL. On success the backend redirects to
`/auth/callback#link_code=...`. The callback page submits that code with the
existing JWT to finish linking:

```http
POST /api/auth/oauth/link/exchange/
Authorization: Bearer <access-token>
Content-Type: application/json

{"code": "opaque-one-time-link-code"}
```

No social identity is changed before this authenticated finalization. The code
is accepted only for the active user who began the link and only once. A
successful response is `{ "user": { ... } }` with the refreshed
`social_identities` list. If the stable provider identity belongs to another
user, finalization fails with `identity_in_use`.

The backend automatically matches a local account by email only when the
provider proves that email verified. An unverified email collision returns
`account_exists` and requires this authenticated linking flow.

## Catalog and marketplace

| Method | Endpoint | Notes |
| --- | --- | --- |
| `GET` | `/api/categories/` | Category list |
| `GET` | `/api/products/` | `search`, `category`, `city`, `vendor`, price, and ordering filters |
| `GET` | `/api/products/{slug}/` | Product detail and stock metadata |
| `GET` | `/api/marketplace/cities/` | Active cities |
| `GET` | `/api/marketplace/vendors/` | Active vendors |
| `GET` | `/api/marketplace/couriers/` | Staff-only couriers |
| `POST` | `/api/marketplace/promo-codes/validate/` | Validate `{code, subtotal}` |
| `GET/POST` | `/api/marketplace/wishlist/` | List/add wishlist items |
| `DELETE` | `/api/marketplace/wishlist/{product_id}/` | Remove wishlist item |

## Cart, checkout, and orders

| Method | Endpoint | Auth | Purpose |
| --- | --- | --- | --- |
| `GET/DELETE` | `/api/cart/` | JWT | Read or clear cart |
| `POST` | `/api/cart/items/` | JWT | Add `{product_id, quantity}` |
| `PATCH/DELETE` | `/api/cart/items/{product_id}/` | JWT | Update/remove a line |
| `GET` | `/api/orders/delivery-zones/?city=tashkent` | No | Delivery choices |
| `POST` | `/api/orders/create/` | JWT | Create an order and reserve stock |
| `GET` | `/api/orders/` | JWT | Own orders; staff sees all |
| `GET` | `/api/orders/{id}/` | JWT | Order detail |
| `POST` | `/api/orders/{id}/repeat/` | JWT | Add available items to cart |

`POST /api/orders/create/` accepts delivery/recipient fields,
`payment_method` (`cash`, `card`, or `online`), `city_slug`, `delivery_zone_id`,
and `promo_code`. `card` and `online` select the backend's configured online
provider. The response contains `latest_payment` when development test mode
pre-created one; real provider payment initialization is the explicit next
request.

## Payments

| Method | Endpoint | Auth | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/orders/payment-methods/` | No | Runtime capabilities and labels |
| `POST` | `/api/orders/{order_id}/payments/` | Owner JWT | Idempotently initialize hosted checkout |
| `GET` | `/api/orders/{order_id}/payments/{payment_uuid}/` | Owner/staff JWT | Read authoritative payment state |
| `POST` | `/api/orders/{order_id}/pay-test/` | Owner JWT | Development-only mock completion |

### Capabilities

```json
{
  "methods": [
    {
      "id": "cash",
      "payment_method": "cash",
      "provider": "cash",
      "label": "Cash",
      "detail": "Pay when your flowers arrive",
      "enabled": true,
      "test_mode": false
    },
    {
      "id": "payme",
      "payment_method": "online",
      "provider": "payme",
      "label": "Payme",
      "detail": "Secure payment on the provider checkout page",
      "enabled": true,
      "test_mode": false
    }
  ]
}
```

An incompletely configured provider is returned with `enabled: false`. Test
mode appears only when the explicit local setting is enabled.

### Initialize payment

```http
POST /api/orders/91/payments/
Authorization: Bearer <access-token>
Idempotency-Key: checkout-91-payme
Content-Type: application/json

{"provider": "payme"}
```

The key can alternatively be supplied as `idempotency_key` in JSON. A new
attempt returns `201`; retrying the same `(order, provider, key)` returns the
same attempt with `200`.

```json
{
  "id": "a87f62fb-bfb8-4f30-81a0-f8746f427f78",
  "order_id": 91,
  "provider": "payme",
  "amount": "505999.00",
  "currency": "UZS",
  "status": "pending",
  "checkout_url": "https://checkout.paycom.uz/...",
  "provider_reference": "a87f62fb-bfb8-4f30-81a0-f8746f427f78",
  "failure_code": "",
  "failure_message": "",
  "paid_at": null,
  "created_at": "2026-09-09T12:00:00Z",
  "updated_at": "2026-09-09T12:00:00Z"
}
```

Statuses are `created`, `pending`, `processing`, `paid`, `failed`, `cancelled`,
and `refunded`. The client should redirect to `checkout_url`, then poll the GET
endpoint after the provider return. Never infer payment success from return URL
parameters.

### Payme Merchant API callback

```text
POST /api/orders/payments/payme/webhook/
Authorization: Basic base64(PAYME_LOGIN:PAYME_SECRET_KEY)
Content-Type: application/json
```

Example check request; Payme amounts are integer tiyin:

```json
{
  "jsonrpc": "2.0",
  "id": 123,
  "method": "CheckPerformTransaction",
  "params": {
    "amount": 50599900,
    "account": {"payment_id": "a87f62fb-bfb8-4f30-81a0-f8746f427f78"}
  }
}
```

```json
{"result": {"allow": true}, "id": 123}
```

The handler implements check, create, perform, cancel, transaction status, and
statement requests. It returns JSON-RPC/provider error objects with HTTP 200,
checks Basic credentials in constant time, validates amount/account/currency,
locks rows during transitions, and safely handles provider retries. Production
also enforces `PAYME_ALLOWED_IPS` when configured.

### Click Shop API callbacks

```text
POST /api/orders/payments/click/prepare/
POST /api/orders/payments/click/complete/
Content-Type: application/x-www-form-urlencoded
```

Prepare (`action=0`) signature input:

```text
md5(click_trans_id + service_id + SECRET_KEY + merchant_trans_id + amount + action + sign_time)
```

Complete (`action=1`) inserts `merchant_prepare_id` before `amount`. The
endpoints validate `sign_string`, `service_id`, action, amount, payment UUID,
Click transaction ID, and prepare ID. They return the standard numeric Click
`error` and `error_note` fields. Duplicate completion of an already-paid
payment returns `-4` without changing state.

## Staff operations

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/orders/dashboard/` | Analytics, delivery queue, inventory alerts |
| `PATCH` | `/api/orders/{id}/status/` | Fulfillment status update |
| `PATCH` | `/api/orders/{id}/courier/` | Assign `{courier_id}` |
| `PATCH` | `/api/orders/{id}/payment-status/` | Audited cash-order adjustment only |

Manual provider-backed payment changes are rejected. Cash adjustment example:

```json
{
  "payment_status": "paid",
  "reason": "Cash receipt confirmed by shift lead",
  "payment_provider": "manual",
  "payment_reference": "cash-receipt-0182"
}
```

The staff user, reason, previous/new status, and safe reference metadata are
stored in `PaymentEvent`. Payment attempts/events are read-only in Django admin
and cannot be deleted there.

## Reviews and support

| Method | Endpoint | Notes |
| --- | --- | --- |
| `GET` | `/api/reviews/products/{product_id}/` | Rating/review summary |
| `POST/DELETE` | `/api/reviews/products/{product_id}/review/` | Review upsert/delete |
| `POST` | `/api/contact/send/` | Create support message |
| `GET` | `/api/contact/my-messages/` | Customer support history |
| `GET` | `/api/contact/admin/messages/` | Staff support queue |
| `POST` | `/api/contact/admin/messages/{id}/reply/` | Staff reply |

## Error and retry guidance

- API validation errors use standard DRF `400` field messages; ownership
  failures intentionally return `404` where appropriate.
- OAuth callback errors are safe codes/messages on `/auth/callback`; provider
  authorization codes and tokens are never echoed.
- Reuse the same idempotency key when retrying payment initialization after a
  timeout. Do not create a new order merely because checkout navigation failed.
- Provider callbacks are the authority. A pending return page should continue
  polling or tell the customer to check order history.
- Webhook audit metadata excludes raw credentials, authorization headers, and
  full untrusted payloads.
