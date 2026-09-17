from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [('marketplace', '0001_initial')]

    operations = [
        migrations.AlterField(
            model_name='city',
            name='default_delivery_fee',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('2.37'),
                help_text='Stored in the backend base price unit.',
                max_digits=10,
                validators=[MinValueValidator(Decimal('0.00'))],
                verbose_name='default delivery fee',
            ),
        ),
        migrations.AlterField(
            model_name='city',
            name='free_delivery_threshold',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('39.53'),
                help_text='Stored in the backend base price unit.',
                max_digits=10,
                validators=[MinValueValidator(Decimal('0.00'))],
                verbose_name='free delivery threshold',
            ),
        ),
        migrations.AlterField(
            model_name='promocode',
            name='discount_value',
            field=models.DecimalField(
                decimal_places=2,
                max_digits=10,
                validators=[MinValueValidator(Decimal('0.01'))],
                verbose_name='discount value',
            ),
        ),
        migrations.AlterField(
            model_name='promocode',
            name='max_discount_amount',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=10,
                null=True,
                validators=[MinValueValidator(Decimal('0.00'))],
                verbose_name='maximum discount amount',
            ),
        ),
        migrations.AlterField(
            model_name='promocode',
            name='min_order_amount',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('0.00'),
                max_digits=10,
                validators=[MinValueValidator(Decimal('0.00'))],
                verbose_name='minimum order amount',
            ),
        ),
        migrations.AlterField(
            model_name='vendor',
            name='commission_percent',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('10.00'),
                max_digits=5,
                validators=[
                    MinValueValidator(Decimal('0.00')),
                    MaxValueValidator(Decimal('100.00')),
                ],
                verbose_name='commission percent',
            ),
        ),
        migrations.AddConstraint(
            model_name='city',
            constraint=models.CheckConstraint(
                check=Q(default_delivery_fee__gte=0) & Q(free_delivery_threshold__gte=0),
                name='city_delivery_values_nonnegative',
            ),
        ),
        migrations.AddConstraint(
            model_name='promocode',
            constraint=models.CheckConstraint(
                check=Q(discount_value__gt=0)
                & (Q(discount_type='fixed_amount') | Q(discount_value__lte=100)),
                name='promo_discount_valid',
            ),
        ),
        migrations.AddConstraint(
            model_name='promocode',
            constraint=models.CheckConstraint(
                check=Q(min_order_amount__gte=0)
                & (Q(max_discount_amount__isnull=True) | Q(max_discount_amount__gte=0)),
                name='promo_amounts_nonnegative',
            ),
        ),
    ]
