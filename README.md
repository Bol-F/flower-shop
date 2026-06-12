<div align="center">

# 🌸 Bloom & Petal

**Flower delivery marketplace — Django REST Framework API + Next.js frontend**

A trilingual Django admin & REST API (products, cart, orders, support chat) paired with **Gulora** — a premium Tashkent flower-marketplace UI with original illustrated bouquets.

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-4.2-092E20?logo=django&logoColor=white)
![DRF](https://img.shields.io/badge/DRF-3.14-A30000?logo=django&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white)
![Tests](https://img.shields.io/badge/tests-45_passing-success)
![License](https://img.shields.io/badge/license-MIT-blue)

</div>

---

## ✨ Features

### 🌸 Gulora marketplace UI (frontend)
- Premium one-page marketplace: trust bar, sticky header with search / location / currency, hero with floating proof cards
- Horizontally scrollable category chips, catalog with **working sort & delivery-today filter**
- Product cards with badges, ratings, favorites, hover quick-buy — 4/2/1 column responsive grid
- Gift finder by occasion and an **interactive bouquet builder** with live recolored preview
- Original illustrated SVG bouquets — zero external image assets, fully self-contained
- Mock data (10 products, 4 shops) — ready to be wired to the Django API

### 🔌 REST API (backend)
- Products & categories with search / filter / sort / pagination — 28 seeded flowers with **real photos**
- Registration & JWT auth with refresh, server-synced cart, checkout, order history
- Customer↔support messaging with admin replies

### 🛠️ Admin
- **Trilingual Django admin**: `/admin/` (English), `/ru/admin/`, `/uz/admin/` + a language switcher in the header
- Product list with photo thumbnails, inline price/stock editing, image preview
- Orders with read-only item inlines, subtotals, and one-click status updates
- Category product counts, customer messages with reply workflow
- React admin dashboard at `/admin` (frontend) with revenue & order stats

### ⚙️ Infrastructure
- Celery + Celery Beat for background tasks (admin notifications, daily summaries)
- Django Channels (ASGI via Daphne) ready for real-time features
- Docker Compose for one-command startup
- 45 pytest tests covering auth, products, cart, orders, categories, contact, and admin i18n

---

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12 · Django 4.2 · DRF 3.14 · SimpleJWT · django-filter |
| Frontend | Next.js 16 (App Router) · React 19 · TypeScript · Tailwind CSS 4 |
| Database | PostgreSQL 15 |
| Queue / Realtime | Redis · Celery 5 · Celery Beat · Django Channels (Daphne) |
| i18n | react-i18next (frontend) · Django locale + gettext catalogs (admin) |
| Testing | pytest + pytest-django |
| Deployment | Docker + Docker Compose |

---

## 📁 Project Structure

```
flower-shop/
├── backend/
│   ├── config/
│   │   ├── settings/            # base / development / production (django-environ)
│   │   ├── urls.py              # API routes + i18n_patterns for the admin
│   │   ├── celery.py            # Celery app & beat schedule
│   │   └── asgi.py / wsgi.py
│   ├── apps/
│   │   ├── common/              # Shared permissions & pagination
│   │   ├── users/               # Custom User (email login), register/login/profile
│   │   ├── categories/          # Category ViewSet (slug lookup)
│   │   ├── products/            # Product ViewSet + filters + search
│   │   │   └── management/commands/
│   │   │       ├── seed_flowers.py            # 7 categories, 28 products
│   │   │       └── download_flower_images.py  # real photos, no API key needed
│   │   ├── cart/                # Cart + CartItem + service layer
│   │   ├── orders/              # Order + OrderItem + service layer
│   │   └── contact/             # Customer → admin messages + Celery notifications
│   ├── locale/                  # ru / uz translation catalogs for the admin
│   ├── scripts/
│   │   └── compile_messages.py  # pure-Python .po → .mo (no GNU gettext needed)
│   ├── templates/admin/         # base_site override: branding + language switcher
│   ├── tests/                   # cross-app tests (admin i18n)
│   └── manage.py · requirements.txt · pytest.ini · Dockerfile
│
├── frontend/                    # "Gulora" — Next.js 16 marketplace UI (mock data)
│   ├── app/                     # App Router: layout, page, global theme tokens
│   ├── components/              # TrustBar, Header, Hero, CategoryNav, Catalog,
│   │                            # ProductCard, GiftFinder, BouquetBuilder,
│   │                            # Reviews, WhyChooseUs, Footer, BouquetArt (SVG)
│   └── lib/                     # types.ts + mock data (products, reviews, palettes)
│
├── docker-compose.yml           # db + backend + frontend
└── README.md
```

---

## 🚀 Quick Start

### Option A — Docker (recommended)

```bash
git clone https://github.com/Bol-F/flower-shop.git
cd flower-shop

cp backend/.env.example backend/.env   # set SECRET_KEY and DB_PASSWORD

docker-compose up --build
```

| Service | URL |
|---|---|
| 🌸 Storefront | http://localhost:3000 |
| 🔌 API | http://localhost:8000/api/ |
| 🛠️ Django Admin | http://localhost:8000/admin/ |

### Option B — Manual setup

**Prerequisites:** Python 3.12, Node.js 18+, PostgreSQL 15+. Redis 7 is optional — only needed for Celery tasks and Channels.

<details>
<summary><b>Backend</b></summary>

```bash
cd backend

py -3.12 -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Mac/Linux

pip install -r requirements.txt

cp .env.example .env            # fill in SECRET_KEY, DB_* values

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver      # http://localhost:8000
```
</details>

<details>
<summary><b>Frontend (Gulora marketplace UI)</b></summary>

```bash
cd frontend

npm install
npm run dev                     # http://localhost:3000
```

Runs standalone on mock data — no backend or env vars required.

> The previous Bloom & Petal storefront (React 18 + i18n + support chat,
> wired to the Django API) was replaced by this design and lives in git
> history up to commit `834f639`.
</details>

### 🌷 Seed demo data

```bash
cd backend

# 7 categories + 28 products
python manage.py seed_flowers

# Download a real photo for every product (Wikimedia Commons, no API key).
# Resumable — if some downloads hit a rate limit, wait a minute and re-run.
python manage.py download_flower_images
```

---

## 🌍 Languages

English is the default. The Django admin is fully trilingual:

| Where | How to switch |
|---|---|
| Django admin | URL prefix — `/admin/` (EN), `/ru/admin/`, `/uz/admin/` — or the **EN / RU / UZ** switcher next to the logout link |
| Gulora frontend | English UI (EN / RU / UZ pills in the footer are visual placeholders for now) |

**Editing admin translations:** edit `backend/locale/{ru,uz}/LC_MESSAGES/django.po`, then compile and restart:

```bash
cd backend
python scripts/compile_messages.py   # pure Python, GNU gettext not required
```

---

## 🚀 Deployment

The backend runs on any PaaS (Render, Railway, Fly) with a managed PostgreSQL (e.g. Supabase). Static files are served by WhiteNoise — no nginx needed.

> 🐍 The repo pins **Python 3.12** via `.python-version` (Render reads it automatically; or set `PYTHON_VERSION=3.12.10` in the dashboard). The pinned dependencies are not compatible with Python 3.13/3.14.

**Environment variables to set on the platform:**

```
DJANGO_SETTINGS_MODULE=config.settings.production
SECRET_KEY=<a long random string>
DEBUG=False
ALLOWED_HOSTS=your-backend.example.com
DATABASE_URL=postgres://USER:PASSWORD@HOST:5432/DBNAME
CORS_ALLOWED_ORIGINS=https://your-frontend.example.com
CSRF_TRUSTED_ORIGINS=https://your-backend.example.com
REDIS_URL=<only if you run Celery / Channels>
```

> ⚠️ `DJANGO_SETTINGS_MODULE` must be a real environment variable on the platform — putting it in `.env` has no effect, because Django chooses the settings module before `.env` is read.

**Build command:**

```bash
pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
```

**Start command** (Daphne serves both HTTP and WebSockets):

```bash
daphne -b 0.0.0.0 -p $PORT config.asgi:application
```

**First deploy:** seed the production database once —

```bash
python manage.py createsuperuser
python manage.py seed_flowers
python manage.py download_flower_images
```

> ⚠️ On most PaaS free tiers the filesystem is ephemeral — uploaded media (product photos) disappears on redeploy. Re-run `download_flower_images` after deploys, or move media to S3/Cloudinary for permanence.

For the Gulora frontend (Vercel / Netlify): it's a standard Next.js app on mock data — no env vars needed; Vercel auto-detects the framework from `frontend/package.json`.

---

## 🧪 Tests

45 tests across users, products, categories, cart, orders, contact, and admin i18n.

```bash
cd backend

pytest                               # whole suite
pytest -v                            # verbose
pytest apps/orders                   # one app
pytest tests/test_admin_i18n.py      # admin language tests
pytest -k "permission"               # by keyword
pytest -x                            # stop at first failure

# coverage report
pip install pytest-cov
pytest --cov=apps --cov-report=term-missing
```

> PostgreSQL must be running — pytest creates and destroys its own test database.

---

## 📡 API Reference

All responses are paginated (`count` / `next` / `previous` / `results`, 12 per page) unless noted.

### Auth
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/api/auth/register/` | Create account | — |
| POST | `/api/auth/login/` | Get JWT access + refresh | — |
| POST | `/api/auth/token/refresh/` | Refresh access token | — |
| GET / PATCH | `/api/auth/profile/` | Get / update current user | ✅ |

### Categories
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/api/categories/` | List | — |
| GET | `/api/categories/{slug}/` | Detail | — |
| POST / PATCH / DELETE | `/api/categories/…` | Manage | 👑 Admin |

### Products
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/api/products/` | List with search & filters | — |
| GET | `/api/products/{slug}/` | Detail | — |
| POST / PATCH / DELETE | `/api/products/…` | Manage | 👑 Admin |

**Query params:** `search` · `category` · `min_price` · `max_price` · `is_available` · `ordering` · `page` · `page_size`

### Cart
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/api/cart/` | Cart with items & totals | ✅ |
| DELETE | `/api/cart/` | Clear cart | ✅ |
| POST | `/api/cart/items/` | Add `{product_id, quantity}` | ✅ |
| PATCH | `/api/cart/items/{productId}/` | Update `{quantity}` | ✅ |
| DELETE | `/api/cart/items/{productId}/` | Remove item | ✅ |

### Orders
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/api/orders/` | Own orders (admin sees all) | ✅ |
| POST | `/api/orders/create/` | Place order from cart | ✅ |
| GET | `/api/orders/{id}/` | Detail | ✅ owner |
| PATCH | `/api/orders/{id}/status/` | Update status | 👑 Admin |

### Contact
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/api/contact/send/` | Send a message to the shop | ✅ |
| GET | `/api/contact/admin/messages/` | List incoming messages | 👑 Admin |
| GET / PATCH | `/api/contact/admin/messages/{id}/` | Read (auto-marks read) / reply | 👑 Admin |

---

## 🏗️ Architecture Notes

**Backend**
- Business logic lives in `services.py` (cart, orders) — views validate input and delegate
- `IsAdminOrReadOnly` / `IsOwnerOrAdmin` permissions shared via `apps/common`
- Slug-based URLs for products and categories
- Orders snapshot `product_name` / `product_price` at purchase time — later price changes never rewrite history
- `@transaction.atomic` order creation: the cart is cleared only if the order commits
- Contact notifications go through Celery, wrapped so a down Redis never breaks the request

**Frontend**
- Axios interceptor attaches the JWT and transparently retries once on 401 with the refresh token
- `AuthContext` and `CartContext` are independent — the cart re-syncs from the server on every auth change
- `ProtectedRoute` guards both authenticated-only and admin-only pages
- All UI strings flow through i18next — adding a 4th language is one JSON file + one entry in `LANGUAGES`

**Admin i18n**
- `i18n_patterns(prefix_default_language=False)` keeps `/admin/` English while `/ru/` and `/uz/` prefixes switch language
- Django supplies its own admin chrome translations; project strings (models, fields, statuses) are marked with `gettext_lazy` and translated in `backend/locale/`
- `scripts/compile_messages.py` is a minimal pure-Python msgfmt, so Windows machines without GNU gettext can still compile catalogs

---

## 👑 Creating an Admin User

```bash
# during setup
python manage.py createsuperuser

# or promote an existing account
python manage.py shell
>>> from apps.users.models import User
>>> u = User.objects.get(email='you@example.com')
>>> u.is_staff = True; u.is_superuser = True; u.save()
```

---

## 📄 License

MIT
