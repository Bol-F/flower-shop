import pytest
from apps.products.admin import ProductAdmin, StockLevelFilter
from apps.products.models import Product
from django.contrib.admin.sites import AdminSite


@pytest.mark.django_db
@pytest.mark.parametrize(
    'stock_level, expected_names',
    [
        ('low', {'Sold out roses', 'Last tulips', 'Threshold lilies', 'Large threshold'}),
        ('in_stock', {'Plentiful peonies'}),
        ('out_of_stock', {'Sold out roses', 'Hidden sold out'}),
    ],
)
def test_stock_filter_uses_each_products_threshold(rf, stock_level, expected_names):
    for name, stock, threshold, available in (
        ('Sold out roses', 0, 3, True),
        ('Last tulips', 2, 3, True),
        ('Threshold lilies', 8, 8, True),
        ('Large threshold', 10, 15, True),
        ('Plentiful peonies', 4, 3, True),
        ('Hidden sold out', 0, 3, False),
        ('Hidden low stock', 1, 3, False),
        ('Hidden plentiful', 20, 3, False),
    ):
        Product.objects.create(
            name=name,
            price='100.00',
            stock=stock,
            low_stock_threshold=threshold,
            is_available=available,
        )

    request = rf.get('/admin/products/product/', {'stock_level': stock_level})
    product_admin = ProductAdmin(Product, AdminSite())
    stock_filter = StockLevelFilter(request, {'stock_level': stock_level}, Product, product_admin)
    filtered = stock_filter.queryset(request, Product.objects.all())

    assert set(filtered.values_list('name', flat=True)) == expected_names
