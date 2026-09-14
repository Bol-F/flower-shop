# Deployment Guide

This guide describes the recommended production setup for Bloom & Petal:

- Backend: Django REST Framework on Render
- Database: Supabase PostgreSQL
- Frontend: Next.js on Vercel
- CI/CD: GitHub Actions

Do not commit real secrets. Set production values in Render, Vercel, Supabase,
or GitHub repository settings.

## 1. Production Checklist

Before the first production deploy:

- Confirm `main` passes GitHub Actions.
- Create a Supabase PostgreSQL database.
- Create a Render web service for `backend/`.
- Create a Vercel project for `frontend/`.
- Set all required environment variables on both platforms.
- Run migrations against the production database.
- Create a production superuser.
- Set CORS and CSRF origins to the exact deployed domains.
- Configure external media storage before relying on uploaded or seeded images.
- Configure exactly one real provider (`payme` or `click`) and verify its test
  credentials/callbacks before accepting production traffic. Production
  settings reject the development test provider.
- Keep email and Telegram disabled until credentials are available.

## 2. Supabase PostgreSQL

1. Create a Supabase project.
2. Open the database connection settings.
3. Copy the PostgreSQL connection string.
4. Use it as `DATABASE_URL` in Render.

Example shape:

```env
DATABASE_URL=postgres://USER:PASSWORD@HOST:5432/postgres?sslmode=require
```

Use the pooled or direct connection recommended by Supabase for your deployment
plan. If Supabase requires SSL, keep `sslmode=require` in the URL.

## 3. Render Backend

Create a new Render Web Service connected to the GitHub repository.

Recommended settings:

| Render setting | Value |
| --- | --- |
| Root directory | `backend` |
| Runtime | Python |
| Python version | from `.python-version` |
| Build command | `pip install -r requirements.txt && python manage.py collectstatic --noinput` |
| Start command | `daphne -b 0.0.0.0 -p $PORT config.asgi:application` |
| Auto deploy | After CI checks pass, if available |

Set this required production variable:

```env
DJANGO_SETTINGS_MODULE=config.settings.production
```

Render also sets `RENDER_EXTERNAL_HOSTNAME`. The production settings add this
hostname to Django `ALLOWED_HOSTS` automatically, but you should still set
`ALLOWED_HOSTS` explicitly for clarity.

### Required Render Environment Variables

```env
DJANGO_SETTINGS_MODULE=config.settings.production
SECRET_KEY=<long-random-production-secret>
DEBUG=False
ALLOWED_HOSTS=<your-render-service>.onrender.com
DATABASE_URL=<supabase-postgres-url>
CORS_ALLOWED_ORIGINS=https://<your-vercel-project>.vercel.app
CSRF_TRUSTED_ORIGINS=https://<your-render-service>.onrender.com
REDIS_URL=redis://...
FRONTEND_URL=https://<your-vercel-project>.vercel.app
OAUTH_FRONTEND_CALLBACK_URL=https://<your-vercel-project>.vercel.app/auth/callback
OAUTH_ATTEMPT_TTL_SECONDS=600
OAUTH_EXCHANGE_TTL_SECONDS=60
OAUTH_HTTP_TIMEOUT_SECONDS=10
```

If you are not running Redis yet, use a managed Redis service before enabling
Celery or Channels features that require it.

### Optional Render Environment Variables

Notifications:

```env
NOTIFICATIONS_ENABLED=true
EMAIL_NOTIFICATIONS_ENABLED=false
EMAIL_HOST=
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_USE_TLS=true
DEFAULT_FROM_EMAIL=
TELEGRAM_NOTIFICATIONS_ENABLED=false
TELEGRAM_BOT_TOKEN=
TELEGRAM_ADMIN_CHAT_ID=
```

Payments:

