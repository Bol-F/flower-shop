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
4. Import the repository into Vercel with `frontend` as the Root Directory and
   deploy it as `flower-shop-demo`.
5. Verify catalog browsing **including product images**, email login, cart,
   checkout, the test-payment action, and the paid order in history. The test
   provider never charges money.

If either generated hostname differs, update the matching values in
`render.yaml` and `frontend/vercel.json` before deploying. Render Free can sleep
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
https://<actual-backend-host>/api/auth/oauth/google/callback/
```

In the backend hosting environment (Render, not Vercel), configure:

```env
DEMO_OAUTH_ENABLED=true
GOOGLE_OAUTH_CLIENT_ID=<web-client-id>
GOOGLE_OAUTH_CLIENT_SECRET=<backend-only-client-secret>
GOOGLE_OAUTH_REDIRECT_URI=https://<actual-backend-host>/api/auth/oauth/google/callback/
FRONTEND_URL=https://<actual-frontend-host>
OAUTH_FRONTEND_CALLBACK_URL=https://<actual-frontend-host>/auth/callback
CORS_ALLOWED_ORIGINS=https://<actual-frontend-host>
ALLOWED_HOSTS=<actual-backend-host>
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
