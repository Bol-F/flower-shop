"""Check the actual PostgreSQL role boundary, without accessing a hosted DB."""

from importlib import import_module

from django.apps import apps
from django.db import ProgrammingError, connection, transaction
import pytest


protect = import_module('apps.users.migrations.0012_private_database_tables').protect_django_tables


@pytest.mark.django_db(transaction=True)
def test_private_database_migration_is_harmless_on_sqlite():
    if connection.vendor != 'sqlite':
        pytest.skip('SQLite compatibility check')
    with connection.schema_editor() as editor:
        protect(apps, editor)
    with connection.cursor() as cursor:
        cursor.execute('SELECT COUNT(*) FROM users_user')
        assert cursor.fetchone()[0] == 0


@pytest.mark.django_db(transaction=True)
def test_supabase_roles_cannot_access_django_tables_but_backend_owner_can():
    if connection.vendor != 'postgresql':
        pytest.skip('Requires PostgreSQL roles and RLS')
    with connection.cursor() as cursor:
        for role in ('anon', 'authenticated', 'service_role', 'flower_qa_table_owner'):
            cursor.execute('SELECT 1 FROM pg_roles WHERE rolname = %s', [role])
            if cursor.fetchone() is None:
                cursor.execute(f'CREATE ROLE "{role}" NOLOGIN')
        cursor.execute('GRANT USAGE ON SCHEMA public TO flower_qa_table_owner')
        cursor.execute('CREATE TABLE users_qa_private (id bigserial PRIMARY KEY, payload text)')
        cursor.execute('CREATE TABLE unrelated_qa_public (id integer)')
        cursor.execute('INSERT INTO users_qa_private (payload) VALUES (%s)', ['synthetic'])
        cursor.execute(
            'GRANT ALL ON users_qa_private, unrelated_qa_public TO anon, authenticated, service_role'
        )
        cursor.execute(
            'GRANT ALL ON SEQUENCE users_qa_private_id_seq TO anon, authenticated, service_role'
        )
        cursor.execute(
            'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES '
            'TO anon, authenticated, service_role'
        )
        cursor.execute(
            'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES '
            'TO anon, authenticated, service_role'
        )
        cursor.execute(
            'ALTER DEFAULT PRIVILEGES GRANT ALL ON TABLES '
            'TO PUBLIC, anon, authenticated, service_role'
        )
        cursor.execute(
            'ALTER DEFAULT PRIVILEGES GRANT ALL ON SEQUENCES '
            'TO PUBLIC, anon, authenticated, service_role'
        )
    try:
        with connection.schema_editor() as editor:
            protect(apps, editor)
            protect(apps, editor)  # Safe if retried after an interrupted release.
        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT relrowsecurity, relforcerowsecurity FROM pg_class '
                "WHERE oid = 'users_qa_private'::regclass"
            )
            assert cursor.fetchone() == (True, False)
            for role in ('anon', 'authenticated', 'service_role'):
                cursor.execute(
                    "SELECT has_table_privilege(%s, 'users_qa_private', 'SELECT'), "
                    "has_table_privilege(%s, 'users_qa_private', 'INSERT'), "
                    "has_table_privilege(%s, 'users_qa_private', 'UPDATE'), "
                    "has_table_privilege(%s, 'users_qa_private', 'DELETE'), "
                    "has_sequence_privilege(%s, 'users_qa_private_id_seq', 'USAGE'), "
                    "has_table_privilege(%s, 'unrelated_qa_public', 'SELECT')",
                    [role] * 6,
                )
                assert cursor.fetchone() == (False, False, False, False, False, True)

        for role in ('anon', 'authenticated', 'service_role'):
            with pytest.raises(ProgrammingError, match='permission denied'):
                with transaction.atomic(), connection.cursor() as cursor:
                    cursor.execute(f'SET LOCAL ROLE "{role}"')
                    cursor.execute('SELECT id FROM users_qa_private LIMIT 0')

        # A real non-superuser table owner still has the CRUD access Django needs.
        with connection.cursor() as cursor:
            cursor.execute('ALTER TABLE users_qa_private OWNER TO flower_qa_table_owner')
        with transaction.atomic(), connection.cursor() as cursor:
            cursor.execute('SET LOCAL ROLE flower_qa_table_owner')
            cursor.execute('SELECT payload FROM users_qa_private')
            assert cursor.fetchone()[0] == 'synthetic'
            cursor.execute('INSERT INTO users_qa_private (payload) VALUES (%s)', ['new'])
            cursor.execute('UPDATE users_qa_private SET payload = %s', ['updated'])
            cursor.execute('DELETE FROM users_qa_private')
            assert cursor.rowcount == 2

        with connection.cursor() as cursor:
            cursor.execute('CREATE TABLE users_qa_future (id bigserial PRIMARY KEY)')
            for role in ('anon', 'authenticated', 'service_role'):
                cursor.execute(
                    "SELECT has_table_privilege(%s, 'users_qa_future', 'SELECT'), "
                    "has_sequence_privilege(%s, 'users_qa_future_id_seq', 'USAGE')",
                    [role, role],
                )
                assert cursor.fetchone() == (False, False)
    finally:
        with connection.cursor() as cursor:
            cursor.execute(
                'DROP TABLE IF EXISTS users_qa_private, users_qa_future, unrelated_qa_public'
            )