```env
PAYMENT_PROVIDER=payme
PAYMENT_TEST_MODE_ENABLED=false
PAYMENT_FRONTEND_RETURN_URL=https://<your-vercel-project>.vercel.app/payment/return
PAYMENT_UZS_PER_PRICE_UNIT=12650
PAYME_MERCHANT_ID=<merchant-id>
PAYME_LOGIN=Paycom
PAYME_SECRET_KEY=<merchant-api-password>
PAYME_CHECKOUT_URL=https://checkout.paycom.uz
```

For Click instead, set `PAYMENT_PROVIDER=click` plus `CLICK_SERVICE_ID`,
`CLICK_MERCHANT_ID`, `CLICK_SECRET_KEY`, and
`CLICK_CHECKOUT_URL=https://my.click.uz/services/pay`. Configure the exact
callback URLs from `README.md` in the chosen provider dashboard.

### OAuth environment and provider dashboards

Google, GitHub, and Microsoft are optional independently. A provider is shown
as available only after both its client ID and backend-only client secret are
set. The repository contains no real provider credentials, so a live consent
flow cannot work until you create an application with that provider and add
the values to Render.

For local development, register these exact provider callback URLs (create
separate development and production provider applications where a provider
allows only one callback):

```text
http://localhost:8000/api/auth/oauth/google/callback/
http://localhost:8000/api/auth/oauth/github/callback/
http://localhost:8000/api/auth/oauth/microsoft/callback/
```

The corresponding local backend values are:

```env
FRONTEND_URL=http://localhost:3000
OAUTH_FRONTEND_CALLBACK_URL=http://localhost:3000/auth/callback
OAUTH_ATTEMPT_TTL_SECONDS=600
OAUTH_EXCHANGE_TTL_SECONDS=60
OAUTH_HTTP_TIMEOUT_SECONDS=10

GOOGLE_OAUTH_CLIENT_ID=<google-client-id>
GOOGLE_OAUTH_CLIENT_SECRET=<google-client-secret>
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8000/api/auth/oauth/google/callback/

GITHUB_OAUTH_CLIENT_ID=<github-client-id>
GITHUB_OAUTH_CLIENT_SECRET=<github-client-secret>
GITHUB_OAUTH_REDIRECT_URI=http://localhost:8000/api/auth/oauth/github/callback/

MICROSOFT_OAUTH_CLIENT_ID=<microsoft-application-client-id>
MICROSOFT_OAUTH_CLIENT_SECRET=<microsoft-client-secret-value>
MICROSOFT_OAUTH_REDIRECT_URI=http://localhost:8000/api/auth/oauth/microsoft/callback/
MICROSOFT_OAUTH_TENANT=common
```

For production, replace the two host placeholders below and paste the three
resulting callback URLs exactly into the provider dashboards:

```text
https://<your-render-service>.onrender.com/api/auth/oauth/google/callback/
https://<your-render-service>.onrender.com/api/auth/oauth/github/callback/
https://<your-render-service>.onrender.com/api/auth/oauth/microsoft/callback/
```

Copy-ready Render variables for all three providers:

```env
FRONTEND_URL=https://<your-vercel-project>.vercel.app
OAUTH_FRONTEND_CALLBACK_URL=https://<your-vercel-project>.vercel.app/auth/callback
OAUTH_ATTEMPT_TTL_SECONDS=600
OAUTH_EXCHANGE_TTL_SECONDS=60
OAUTH_HTTP_TIMEOUT_SECONDS=10

GOOGLE_OAUTH_CLIENT_ID=<google-client-id>
GOOGLE_OAUTH_CLIENT_SECRET=<google-client-secret>
GOOGLE_OAUTH_REDIRECT_URI=https://<your-render-service>.onrender.com/api/auth/oauth/google/callback/

GITHUB_OAUTH_CLIENT_ID=<github-client-id>
GITHUB_OAUTH_CLIENT_SECRET=<github-client-secret>
GITHUB_OAUTH_REDIRECT_URI=https://<your-render-service>.onrender.com/api/auth/oauth/github/callback/

MICROSOFT_OAUTH_CLIENT_ID=<microsoft-application-client-id>
MICROSOFT_OAUTH_CLIENT_SECRET=<microsoft-client-secret-value>
MICROSOFT_OAUTH_REDIRECT_URI=https://<your-render-service>.onrender.com/api/auth/oauth/microsoft/callback/
MICROSOFT_OAUTH_TENANT=common
```

