from django.db import migrations, models


def backfill_payment_metadata_and_zone_city(apps, schema_editor):
    Order = apps.get_model('orders', 'Order')
    DeliveryZone = apps.get_model('orders', 'DeliveryZone')

    for order in Order.objects.all().only('id', 'payment_method', 'payment_provider'):
        if order.payment_provider:
            continue
        order.payment_provider = 'cash' if order.payment_method == 'cash' else 'manual'
        order.save(update_fields=['payment_provider'])

    DeliveryZone.objects.filter(name__in=['Tashkent Center', 'Outer Tashkent']).update(
        city='Tashkent'
    )
    DeliveryZone.objects.filter(name='Outside City').update(city='Outside city')


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0006_deliveryzone_order_delivery_requires_confirmation_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='deliveryzone',
            name='city',
            field=models.CharField(
                default='Tashkent',
                max_length=80,
                verbose_name='city',
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='paid_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='paid at'),
        ),
        migrations.AddField(
            model_name='order',
            name='payment_provider',
            field=models.CharField(
                blank=True,
                default='',
                max_length=60,
                verbose_name='payment provider',
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='payment_reference',
            field=models.CharField(
                blank=True,
                default='',
                max_length=120,
                verbose_name='payment reference',
            ),
        ),
        migrations.RunPython(
            backfill_payment_metadata_and_zone_city,
            migrations.RunPython.noop,
        ),
    ]
