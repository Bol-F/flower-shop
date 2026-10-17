import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.marketplace.models import City
from apps.orders.models import DeliveryZone


@pytest.mark.django_db
def test_delivery_zone_exposes_admin_configured_city_threshold():
    city = City.objects.create(name='Flexible City', slug='flexible', free_delivery_threshold='100')
    DeliveryZone.objects.create(name='Flexible Zone', city=city, fee='5')
    response = APIClient().get(reverse('delivery-zone-list'), {'city': city.slug})
    assert response.status_code == 200
    zones = response.data['results'] if isinstance(response.data, dict) else response.data
    assert zones[0]['free_delivery_threshold'] == '100.00'
