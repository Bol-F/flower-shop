# Backend logic and security review

The backend hardening release preserves the storefront design and keeps real
payment collection disabled in the public demo.

## Confirmed defects addressed

| Area | Result |
| --- | --- |
| Account security | Password changes invalidate access/refresh tokens and pending OAuth credentials; concurrent refresh rotation is single-use. |
| Stale edits | Profile and Django admin edits preserve newer password, permissions, payment and fulfillment changes. |
| Account identity | Case-insensitive email uniqueness is enforced by the database; concurrent duplicate registrations return validation errors. |
| Payment state | Payment transitions reload locked records; obsolete attempts cannot overwrite a newer payment outcome. |
| Concurrency | Checkout, callbacks and cancellation use consistent locks; last-unit stock contention and expiry refreshes are checked on PostgreSQL. |
| Delivery | Checkout uses current delivery-zone settings and rejects unavailable products, vendors, cities and mismatched delivery cities. |
| Catalog/admin | Generated slugs and promo codes are validated before persistence; review admin listing/search works. |
| Support | Staff queue filters work, cleared replies clear their timestamp, and outgoing messages cannot acquire nested replies. |
| Loyalty | Persisted order eligibility and atomic increments prevent duplicate awards and lost balances. |
| Queries | Four-product wishlist queries fell from ten to three; four-category listing queries fell from six to two, with stable ordering. |
| Public data | Hidden catalog entries stay out of reviews, wishlists and AI recommendations; internal vendor commission rates are excluded. |

## Database boundary

Supabase is used as private PostgreSQL storage. Metadata inspection found 43
Django tables with API-role grants and no RLS. A zero-row REST probe returned
a schema-cache error, so this review does not establish a successful public
read or a past data breach.

The matching permission mitigation was applied to the existing database and
verified: all 43 tables have RLS enabled; `anon`, `authenticated` and
`service_role` have no CRUD grants. The backend owner retains access.
Migration `users.0012_private_database_tables` makes the same protection
repeatable on deployments. It also removes table/sequence default API grants
for the migration role. Supabase-managed objects remain unchanged.

## Dependencies and verification

Security updates cover DRF, joserfc, Pillow, certifi, setuptools, Twisted and
Autobahn. Build instructions upgrade pip. Release notes were checked against
the maintainers' documentation before selecting versions.

The logic patch passed 577 PostgreSQL tests, 572 SQLite tests and 125 frontend
tests. PostgreSQL includes real concurrent checkout, token rotation,
payment/cancellation and loyalty tests. CI now runs the entire backend suite
on both database engines. The upgraded isolated environment passes `pip check`
and pip-audit reports no known vulnerabilities in its installed dependencies.

## Deployment and remaining limits

Existing JWTs require a fresh sign-in after password binding is deployed.
Migration 0011 stops on ambiguous email identities without changing accounts.
Migration 0012 intentionally does not reopen API access on rollback.

Real payment providers still require merchant sandbox acceptance, settlement
reconciliation and refund procedures before live collection. The demo remains
test-only. Zero-total promotional checkout needs an explicit free-order
completion policy; refunded deliveries currently retain earned loyalty points.
Reviews remain open to signed-in users, matching the existing product behavior.

## Primary references

- [Supabase API security](https://supabase.com/docs/guides/api/securing-your-api)
- [PostgreSQL default privileges](https://www.postgresql.org/docs/17/sql-alterdefaultprivileges.html)
- [DRF release notes](https://www.django-rest-framework.org/community/release-notes/)
- [Pillow 13 release notes](https://pillow.readthedocs.io/en/stable/releasenotes/13.0.0.html)
- [Twisted 26.10 security fixes](https://github.com/twisted/twisted/releases/tag/twisted-26.10.0)
- [Twisted IMAP advisory](https://github.com/twisted/twisted/security/advisories/GHSA-8pqf-f4m5-798g)
