<div align="center">

# 🌸 Bloom & Petal

**Full-stack flower shop e-commerce — Django REST Framework + React**

Fresh flowers, real product photos, JWT auth, server-synced cart, and a trilingual UI & admin (EN / RU / UZ).

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

### 🛍️ Customer
- Browse 28 flower products across 7 categories — **real photos** from Wikimedia Commons
- Search, filter by category / price / availability, sort, pagination
- **Three languages — English (default), Русский, Oʻzbekcha** — switchable from the navbar, remembered in localStorage
- Registration & JWT login with automatic token refresh
- Server-synced shopping cart: add, update quantity, remove, clear
- Checkout with delivery details, free shipping over $50
- Order history with live status badges
- Profile editing, contact-the-shop messaging

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
| Frontend | React 18 · React Router v6 · Axios · react-i18next |
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
├── frontend/
│   └── src/
│       ├── api/                 # Axios instance + JWT refresh interceptor
│       ├── components/          # common / products / cart
│       ├── context/             # AuthContext, CartContext
│       ├── hooks/               # useAuth, useCart, useProducts
│       ├── i18n/                # en.json · ru.json · uz.json + i18next setup
│       ├── pages/               # Home, Products, Detail, Cart, Checkout, Auth,
│       │                        # Profile, Orders, AdminDashboard
│       ├── routes/              # AppRoutes + ProtectedRoute (auth/admin guards)
│       └── utils/               # JWT storage, formatting helpers
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
<summary><b>Frontend</b></summary>

```bash
cd frontend

cp .env.example .env            # REACT_APP_API_URL=http://localhost:8000/api

npm install
npm start                       # http://localhost:3000
```
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

English is the default everywhere. Russian and Uzbek are fully supported:

| Where | How to switch |
|---|---|
| Storefront | **EN / РУ / OʻZ** buttons in the navbar — persisted in localStorage, auto-detected from the browser on first visit |
| Django admin | URL prefix — `/admin/` (EN), `/ru/admin/`, `/uz/admin/` — or the **EN / RU / UZ** switcher next to the logout link |

**Editing translations:**

- *Frontend:* edit `frontend/src/i18n/locales/{en,ru,uz}.json` — hot-reloads in dev.
- *Admin:* edit `backend/locale/{ru,uz}/LC_MESSAGES/django.po`, then compile and restart:

  ```bash
  cd backend
  python scripts/compile_messages.py   # pure Python, GNU gettext not required
  ```

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
