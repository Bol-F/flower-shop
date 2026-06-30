# Bloom & Petal Flower Delivery Marketplace

Bloom & Petal is a full-stack flower delivery marketplace. It includes a
customer storefront, product catalog, cart, checkout, order tracking, staff
dashboard, stock checks, fake/test payments, notification logs, and support
messages.

The project is designed for a practical production path:

- Frontend: Next.js app deployed on Vercel.
- Backend: Django REST Framework API deployed on Render.
- Database: PostgreSQL, commonly Supabase in production.
- CI/CD: GitHub Actions for backend and frontend checks.

## Tech Stack

| Area | Technology |
| --- | --- |
| Frontend | Next.js, React, TypeScript, Tailwind CSS, Leaflet |
| Backend | Python 3.12, Django 4.2, Django REST Framework |
| Auth | JWT with `djangorestframework-simplejwt` |
| Database | PostgreSQL / Supabase |
| Async-ready services | Redis, Celery, Django Channels, Daphne |
| Static files | WhiteNoise |
| Notifications | Console logs, email channel, Telegram admin channel |
| Payments | Internal workflow, fake/test provider, real-provider placeholders |
| Tests | pytest, pytest-django, Vitest, ESLint |
| Deployment | Render backend, Vercel frontend, GitHub Actions CI |

## Main Features

- Product catalog with categories, search, filtering, sorting, and product detail pages.
- Customer cart and checkout with delivery details, recipient fields, gift notes, and delivery zones.
- Order history with order status timeline and payment status.
- Internal payment workflow with `cash`, `card`, and `online` methods.
- Safe fake/test payment flow for card and online demo orders.
- Provider abstraction prepared for future Click, Payme, or Stripe test-mode integration.
- Staff dashboard for orders, payment status updates, inventory alerts, support messages, and reviews.
- Stock validation during checkout so unavailable quantities cannot be oversold.
- Notification log foundation with console, email, and Telegram channels.
- Customer support messages and staff replies.
- Product reviews.
- Django admin with operational access to products, orders, users, and notification logs.

## Architecture Overview

The backend is the source of truth for catalog data, cart sync, checkout,
payments, notifications, stock validation, users, and staff operations. Views
validate API input and delegate business rules to service modules.

Important backend modules:

- `backend/apps/orders/services.py` creates orders, validates stock, snapshots order items, and triggers payment/notification behavior.
- `backend/apps/orders/payments.py` owns payment status rules and fake/test payment completion.
- `backend/apps/orders/payment_providers/` contains the provider interface, the implemented test provider, and placeholders for real providers.
- `backend/apps/orders/notification_services.py` creates `NotificationLog` rows and sends console/email/Telegram notifications safely.
- `backend/apps/contact/` handles support messages and staff replies.

The frontend is a Next.js storefront and profile/staff interface. It talks to
the Django API through `frontend/lib/api.ts`, stores shared UI state in
`frontend/lib/store.tsx`, and keeps checkout/customer flows inside reusable
components.

## Folder Structure

```text
flower-shop/
  backend/
    apps/
      cart/                 Cart models, serializers, views, services
      categories/           Category API
      contact/              Support/contact messages
      marketplace/          Cities, vendors, couriers, promo/wishlist foundation
      orders/               Checkout, orders, payments, notifications
      products/             Product catalog and seed commands
      reviews/              Product reviews
      users/                Custom user model and auth endpoints
    config/
      settings/             base, development, production settings
      urls.py               API and admin routes
      asgi.py / wsgi.py
    locale/                 Admin translation catalogs
    manage.py
    requirements.txt
    pytest.ini
  frontend/
    app/                    Next.js App Router
    components/             Storefront, checkout, profile, staff components
    lib/                    API client, store, adapters, i18n, fallback data
    package.json
  docs/
    API.md                  API reference
    DEPLOYMENT.md           Render, Supabase, Vercel deployment guide
  .github/workflows/
    ci.yml                  Backend and frontend CI
  docker-compose.yml
  README.md
```

## Prerequisites

- Python 3.12
- Node.js 22 recommended for CI parity
- PostgreSQL 15 or a Supabase PostgreSQL database
- Redis 7 if you want Celery/Channels locally
- Git