`MICROSOFT_OAUTH_TENANT` may be `common`, `organizations`, `consumers`, or an
exact tenant UUID. Production startup rejects frontend URLs that are not HTTPS,
do not share an origin, use localhost, or do not end at the exact
`/auth/callback` route. It also rejects enabled provider callbacks with the
wrong route, query string, fragment, user information, non-HTTPS scheme, or a
hostname absent from `ALLOWED_HOSTS`.

Provider dashboard fields:

- Google Cloud: add the Google callback above as an **Authorized redirect URI**
  on a **Web application** OAuth client.
- GitHub: set **Authorization callback URL** to the GitHub callback above.
- Microsoft Entra: add the Microsoft callback above under
  **Authentication → Web → Redirect URIs**, then create a client secret and
  copy its **value** while it is visible.

After saving credentials, redeploy the backend and confirm
`GET /api/auth/oauth/providers/` reports only the intended providers as
configured before testing each consent flow.

Media/storage placeholders:

```env
CLOUDINARY_URL=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=
AWS_S3_REGION_NAME=
SUPABASE_STORAGE_URL=
SUPABASE_STORAGE_BUCKET=
SUPABASE_STORAGE_SERVICE_KEY=
```

Development stores media on the local filesystem. Production does not serve
`/media/` from Django; use external media storage before relying on uploaded or
seeded images.

## 4. Production Migrations

Run migrations after the first backend deploy and after every deploy that adds
new migrations.

In Render Shell:

```bash
python manage.py migrate
```

Schedule the following maintenance command daily (for example with a Render
Cron Job) so abandoned OAuth attempts and expired one-time codes are removed:

```bash
python manage.py purge_expired_oauth
```

Create a production superuser:

```bash
python manage.py createsuperuser
```

Optional seed data:

```bash
python manage.py seed_flowers
python manage.py download_flower_images
```

Do not run seed commands repeatedly in production unless you understand whether
the command is idempotent for the data you already have.

## 5. Vercel Frontend

Create a Vercel project connected to the same GitHub repository.

Recommended settings:

| Vercel setting | Value |
| --- | --- |
| Root directory | `frontend` |
| Framework | Next.js |
| Install command | `npm ci` |
| Build command | `npm run build` |
| Output | Next.js default |

Required Vercel environment variables:

```env
NEXT_PUBLIC_API_URL=https://<your-render-service>.onrender.com
NEXT_PUBLIC_SITE_URL=https://<your-vercel-project>.vercel.app
```

Do not put backend secrets, SMTP passwords, Telegram bot tokens, or payment
provider secret keys in Vercel `NEXT_PUBLIC_*` variables.

## 6. CORS, CSRF, and Host Setup

For a Vercel frontend calling a Render backend:

Backend `ALLOWED_HOSTS` should include only backend hostnames:

```env
ALLOWED_HOSTS=<your-render-service>.onrender.com
```

Backend `CORS_ALLOWED_ORIGINS` should include frontend origins:

```env
CORS_ALLOWED_ORIGINS=https://<your-vercel-project>.vercel.app,https://www.your-domain.com
```

Backend `CSRF_TRUSTED_ORIGINS` should include trusted HTTPS backend/admin origins:

```env
CSRF_TRUSTED_ORIGINS=https://<your-render-service>.onrender.com
```

If you add a custom frontend domain, add it to `CORS_ALLOWED_ORIGINS`. If you
add a custom backend/admin domain, add it to `ALLOWED_HOSTS` and
`CSRF_TRUSTED_ORIGINS`.

