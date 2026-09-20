# Free public demo deployment

This topology is for a portfolio demo, not a client production shop:

- Vercel Hobby serves `frontend/`.
- Render Free serves the Django API from `backend/`.
- Supabase Free provides PostgreSQL.
- Payments use the explicit test provider and never charge money.
- Authentication is email/password only; OAuth is disabled.
- Checked-in demo images are served by Django and the filesystem is disposable.

## Deploy

1. Create a Supabase project and copy its shared Session pooler connection
   string (port 5432). Append `?sslmode=require` and keep it secret.
2. Create a Render Blueprint from the repository-root `render.yaml`. Enter the
   Supabase connection string for `DATABASE_URL` when prompted.
3. Wait until `https://flower-shop-api-demo.onrender.com/api/products/` returns
   HTTP 200. Migrations and the idempotent `seed_demo` command run on startup.
4. Import the repository into Vercel with `frontend` as the Root Directory and
   deploy it as `flower-shop-demo`.
5. Verify catalog browsing, email registration/login, cart, checkout, and the
   visible test-payment action.

If either generated hostname differs, update the matching values in
`render.yaml` and `frontend/vercel.json` before deploying. Render Free can sleep
after inactivity, so the first API request may take longer. Supabase Free can
pause inactive projects. Do not replace `config.settings.demo` with production
settings until real payment, OAuth, Redis, media storage, notification, and
operational requirements are ready.