Docker Compose is also available for a local stack, but the manual setup below
is the clearest way to understand the project.

## Backend Setup

From the repository root:

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment:

```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create the backend environment file:

```bash
cp .env.example .env
```

Edit `backend/.env` and set at least:

```env
SECRET_KEY=replace-with-a-local-secret
DEBUG=True
DB_NAME=flower_shop_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

Run migrations and start the API:

```bash
python manage.py migrate
python manage.py runserver
```

Backend URLs:

- API root: `http://localhost:8000/api/`
- Django admin: `http://localhost:8000/admin/`

## Frontend Setup

Open a second terminal:

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Frontend URL:

- Storefront: `http://localhost:3000`

The frontend reads `NEXT_PUBLIC_API_URL`. For local development this should
usually be:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SITE_URL=http://localhost:3000
```

## Environment Variables

Example files are committed for safe local setup:

- `backend/.env.example`
- `frontend/.env.example`

Do not commit real `.env` files or secrets.

Backend variable groups:

- Django: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`
- Database: `DATABASE_URL` or `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
- Browser security: `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`
- Redis: `REDIS_URL`
- Notifications: `NOTIFICATIONS_ENABLED`, `EMAIL_NOTIFICATIONS_ENABLED`, SMTP variables, Telegram variables
- Payments: `PAYMENT_PROVIDER`, Stripe/Click/Payme placeholder credentials
- Optional media/storage: Cloudinary, S3, or Supabase Storage placeholders

Frontend variables must be public-safe because `NEXT_PUBLIC_*` values can be
exposed in browser JavaScript:

- `NEXT_PUBLIC_API_URL`
- `NEXT_PUBLIC_SITE_URL`
- Optional public display flags only

Provider secrets, Telegram tokens, SMTP passwords, and Django secrets belong in
the backend environment only.

## Database Setup

For local PostgreSQL, create a database that matches `backend/.env`:

```sql
CREATE DATABASE flower_shop_db;
```

For Supabase, copy the PostgreSQL connection string and set it as
`DATABASE_URL` in Render or in `backend/.env` for a local Supabase-backed run.
If Supabase requires SSL, include `?sslmode=require` in the URL.

Seed a complete demo environment after migrations:

```bash
cd backend
python manage.py seed_demo
```

`seed_demo` is idempotent. It creates or updates demo users, categories,
products, placeholder product images, delivery zones, promo codes, reviews,
support messages, and sample orders with different order/payment statuses.
Running it more than once should not create endless duplicate records.

If you only want the larger catalog fixture from the older product seed command,
you can still run:

```bash
cd backend
python manage.py seed_flowers
python manage.py download_flower_images
```

`download_flower_images` stores files in local media storage for development.
Production does not serve `/media/` from Django; configure external media
storage before relying on uploaded or seeded images.

## Migrations

Run migrations locally:

```bash
cd backend
python manage.py migrate
```

Check that model changes have migrations:

```bash
python manage.py makemigrations --check
```

Create a new migration only when models change:

```bash
python manage.py makemigrations
```

## Creating a Superuser

```bash
cd backend
python manage.py createsuperuser
```

Or promote an existing account:

```bash
python manage.py shell
```

```python
from apps.users.models import User
user = User.objects.get(email="you@example.com")
user.is_staff = True
user.is_superuser = True
user.save()
```

## Running Tests

Backend:

```bash
cd backend
python manage.py makemigrations --check
python manage.py migrate
pytest
```

Frontend:

```bash
cd frontend
npm run lint
npm run test
npm run build
```

GitHub Actions runs the same core backend and frontend checks on pushes and
pull requests.

## Running With Docker

Copy the backend env file first:

```bash
cp backend/.env.example backend/.env
```

Then run:

```bash
docker-compose up --build
```

Services:

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000/api/`
- Django admin: `http://localhost:8000/admin/`
- PostgreSQL: `localhost:5432`

## Payments

The project does not integrate real payment providers yet.

Current behavior:

