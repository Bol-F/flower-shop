from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import UserMessage


@admin.register(UserMessage)
class UserMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_email', 'subject', 'is_read', 'has_reply', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__email', 'user__username', 'subject', 'body')
    readonly_fields = ('user', 'subject', 'body', 'created_at', 'replied_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    list_per_page = 25

    fieldsets = (
        (_('Incoming message'), {
            'fields': ('user', 'subject', 'body', 'created_at', 'is_read'),
        }),
        (_('Admin reply'), {
            'fields': ('admin_reply', 'replied_at'),
        }),
    )

    @admin.display(description=_('From'), ordering='user__email')
    def user_email(self, obj):
        return obj.user.email

    @admin.display(description=_('Replied'), boolean=True)
    def has_reply(self, obj):
        return bool(obj.admin_reply)
