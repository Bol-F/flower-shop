from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('cart', '0003_alter_cart_options_alter_cartitem_options_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='GuestSelectionMerge',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('merge_id', models.UUIDField()),
                ('payload_hash', models.CharField(max_length=64)),
                ('adjustments', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'constraints': [models.UniqueConstraint(fields=('user', 'merge_id'), name='guest_merge_user_id_unique')],
            },
        ),
    ]
