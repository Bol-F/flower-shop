from uuid import uuid4

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.cart.models import Cart, CartItem, GuestSelectionMerge
from apps.marketplace.models import WishlistItem
from apps.products.models import Product
from apps.users.models import User


pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    return User.objects.create_user('guest-merge', 'merge@example.test', 'pw')


@pytest.fixture
def client(user):
    result = APIClient()
    result.force_authenticate(user)
    return result


@pytest.fixture
def rose():
    return Product.objects.create(name='Rose', slug='rose', stock=5, price='10')


def payload(**changes):
    return {
        'merge_id': str(uuid4()),
        'items': [{'product_slug': 'rose', 'quantity': 2}],
        'wishlist': ['rose'],
        **changes,
    }


def test_merge_authentication_required():
    assert APIClient().post(reverse('cart-merge'), payload(), format='json').status_code == 401


def test_merge_combines_account_and_guest_selections_once(client, user, rose):
    cart = Cart.objects.create(user=user)
    CartItem.objects.create(cart=cart, product=rose, quantity=1)
    body = payload()
    first = client.post(reverse('cart-merge'), body, format='json')
    second = client.post(reverse('cart-merge'), body, format='json')
    assert first.status_code == second.status_code == 200
    assert first.data['cart']['total_items'] == second.data['cart']['total_items'] == 3
    assert len(second.data['wishlist']) == 1
    assert WishlistItem.objects.filter(user=user).count() == 1
    assert GuestSelectionMerge.objects.filter(user=user).count() == 1
    assert second['Cache-Control'] == 'no-store'


def test_same_receipt_does_not_restore_removed_or_checked_out_items(client, user, rose):
    body = payload()
    assert client.post(reverse('cart-merge'), body, format='json').status_code == 200
    CartItem.objects.filter(cart__user=user).delete()
    WishlistItem.objects.filter(user=user).delete()
    response = client.post(reverse('cart-merge'), body, format='json')
    assert response.status_code == 200
    assert response.data['cart']['total_items'] == 0
    assert response.data['wishlist'] == []


def test_merge_clamps_stock_and_reports_unavailable_products(client, user, rose):
    sold_out = Product.objects.create(name='Sold out', slug='sold-out', stock=0, price='12')
    Product.objects.create(name='Hidden', slug='hidden', stock=4, price='9', is_available=False)
    response = client.post(
        reverse('cart-merge'),
        payload(
            items=[
                {'product_slug': 'rose', 'quantity': 4},
                {'product_slug': 'rose', 'quantity': 4},
                {'product_slug': 'sold-out', 'quantity': 1},
                {'product_slug': 'missing', 'quantity': 1},
            ],
            wishlist=['sold-out', 'hidden'],
        ),
        format='json',
    )
    assert response.status_code == 200
    assert response.data['cart']['total_items'] == 5
    assert response.data['adjusted_products'] == ['rose']
    assert response.data['unavailable_products'] == ['hidden', 'missing', 'sold-out']
    assert WishlistItem.objects.filter(user=user, product=sold_out).exists()
    rose.refresh_from_db()
    assert rose.stock == 5  # Carts do not reserve inventory.


def test_receipt_cannot_be_reused_with_other_content(client, user, rose):
    body = payload()
    client.post(reverse('cart-merge'), body, format='json')
    body['items'][0]['quantity'] = 4
    response = client.post(reverse('cart-merge'), body, format='json')
    assert response.status_code == 400
    assert CartItem.objects.get(cart__user=user).quantity == 2


def test_merge_ids_are_scoped_to_the_authenticated_account(client, user, rose):
    body = payload()
    client.post(reverse('cart-merge'), body, format='json')
    other = User.objects.create_user('other-merge', password='pw')
    client.force_authenticate(other)
    response = client.post(reverse('cart-merge'), body, format='json')
    assert response.status_code == 200
    assert Cart.objects.get(pk=response.data['cart']['id']).user == other
    assert GuestSelectionMerge.objects.count() == 2
    assert CartItem.objects.get(cart__user=user).quantity == 2


@pytest.mark.parametrize(
    'changes',
    [
        {'merge_id': 'bad'},
        {'items': [{'product_slug': 'rose', 'quantity': 0}]},
        {'items': [{'product_slug': 'rose', 'quantity': 1000}]},
        {'items': [{'product_slug': 'rose', 'quantity': 1}] * 101},
        {'wishlist': ['rose'] * 101},
    ],
)
def test_bad_merge_payloads_do_not_write(client, changes):
    response = client.post(reverse('cart-merge'), payload(**changes), format='json')
    assert response.status_code == 400
    assert not GuestSelectionMerge.objects.exists()
    assert not Cart.objects.exists()
