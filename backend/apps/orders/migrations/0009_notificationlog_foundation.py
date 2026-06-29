from django.db import migrations, models
import django.db.models.deletion


def normalize_notification_statuses(apps, schema_editor):
    NotificationLog = apps.get_model('orders', 'NotificationLog')
    NotificationLog.objects.filter(status='success').update(status='sent')


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0008_deliveryzone_city_order_assigned_courier_order_city_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='notificationlog',
            old_name='order',
            new_name='related_order',
        ),
        migrations.RenameField(
            model_name='notificationlog',
            old_name='event',
            new_name='event_type',
        ),
        migrations.RenameField(
            model_name='notificationlog',
            old_name='error',
            new_name='error_message',
        ),
        migrations.AddField(
            model_name='notificationlog',
            name='recipient',
            field=models.CharField(blank=True, default='', max_length=255, verbose_name='recipient'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='notificationlog',
            name='sent_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='sent at'),
        ),
        migrations.AddField(
            model_name='notificationlog',
            name='subject',
            field=models.CharField(blank=True, default='', max_length=255, verbose_name='subject'),
            preserve_default=False,
        ),
        migrations.RunPython(
            normalize_notification_statuses,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name='notificationlog',
            name='channel',
            field=models.CharField(
                choices=[
                    ('console', 'Console'),
                    ('email', 'Email'),
                    ('telegram', 'Telegram'),
                ],
                max_length=20,
                verbose_name='channel',
            ),
        ),
        migrations.AlterField(
            model_name='notificationlog',
            name='error_message',
            field=models.TextField(blank=True, verbose_name='error message'),
        ),
        migrations.AlterField(
            model_name='notificationlog',
            name='event_type',
            field=models.CharField(
                choices=[
                    ('order_created', 'Order created'),
                    ('order_confirmed', 'Order confirmed'),
                    ('order_preparing', 'Order preparing'),
                    ('courier_picked_up', 'Courier picked up'),
                    ('order_delivered', 'Order delivered'),
                    ('payment_paid', 'Payment paid'),
                    ('payment_failed', 'Payment failed'),
                    ('payment_status_changed', 'Payment status changed'),
                    ('support_message_created', 'Support message created'),
                ],
                max_length=40,
                verbose_name='event type',
            ),
        ),
        migrations.AlterField(
            model_name='notificationlog',
            name='related_order',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='notification_logs',
                to='orders.order',
                verbose_name='related order',
            ),
        ),
        migrations.AlterField(
            model_name='notificationlog',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending'),
                    ('sent', 'Sent'),
                    ('failed', 'Failed'),
                    ('skipped', 'Skipped'),
                ],
                max_length=20,
                verbose_name='status',
            ),
        ),
    ]
