from django.contrib import admin
from .models import UserMessage


@admin.register(UserMessage)
class UserMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_email', 'subject', 'is_read', 'has_reply', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__email', 'user__username', 'subject', 'body')
    readonly_fields = ('user', 'subject', 'body', 'created_at', 'replied_at')
    ordering = ('-created_at',)
    list_per_page = 25

    fieldsets = (
        ('Incoming Message', {
            'fields': ('user', 'subject', 'body', 'created_at', 'is_read'),
        }),
        ('Admin Reply', {
            'fields': ('admin_reply', 'replied_at'),
        }),
    )

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'From'
    user_email.admin_order_field = 'user__email'

    def has_reply(self, obj):
        return bool(obj.admin_reply)
    has_reply.boolean = True
    has_reply.short_description = 'Replied'
