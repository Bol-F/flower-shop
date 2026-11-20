"""Malformed public webhook credentials must be rejected without server errors."""

import base64
from urllib.parse import urlencode

import pytest
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from .test_payments import CLICK_SETTINGS, PAYME_SETTINGS


@pytest.mark.django_db
@override_settings(**PAYME_SETTINGS)
@pytest.mark.parametrize(
    'credential', ['Paycom:p\u00e4ssword', '\u041f\u0430\u0439com:payme-secret']
)
def test_payme_rejects_non_ascii_credentials_safely(credential):
    authorization = 'Basic ' + base64.b64encode(credential.encode('utf-8')).decode('ascii')

    response = APIClient().post(
        reverse('payme-webhook'),
        {'id': 1, 'method': 'CheckPerformTransaction', 'params': {}},
        format='json',
        HTTP_AUTHORIZATION=authorization,
        REMOTE_ADDR='185.234.113.1',
    )

    assert response.status_code == 200
    assert response.data['error']['code'] == -32504


@pytest.mark.django_db
@override_settings(**CLICK_SETTINGS)
def test_click_rejects_non_ascii_signature_safely():
    response = APIClient().post(
        reverse('click-prepare'),
        urlencode({'action': '0', 'service_id': '12345', 'sign_string': '\u00e9' * 32}),
        content_type='application/x-www-form-urlencoded',
    )

    assert response.status_code == 200
    assert response.data['error'] == -1