## 7. GitHub Actions and Deployment Flow

The repository includes `.github/workflows/ci.yml`.

On pushes to `main` and on pull requests, CI runs:

Backend:

```bash
python manage.py makemigrations --check --dry-run
pytest
```

Frontend:

```bash
npm run lint
npm run test
npm run build
```

Recommended flow:

1. Create a feature branch.
2. Commit logical changes.
3. Open a pull request or merge when ready.
4. Let GitHub Actions run.
5. Deploy from `main` after checks pass.

If Render and Vercel are connected to GitHub, they can deploy automatically
from `main`. Configure Render to wait for CI checks if your plan supports it.

## 8. Common Deployment Errors

### `DisallowedHost`

Cause: the backend domain is missing from `ALLOWED_HOSTS`.

Fix:

```env
ALLOWED_HOSTS=<your-render-service>.onrender.com
```

### Browser CORS error

Cause: the frontend origin is missing from `CORS_ALLOWED_ORIGINS`.

Fix:

```env
CORS_ALLOWED_ORIGINS=https://<your-vercel-project>.vercel.app
```

Use the exact origin. Include protocol. Do not include a trailing slash.

### CSRF trusted origin error in Django admin

Cause: the backend/admin HTTPS origin is missing from `CSRF_TRUSTED_ORIGINS`.

Fix:

```env
CSRF_TRUSTED_ORIGINS=https://<your-render-service>.onrender.com
```

### Static files are missing

Cause: `collectstatic` did not run or WhiteNoise is not using collected assets.

Fix:

```bash
python manage.py collectstatic --noinput
```

Ensure the Render build command includes `collectstatic`.

### Database connection fails

Causes:

- Wrong Supabase password or host.
- Missing `sslmode=require`.
- Supabase database paused or unreachable.
- Render env variable has a malformed `DATABASE_URL`.

Fix: recopy the Supabase connection string and redeploy.

### Migrations did not run

Cause: code deployed before database schema was updated.

Fix in Render Shell:

```bash
python manage.py migrate
```

### Frontend build cannot reach the backend

The frontend build should not require a live backend for most pages. Runtime API
calls use `NEXT_PUBLIC_API_URL`. If customer flows fail after deploy, confirm:

```env
NEXT_PUBLIC_API_URL=https://<your-render-service>.onrender.com
```

Then confirm the backend CORS setting includes the Vercel origin.

### Notifications fail

Email and Telegram failures should not block checkout. Check Django admin
`NotificationLog` rows for `skipped` or `failed` entries.

Common fixes:

- Enable the channel: `EMAIL_NOTIFICATIONS_ENABLED=true` or `TELEGRAM_NOTIFICATIONS_ENABLED=true`.
- Add complete credentials.
- Verify SMTP host/port/TLS settings.
- Verify Telegram bot token and admin chat id.

### Local test payments do not work

The mock provider is local/development-only. Confirm both settings:

```env
PAYMENT_PROVIDER=test
PAYMENT_TEST_MODE_ENABLED=true
```

For card/online orders, the order should start as `pending` and the customer
can call:

```http
POST /api/orders/{id}/pay-test/
```

Never deploy these values with `config.settings.production`; that settings
module intentionally rejects them.

## 9. Production Verification Commands

Backend:

```bash
python manage.py check --deploy
python manage.py migrate
python manage.py createsuperuser
```

Frontend:

```bash
npm run build
```

Smoke test after deployment:

1. Open the Vercel storefront.
2. Register a customer.
3. Add a product to cart.
4. Place a cash order.
5. Place an online order using the configured provider's test credentials.
6. Finish hosted checkout and confirm the provider callback, not the return
   URL, changed the payment to `paid`.
7. Log in as staff/admin.
8. Confirm the order, payment status, notification logs, and stock changes.
