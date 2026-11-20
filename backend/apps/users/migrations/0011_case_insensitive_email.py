"""Enforce the same email identity rule for every account creation path."""

from django.db import migrations, models
from django.db.models.functions import Lower


def reject_ambiguous_email_identities(apps, schema_editor):
    User = apps.get_model('users', 'User')
    duplicates = (
        User.objects.using(schema_editor.connection.alias)
        .annotate(email_identity=Lower('email'))
        .values('email_identity')
        .annotate(accounts=models.Count('pk'))
        .filter(accounts__gt=1)
    )
    if duplicates.exists():
        # Choosing an owner automatically could attach order history or OAuth
        # identities to the wrong person. Preserve every account and stop.
        raise RuntimeError(
            'Case-insensitive duplicate user emails must be resolved before applying '
            'users.0011_case_insensitive_email. No accounts have been changed.'
        )


class Migration(migrations.Migration):
    dependencies = [('users', '0010_retire_public_demo_accounts')]

    operations = [
        migrations.RunPython(reject_ambiguous_email_identities, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='user',
            constraint=models.UniqueConstraint(Lower('email'), name='users_email_ci_unique'),
        ),
    ]
