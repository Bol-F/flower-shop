import pytest

from apps.cart.models import Cart, CartItem
from apps.marketplace.services import repeat_order_to_cart
from apps.orders.models import Order, OrderItem
from apps.products.models import Product
from apps.users.models import User


@pytest.mark.django_db
@pytest.mark.parametrize('existing_quantity,expected_added', [(3, 2), (5, 0)])
def test_repeat_order_adds_only_remaining_stock(existing_quantity, expected_added):
    user = User.objects.create_user(username='repeat-user', email='repeat@example.test')
    product = Product.objects.create(name='Repeat roses', description='Flowers', price=25, stock=5)
    order = Order.objects.create(
        user=user, total_price=100, shipping_address='Tashkent', phone='+998901234567'
    )
    OrderItem.objects.create(
        order=order, product=product, product_name=product.name, quantity=4, product_price=25
    )
    cart = Cart.objects.create(user=user)
    item = CartItem.objects.create(cart=cart, product=product, quantity=existing_quantity)

    result = repeat_order_to_cart(order, user)

    item.refresh_from_db()
    assert item.quantity == 5
    assert result['added'] == (
        [{'product': product.name, 'quantity': expected_added}] if expected_added else []
    )
    assert result['skipped'] == ([] if expected_added else [product.name])
