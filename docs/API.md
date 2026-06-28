# Bloom & Petal API Reference

Base URL: `https://your-backend.example.com`

Auth uses JWT bearer tokens from `/api/auth/login/`.

## Auth

| Method | Endpoint | Notes |
|---|---|---|
| `POST` | `/api/auth/register/` | Create customer account |
| `POST` | `/api/auth/login/` | Returns access, refresh, and user profile |
| `POST` | `/api/auth/token/refresh/` | Refresh access token |
| `GET/PATCH` | `/api/auth/profile/` | Profile, city, language, currency, loyalty points |

## Catalog

| Method | Endpoint | Notes |
|---|---|---|
| `GET` | `/api/categories/` | Category list |
| `GET` | `/api/products/` | Supports `search`, `category`, `city`, `vendor`, `min_price`, `max_price`, `ordering` |
| `GET` | `/api/products/{slug}/` | Product detail with stock, city, vendor metadata |

## Marketplace Foundation

| Method | Endpoint | Notes |
|---|---|---|
| `GET` | `/api/marketplace/cities/` | Active cities |
| `GET` | `/api/marketplace/vendors/` | Active vendors |
| `GET` | `/api/marketplace/couriers/` | Staff-only active couriers |
| `POST` | `/api/marketplace/promo-codes/validate/` | `{code, subtotal}` returns estimated discount |
| `GET/POST` | `/api/marketplace/wishlist/` | Logged-in wishlist list/add |
| `DELETE` | `/api/marketplace/wishlist/{product_id}/` | Remove product from wishlist |

## Cart And Checkout

| Method | Endpoint | Notes |
|---|---|---|
| `GET/DELETE` | `/api/cart/` | Read or clear cart |
| `POST` | `/api/cart/items/` | Add `{product_id, quantity}` |
| `PATCH/DELETE` | `/api/cart/items/{product_id}/` | Update or remove |
| `POST` | `/api/orders/create/` | Creates order from cart; accepts delivery fields, `city_slug`, `promo_code`, and payment method |

## Orders And Staff

| Method | Endpoint | Notes |
|---|---|---|
| `GET` | `/api/orders/` | Customer sees own orders; staff sees all |
| `GET` | `/api/orders/{id}/` | Order detail |
| `POST` | `/api/orders/{id}/repeat/` | Adds available previous order items back to cart |
| `PATCH` | `/api/orders/{id}/status/` | Staff order status update |
| `PATCH` | `/api/orders/{id}/payment-status/` | Staff payment status update with optional provider/reference |
| `PATCH` | `/api/orders/{id}/courier/` | Staff courier assignment `{courier_id}` |
| `GET` | `/api/orders/dashboard/` | Staff analytics, inventory, delivery queue |
| `GET` | `/api/orders/delivery-zones/?city=tashkent` | Active delivery zones, optionally city-filtered |

## Reviews And Support

| Method | Endpoint | Notes |
|---|---|---|
| `GET` | `/api/reviews/products/{product_id}/` | Product rating/review summary |
| `POST/DELETE` | `/api/reviews/products/{product_id}/review/` | Customer review upsert/delete |
| `POST` | `/api/contact/send/` | Customer support message |
| `GET` | `/api/contact/my-messages/` | Customer support history |
| `GET` | `/api/contact/admin/messages/` | Staff support queue |
| `POST` | `/api/contact/admin/messages/{id}/reply/` | Staff reply |

## Production Notes

Prices remain stored in the backend base price unit. Frontend currency display is converted client-side. Media storage is local by default; use Cloudinary, Supabase Storage, S3, or another external storage service before accepting production uploads.
