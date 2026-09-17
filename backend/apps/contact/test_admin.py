import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Permission
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory

from apps.users.models import User

from .admin import UserMessageAdmin
from .models import UserMessage


@pytest.fixture
def admin_request(db):
    user = User.objects.create_superuser(
        username='support-admin', email='support-admin@example.com', password='safe-password'
    )
    request = RequestFactory().post('/admin/contact/usermessage/')
    request.user = user
    request.session = {}
    request._messages = FallbackStorage(request)
    return request


@pytest.fixture
def incoming_message(db):
    customer = User.objects.create_user(
        username='support-customer',
        email='support-customer@example.com',
        password='safe-password',
    )
    return UserMessage.objects.create(
        user=customer,
        subject='Delivery question',
        body='When will my flowers arrive?',
    )


def _save_admin_reply(message_admin, request, message, reply):
    form_class = message_admin.get_form(request, obj=message)
    form = form_class(data={'admin_reply': reply}, instance=message)
    assert form.is_valid(), form.errors
    message_admin.save_model(request, form.save(commit=False), form, change=True)
    message.refresh_from_db()


@pytest.mark.django_db
def test_admin_reply_sets_and_clears_reply_metadata(admin_request, incoming_message):
    message_admin = UserMessageAdmin(UserMessage, AdminSite())
    assert message_admin.has_add_permission(admin_request) is False

    _save_admin_reply(message_admin, admin_request, incoming_message, 'Courier is on the way.')
    assert incoming_message.is_read is True
    assert incoming_message.replied_at is not None
    first_reply_time = incoming_message.replied_at

    _save_admin_reply(message_admin, admin_request, incoming_message, 'Updated arrival time.')
    assert incoming_message.replied_at >= first_reply_time

    _save_admin_reply(message_admin, admin_request, incoming_message, '   ')
    assert incoming_message.admin_reply == ''
    assert incoming_message.replied_at is None


@pytest.mark.django_db
def test_admin_direction_and_bulk_mark_read(admin_request, incoming_message):
    outgoing = UserMessage.objects.create(
        user=incoming_message.user,
        subject=incoming_message.subject,
        body='We will arrive tomorrow.',
        is_from_admin=True,
        is_read=False,
    )
    message_admin = UserMessageAdmin(UserMessage, AdminSite())
    assert message_admin.message_direction(incoming_message) != message_admin.message_direction(
        outgoing
    )
    assert 'is_from_admin' in message_admin.list_filter
    assert {'is_read', 'admin_reply'} <= set(
        message_admin.get_readonly_fields(admin_request, outgoing)
    )

    message_admin.mark_selected_read(
        admin_request,
        UserMessage.objects.filter(pk__in=(incoming_message.pk, outgoing.pk)),
    )
    incoming_message.refresh_from_db()
    outgoing.refresh_from_db()
    assert incoming_message.is_read is True
    assert outgoing.is_read is False


@pytest.mark.django_db
def test_view_only_support_staff_cannot_use_mark_read_action(incoming_message):
    viewer = User.objects.create_user(
        username='support-viewer',
        email='support-viewer@example.com',
        password='safe-password',
        is_staff=True,
    )
    viewer.user_permissions.add(
        Permission.objects.get(content_type__app_label='contact', codename='view_usermessage')
    )
    request = RequestFactory().get('/admin/contact/usermessage/')
    request.user = viewer
    message_admin = UserMessageAdmin(UserMessage, AdminSite())
    assert 'mark_selected_read' not in message_admin.get_actions(request)
