"""Keep Django data private when Postgres is hosted by Supabase.

Django owns authentication and authorization. Supabase's browser API roles must
not bypass those checks by querying its application tables directly.
"""

from django.db import migrations


APPLICATION_TABLE_PATTERN = (
    r'^(users_|orders_|contact_|products_|reviews_|cart_|marketplace_|'
    r'categories_|auth_|django_|token_blacklist_)'
)


def protect_django_tables(apps, schema_editor):
    connection = schema_editor.connection
    if connection.vendor != 'postgresql':
        return

    quote = connection.ops.quote_name
    with connection.cursor() as cursor:
        cursor.execute(
            'SELECT rolname FROM pg_roles WHERE rolname IN (%s, %s, %s) ORDER BY rolname',
            ['anon', 'authenticated', 'service_role'],
        )
        api_roles = [row[0] for row in cursor.fetchall()]
        if not api_roles:
            # Plain PostgreSQL installations have no Supabase browser API roles.
            return

        grantees = ', '.join(['PUBLIC', *(quote(role) for role in api_roles)])
        cursor.execute(
            "SELECT c.oid, c.relname FROM pg_class c "
            'JOIN pg_namespace n ON n.oid = c.relnamespace '
            "WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p') "
            'AND c.relname ~ %s ORDER BY c.relname',
            [APPLICATION_TABLE_PATTERN],
        )
        tables = cursor.fetchall()
        for _, name in tables:
            relation = f'{quote("public")}.{quote(name)}'
            cursor.execute(f'REVOKE ALL PRIVILEGES ON TABLE {relation} FROM {grantees}')
            # The backend table owner retains access. FORCE RLS would require
            # per-request DB policies, which this Django architecture does not use.
            cursor.execute(f'ALTER TABLE {relation} ENABLE ROW LEVEL SECURITY')

        if tables:
            cursor.execute(
                'SELECT DISTINCT s.relname FROM pg_class s '
                'JOIN pg_namespace n ON n.oid = s.relnamespace '
                'JOIN pg_depend d ON d.objid = s.oid '
                "WHERE n.nspname = 'public' AND s.relkind = 'S' "
                "AND d.deptype IN ('a', 'i') AND d.refobjid = ANY(%s) ORDER BY s.relname",
                [[oid for oid, _ in tables]],
            )
            for (name,) in cursor.fetchall():
                relation = f'{quote("public")}.{quote(name)}'
                cursor.execute(f'REVOKE ALL PRIVILEGES ON SEQUENCE {relation} FROM {grantees}')

        # This database is a private Django store. Future tables/sequences made
        # by the migration role must require explicit grants to become public.
        for kind in ('TABLES', 'SEQUENCES'):
            # Schema-scoped REVOKE cannot undo a global default GRANT. Remove
            # both scopes for this private database's migration role.
            for scope in ('', f'IN SCHEMA {quote("public")} '):
                cursor.execute(
                    f'ALTER DEFAULT PRIVILEGES {scope}'
                    f'REVOKE ALL PRIVILEGES ON {kind} FROM {grantees}'
                )


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0011_case_insensitive_email'),
        ('cart', '0004_guest_selection_merge'),
        ('orders', '0011_validate_delivery_zone_fee'),
        ('marketplace', '0002_validate_pricing_and_promos'),
        ('products', '0005_validate_positive_price'),
        ('categories', '0002_alter_category_created_at_alter_category_description_and_more'),
        ('contact', '0003_usermessage_is_from_admin'),
        ('reviews', '0002_delete_productlike'),
    ]

    operations = [
        # Rolling back application code must never reopen private data access.
        migrations.RunPython(protect_django_tables, migrations.RunPython.noop),
    ]
