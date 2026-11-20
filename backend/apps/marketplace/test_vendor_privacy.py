import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.marketplace.models import City, Vendor


@pytest.mark.django_db
def test_public_florist_directory_hides_internal_commission():
    Vendor.objects.create(name='Public florist', commission_percent='17.50')

    response = APIClient().get(reverse('marketplace-vendor-list'))

    assert response.status_code == 200
    assert response.data['count'] == 1
    assert 'commission_percent' not in response.data['results'][0]


@pytest.mark.django_db
def test_public_florist_directory_hides_inactive_cities():
    city = City.objects.create(name='Inactive florist city', is_active=False)
    Vendor.objects.create(name='Unavailable florist', city=city)

    response = APIClient().get(reverse('marketplace-vendor-list'))

    assert response.status_code == 200
    assert response.data['count'] == 0
