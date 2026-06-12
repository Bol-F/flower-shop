"""The admin must be served in English (default), Russian, and Uzbek."""
import pytest
from django.utils import translation

from apps.orders.models import Order
from apps.products.models import Product


@pytest.mark.django_db
class TestAdminLanguages:
    def test_default_admin_is_english(self, client):
        response = client.get('/admin/login/')
        assert response.status_code == 200
        body = response.content.decode('utf-8')
        assert 'Bloom &amp; Petal administration' in body
        assert 'Password' in body

    def test_russian_admin(self, client):
        response = client.get('/ru/admin/login/')
        assert response.status_code == 200
        body = response.content.decode('utf-8')
        assert 'Администрирование Bloom &amp; Petal' in body
        assert 'Пароль' in body

    def test_uzbek_admin(self, client):
        response = client.get('/uz/admin/login/')
        assert response.status_code == 200
        body = response.content.decode('utf-8')
        assert 'Bloom &amp; Petal boshqaruvi' in body
        assert 'Parol' in body

    def test_set_language_redirects_to_prefixed_admin(self, client):
        response = client.post('/i18n/setlang/', {'language': 'ru', 'next': '/admin/'})
        assert response.status_code == 302
        assert response.url == '/ru/admin/'


class TestModelLabelTranslations:
    @pytest.mark.parametrize('lang, products, price, pending', [
        ('en', 'Products', 'price', 'Pending'),
        ('ru', 'Товары', 'цена', 'В ожидании'),
        ('uz', 'Mahsulotlar', 'narx', 'Kutilmoqda'),
    ])
    def test_labels_translate(self, lang, products, price, pending):
        with translation.override(lang):
            assert str(Product._meta.verbose_name_plural) == products
            assert str(Product._meta.get_field('price').verbose_name) == price
            assert str(Order.Status.PENDING.label) == pending
