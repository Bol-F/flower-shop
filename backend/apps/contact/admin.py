from django.contrib import admin, messages
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from .models import UserMessage


@admin.register(UserMessage)
class UserMessageAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user_email',
        'message_direction',
        'subject',
        'is_read',
        'has_reply',
        'created_at',
    )
    list_filter = ('is_from_admin', 'is_read', 'created_at')
    search_fields = ('user__email', 'user__username', 'subject', 'body')
    list_select_related = ('user',)
    readonly_fields = ('user', 'subject', 'body', 'is_from_admin', 'created_at', 'replied_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    list_per_page = 25
    actions = ('mark_selected_read',)

    fieldsets = (
        (
            _('Incoming message'),
            {
                'fields': ('user', 'is_from_admin', 'subject', 'body', 'created_at', 'is_read'),
            },
        ),
        (
            _('Admin reply'),
            {
                'fields': ('admin_reply', 'replied_at'),
            },
        ),
    )

    @admin.display(description=_('From'), ordering='user__email')
    def user_email(self, obj):
        return obj.user.email

    @admin.display(description=_('Direction'), ordering='is_from_admin')
    def message_direction(self, obj):
        return _('Support to customer') if obj.is_from_admin else _('Customer to support')

    @admin.display(description=_('Replied'), boolean=True)
    def has_reply(self, obj):
        return bool(obj.admin_reply)

    def has_add_permission(self, request):
        return False

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        if obj and obj.is_from_admin:
            return (*fields, 'is_read', 'admin_reply')
        return fields

    def save_model(self, request, obj, form, change):
        if change and not obj.is_from_admin and 'admin_reply' in form.changed_data:
            if obj.admin_reply.strip():
                obj.replied_at = timezone.now()
                obj.is_read = True
            else:
                obj.admin_reply = ''
                obj.replied_at = None
        super().save_model(request, obj, form, change)

    @admin.action(description=_('Mark selected incoming messages as read'), permissions=['change'])
    def mark_selected_read(self, request, queryset):
        updated = queryset.filter(is_from_admin=False, is_read=False).update(is_read=True)
        self.message_user(
            request,
            ngettext(
                '%(count)d incoming message marked as read.',
                '%(count)d incoming messages marked as read.',
                updated,
            )
            % {'count': updated},
            level=messages.SUCCESS,
        )
