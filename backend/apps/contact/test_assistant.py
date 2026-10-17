import json
from unittest.mock import Mock, patch

import pytest
import requests
from django.urls import reverse
from django.core.cache import cache
from rest_framework.test import APIClient

from apps.products.models import Product
from apps.users.models import User


pytestmark = pytest.mark.django_db


@pytest.fixture
def assistant_client(settings):
    settings.FLOWER_ASSISTANT_ENABLED = True
    settings.GEMINI_API_KEY = 'private-gemini-test-key'
    settings.GEMINI_MODEL = 'gemini-3.5-flash-lite'
    settings.TAVILY_API_KEY = ''
    client = APIClient()
    client.force_authenticate(User.objects.create_user('flower-test', 'private@example.test', 'pw'))
    return client


def provider_response(data):
    return Mock(ok=True, is_redirect=False, json=Mock(return_value=data))


def gemini_response(answer='Try our rose bouquet.'):
    return provider_response({'candidates': [{'content': {'parts': [{'text': answer}]}}]})


def test_assistant_is_disabled_by_default_and_requires_authentication(settings):
    settings.FLOWER_ASSISTANT_ENABLED = False
    settings.GEMINI_API_KEY = 'configured-but-disabled'
    client = APIClient()
    response = client.get(reverse('assistant-capabilities'))
    assert response.data == {'enabled': False, 'web_search_enabled': False}
    assert 'no-store' in response['Cache-Control']
    assert (
        client.post(reverse('flower-advice'), {'message': 'Roses?'}, format='json').status_code
        == 401
    )
    client.force_authenticate(User.objects.create_user('disabled-user', password='pw'))
    with patch('apps.contact.assistant.requests.post') as post:
        assert (
            client.post(reverse('flower-advice'), {'message': 'Roses?'}, format='json').status_code
            == 503
        )
    post.assert_not_called()


def test_catalog_advice_sends_only_public_available_catalog(assistant_client):
    Product.objects.create(name='Rose bouquet', price='30', stock=2, description='Fresh roses')
    Product.objects.create(name='Sold out', price='40', stock=0)
    Product.objects.create(name='Hidden bouquet', price='50', stock=3, is_available=False)
    with patch('apps.contact.assistant.requests.post', return_value=gemini_response()) as post:
        response = assistant_client.post(
            reverse('flower-advice'),
            {'message': 'A birthday gift?', 'language': 'UZ'},
            format='json',
        )
    assert response.status_code == 200
    assert response.data == {'answer': 'Try our rose bouquet.', 'sources': []}
    assert 'no-store' in response['Cache-Control']
    post.assert_called_once()
    args, kwargs = post.call_args
    assert args[0].startswith('https://generativelanguage.googleapis.com/')
    assert kwargs['headers'] == {'x-goog-api-key': 'private-gemini-test-key'}
    assert kwargs['allow_redirects'] is False
    payload = kwargs['json']
    prompt = json.loads(payload['contents'][0]['parts'][0]['text'])
    assert [p['name'] for p in prompt['catalog']] == ['Rose bouquet']
    assert prompt['catalog'][0]['price'] == '30.00'
    assert 'private@example.test' not in json.dumps(payload)
    assert 'Uzbek' in payload['systemInstruction']['parts'][0]['text']


def test_web_search_requires_explicit_opt_in_and_sanitizes_sources(assistant_client, settings):
    settings.TAVILY_API_KEY = 'private-tavily-key'
    search = provider_response(
        {
            'results': [
                {
                    'title': 'Care guide',
                    'url': 'https://example.test/care',
                    'content': 'Trim stems',
                },
                {'title': 'Unsafe', 'url': 'javascript:alert(1)'},
                {'title': 'Credentials', 'url': 'https://user:secret@example.test/'},
            ]
        }
    )
    with patch(
        'apps.contact.assistant.requests.post',
        side_effect=[search, gemini_response('Trim the stems.')],
    ) as post:
        response = assistant_client.post(
            reverse('flower-advice'),
            {'message': 'How to care for roses?', 'use_web_search': True},
            format='json',
        )
    assert response.status_code == 200
    assert response.data['sources'] == [{'title': 'Care guide', 'url': 'https://example.test/care'}]
    assert post.call_count == 2
    first = post.call_args_list[0]
    assert first.args[0] == 'https://api.tavily.com/search'
    assert first.kwargs['headers'] == {'Authorization': 'Bearer private-tavily-key'}
    assert first.kwargs['json']['include_raw_content'] is False
    with patch('apps.contact.assistant.requests.post', return_value=gemini_response()) as post:
        assistant_client.post(reverse('flower-advice'), {'message': 'Roses?'}, format='json')
    post.assert_called_once()


@pytest.mark.parametrize(
    'provider_data',
    [
        [],
        {},
        {'candidates': []},
        {'candidates': [{'content': {'parts': [{'thought': True, 'text': 'Hidden'}]}}]},
    ],
)
def test_malformed_or_blocked_provider_answers_fail_safely(assistant_client, provider_data):
    with patch(
        'apps.contact.assistant.requests.post', return_value=provider_response(provider_data)
    ):
        response = assistant_client.post(
            reverse('flower-advice'), {'message': 'Roses?'}, format='json'
        )
    assert response.status_code == 503
    assert 'private-gemini-test-key' not in str(response.data)


def test_provider_failures_do_not_disclose_keys(assistant_client):
    with patch(
        'apps.contact.assistant.requests.post',
        side_effect=requests.Timeout('private-gemini-test-key'),
    ):
        response = assistant_client.post(
            reverse('flower-advice'), {'message': 'Roses?'}, format='json'
        )
    assert response.status_code == 503
    assert 'private-gemini-test-key' not in str(response.data)


@pytest.mark.parametrize(
    'payload',
    [
        {'message': ''},
        {'message': 'a' * 1501},
        {'message': 'Roses?', 'language': 'invalid'},
        {'message': 'Roses?', 'use_web_search': True},
    ],
)
def test_invalid_questions_do_not_contact_providers(assistant_client, payload):
    with patch('apps.contact.assistant.requests.post') as post:
        response = assistant_client.post(reverse('flower-advice'), payload, format='json')
    assert response.status_code == 400
    post.assert_not_called()


def test_invalid_model_configuration_disables_assistant(assistant_client, settings):
    settings.GEMINI_MODEL = '../invalid?key=secret'
    assert assistant_client.get(reverse('assistant-capabilities')).data['enabled'] is False


def test_advice_rate_limit_does_not_call_provider_again(assistant_client):
    cache.clear()
    with (
        patch('apps.contact.assistant_views.AssistantThrottle.rate', '1/minute', create=True),
        patch(
            'apps.contact.assistant.requests.post',
            return_value=gemini_response(),
        ) as post,
    ):
        first = assistant_client.post(
            reverse('flower-advice'), {'message': 'Roses?'}, format='json'
        )
        second = assistant_client.post(
            reverse('flower-advice'), {'message': 'Roses?'}, format='json'
        )
    assert first.status_code == 200
    assert second.status_code == 429
    assert 'no-store' in second['Cache-Control']
    post.assert_called_once()