- `cash` orders are created without a provider charge and remain `unpaid` unless staff changes them.
- `card` and `online` orders use the configured provider and start as `pending`.
- `PAYMENT_PROVIDER=test` is the safe default.
- The test provider creates a fake payment reference and lets the customer click `Pay test order`.
- Staff can manually mark payment status as `paid` or `failed`.
- `paid_at` is set by the backend when payment becomes `paid`.

Real Click, Payme, or Stripe work should be added only with official docs,
test credentials, webhook signature validation, idempotency, and provider tests.

## Notifications

Important order, payment, and support events create `NotificationLog` rows.

Supported channels:

- Console/log fallback for development.
- Customer email notifications when SMTP is enabled and configured.
- Telegram admin notifications when a bot token and admin chat id are configured.

Missing email or Telegram credentials never block checkout. Notification rows
are marked `skipped` or `failed`, and the order/support action continues.

## API Overview

See `docs/API.md` for more detail.

Common endpoints:

| Area | Endpoint |
| --- | --- |
| Auth | `POST /api/auth/register/`, `POST /api/auth/login/`, `GET /api/auth/profile/` |
| Catalog | `GET /api/categories/`, `GET /api/products/`, `GET /api/products/{slug}/` |
| Cart | `GET /api/cart/`, `POST /api/cart/items/`, `PATCH /api/cart/items/{product_id}/` |
| Checkout | `POST /api/orders/create/` |
| Orders | `GET /api/orders/`, `GET /api/orders/{id}/` |
| Test payment | `POST /api/orders/{id}/pay-test/` |
| Staff | `GET /api/orders/dashboard/`, `PATCH /api/orders/{id}/status/`, `PATCH /api/orders/{id}/payment-status/` |
| Support | `POST /api/contact/send/`, `GET /api/contact/admin/messages/` |
| Reviews | `GET /api/reviews/products/{product_id}/`, `POST /api/reviews/products/{product_id}/review/` |

## Deployment Overview

Recommended production setup:

- Supabase PostgreSQL for the database.
- Render web service for the Django backend.
- Vercel project for the Next.js frontend.
- GitHub Actions for CI before deployment.

Short version:

1. Create a Supabase PostgreSQL database.
2. Deploy `backend/` to Render with `DJANGO_SETTINGS_MODULE=config.settings.production`.
3. Set backend env variables on Render.
4. Run migrations on Render.
5. Deploy `frontend/` to Vercel.
6. Set `NEXT_PUBLIC_API_URL` on Vercel to the Render backend URL.
7. Add the Vercel URL to backend `CORS_ALLOWED_ORIGINS`.

Full deployment instructions are in `docs/DEPLOYMENT.md`.

## Demo Accounts

Run `python manage.py seed_demo` to create these local/demo accounts:

| Role | Email | Password | Notes |
| --- | --- | --- | --- |
| Customer | `customer@example.com` | `demo12345` | Use for storefront, cart, checkout, order history, reviews, and support messages |
| Staff | `staff@example.com` | `demo12345` | Has `is_staff=True` for the staff dashboard |

These passwords are for local development and controlled demo environments
only. Do not use demo passwords in production.

For Django admin access, create a separate superuser:

```bash
cd backend
python manage.py createsuperuser
```

## Screenshots

Screenshot files are intentionally not generated in this repository. Capture
real screenshots after running the app with `python manage.py seed_demo`, then
save them under `docs/screenshots/`.

See `docs/SCREENSHOTS.md` for the full capture checklist.

Portfolio placeholders:

![Homepage](docs/screenshots/homepage.png)
![Checkout](docs/screenshots/checkout.png)
![Order History](docs/screenshots/order-history.png)
![Staff Dashboard](docs/screenshots/staff-dashboard.png)
![Support Inbox](docs/screenshots/support-inbox.png)

## Future Improvements

- Add real payment providers with official Click, Payme, or Stripe documentation.
- Add production media storage with Cloudinary, S3, or Supabase Storage.
- Add webhook processing and audit logs for real payment providers.
- Add richer HTML email templates.
- Add customer notification preferences.
- Add courier assignment and courier-facing delivery views.
- Add stronger analytics and reporting for vendors and staff.
- Add end-to-end browser tests for checkout and staff workflows.
