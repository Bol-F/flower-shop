from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [('products', '0004_product_city_product_vendor')]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='price',
            field=models.DecimalField(
                decimal_places=2,
                max_digits=10,
                validators=[MinValueValidator(Decimal('0.01'))],
                verbose_name='price',
            ),
        ),
        migrations.AddConstraint(
            model_name='product',
            constraint=models.CheckConstraint(check=Q(price__gt=0), name='product_price_positive'),
        ),
    ]
