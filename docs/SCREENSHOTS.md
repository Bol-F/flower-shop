# Screenshot Checklist

Use this checklist when preparing portfolio screenshots for Bloom & Petal.

Recommended setup:

1. Run the backend and frontend locally.
2. Run `python manage.py seed_demo`.
3. Log in as `customer@example.com` / `demo12345` for customer screens.
4. Log in as `staff@example.com` / `demo12345` for staff screens.
5. Capture desktop at 1440px wide and mobile at 390px wide.

Save final screenshots in:

```text
docs/screenshots/
```

## Customer Screens

- [ ] Homepage hero: `docs/screenshots/homepage.png`
- [ ] Product catalog with filters: `docs/screenshots/catalog.png`
- [ ] Empty product search state: `docs/screenshots/empty-search.png`
- [ ] Product detail page: `docs/screenshots/product-detail.png`
- [ ] Product reviews section: `docs/screenshots/reviews.png`
- [ ] Cart with items: `docs/screenshots/cart.png`
- [ ] Checkout form: `docs/screenshots/checkout.png`
- [ ] Order success with test payment: `docs/screenshots/order-success.png`
- [ ] Order history: `docs/screenshots/order-history.png`
- [ ] Order status timeline: `docs/screenshots/order-timeline.png`
- [ ] Customer support chat: `docs/screenshots/support-chat.png`
- [ ] Login/register screen: `docs/screenshots/auth.png`

## Staff Screens

- [ ] Staff dashboard: `docs/screenshots/staff-dashboard.png`
- [ ] Delivery queue: `docs/screenshots/delivery-queue.png`
- [ ] Staff order management: `docs/screenshots/staff-orders.png`
- [ ] Low-stock warnings: `docs/screenshots/stock-alerts.png`
- [ ] Support inbox: `docs/screenshots/support-inbox.png`
- [ ] Django admin order view: `docs/screenshots/django-admin-orders.png`

## Mobile Screens

- [ ] Mobile homepage: `docs/screenshots/mobile-homepage.png`
- [ ] Mobile product card grid: `docs/screenshots/mobile-catalog.png`
- [ ] Mobile cart and checkout: `docs/screenshots/mobile-checkout.png`
- [ ] Mobile profile/order history: `docs/screenshots/mobile-profile.png`

## Notes

- Do not commit screenshots with real customer data.
- Keep demo credentials out of screenshots unless the screenshot is specifically
  documenting local setup.
- Prefer seeded demo orders and products so screenshots are repeatable.
- If the backend is intentionally offline, capture the catalog fallback warning.
