# Public demo deployment

This topology is for a portfolio demo, not a client production shop:

- Vercel Hobby serves `frontend/`.
- Render Free serves the Django API from `backend/`.
- Supabase Free provides PostgreSQL.
- Payments use the explicit test provider and never charge money.
- Authentication defaults to email/password. Real OAuth is an explicit opt-in;
  payment processing remains a no-charge test even when OAuth is enabled.
- Checked-in demo images are served by Django and the filesystem is disposable.

## Deploy

1. Create a Supabase project and copy the PostgreSQL connection string
   recommended for your Render deployment. Use the host and port shown in
   Supabase, add `sslmode=require` if required, and keep the URL secret. A
   persistent IPv4-only backend generally uses the session pooler; confirm
   the current recommendation in the [Supabase connection guide](https://supabase.com/docs/guides/database/connecting-to-postgres).
2. Create a Render Blueprint from the repository-root `render.yaml`. Enter the
   Supabase connection string for `DATABASE_URL` when prompted.
3. Wait until `https://flower-shop-api-demo.onrender.com/api/products/` returns
   HTTP 200. Migrations and the idempotent `seed_demo` command run on startup.
4. Use the existing Vercel project `flower-store` in the `bol-fs-projects` scope,
   linked to `Bol-F/flower-shop`, with `frontend` as the Root Directory. Deploy
   the storefront at `https://flower-store-theta.vercel.app`.
5. Verify catalog browsing **including product images**, email login, cart,
   checkout, the test-payment action, and the paid order in history. The test
   provider never charges money.

If either hostname changes, update the matching values in `render.yaml`,
`frontend/vercel.json`, and the hosting environment settings before deploying.
`FRONTEND_URL`, `CORS_ALLOWED_ORIGINS`, `OAUTH_FRONTEND_CALLBACK_URL`, and
`PAYMENT_FRONTEND_RETURN_URL` must use the same frontend origin. Render Free can sleep
after inactivity, so the first API request may take longer. Supabase Free can
pause inactive projects. Do not replace `config.settings.demo` with production
settings until real payment, OAuth, Redis, media storage, notification, and
operational requirements are ready.

Demo accounts and seeded orders are public sample data. Do not put real
customer records, private provider credentials, or production API keys in the
demo database. See the [screenshot gallery](SCREENSHOTS.md) for the expected
customer and staff views.

## Enable real Google sign-in on the demo

In Google Auth Platform, select the intended project, configure Branding and
Audience, and create a **Web application** OAuth client. For an external app in
testing, add the Google accounts that will test it. Register the exact Django
callback, not the Vercel frontend callback:

```text
https://flower-shop-api-demo.onrender.com/api/auth/oauth/google/callback/
```

In the backend hosting environment (Render, not Vercel), configure:

```env
DEMO_OAUTH_ENABLED=true
GOOGLE_OAUTH_CLIENT_ID=<web-client-id>
GOOGLE_OAUTH_CLIENT_SECRET=<backend-only-client-secret>
GOOGLE_OAUTH_REDIRECT_URI=https://flower-shop-api-demo.onrender.com/api/auth/oauth/google/callback/
FRONTEND_URL=https://flower-store-theta.vercel.app
OAUTH_FRONTEND_CALLBACK_URL=https://flower-store-theta.vercel.app/auth/callback
CORS_ALLOWED_ORIGINS=https://flower-store-theta.vercel.app
PAYMENT_FRONTEND_RETURN_URL=https://flower-store-theta.vercel.app/payment/return
ALLOWED_HOSTS=flower-shop-api-demo.onrender.com
```

Redeploy the backend, then check `/api/auth/oauth/providers/`: Google should be
enabled. Exercise sign-in through the storefront and linking from an already
authenticated Profile. Existing local accounts must connect Google explicitly;
matching email alone never grants access. Never put the client secret in a
`NEXT_PUBLIC_*` variable, Git, screenshots, or chat. Confirm new credential
creation before proceeding; a Google account alone is not an OAuth client.

Public demo OAuth startup rejects partial credentials, insecure/incorrect
callbacks, and callback hosts absent from `ALLOWED_HOSTS`. The default remains
off and test payments remain enforced. For a real shop, follow the production
guide instead. See [Google's web-server OAuth documentation](https://developers.google.com/identity/protocols/oauth2/web-server).

## Enable GitHub login and registration

Register a dedicated GitHub OAuth App with homepage
`https://flower-store-theta.vercel.app` and this exact redirect URI:

```text
https://flower-shop-api-demo.onrender.com/api/auth/oauth/github/callback/
```

Leave wildcard matching and device flow disabled. Keep expiring access tokens
enabled: the backend uses GitHub's token only to verify identity during the
callback, then issues its own application session. Do not reuse another app's
client secret.

Add these settings only to the Render backend, leaving the Google settings intact:

```env
GITHUB_OAUTH_CLIENT_ID=<github-client-id>
GITHUB_OAUTH_CLIENT_SECRET=<backend-only-client-secret>
GITHUB_OAUTH_REDIRECT_URI=https://flower-shop-api-demo.onrender.com/api/auth/oauth/github/callback/
```

Keep `DEMO_OAUTH_ENABLED=true` and the shared frontend/callback origins above.
Redeploy and confirm GitHub is enabled in `/api/auth/oauth/providers/`. The app
requests `read:user user:email`, never repository or write scopes.

"Continue with GitHub" handles both login and first-time registration when the
provider supplies a verified email. An existing email/Google account must sign in
first and use **Profile → Connect GitHub**; matching email never auto-links
accounts. After connection, GitHub signs in to that same account. Check login,
session refresh, and preserved cart/favourites without placing a real payment.
