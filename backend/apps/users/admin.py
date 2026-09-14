from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import SocialIdentity, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'username', 'city', 'loyalty_points', 'is_staff', 'date_joined')
    search_fields = ('email', 'username')
    ordering = ('-date_joined',)
    fieldsets = BaseUserAdmin.fieldsets + (
        (
            _('Extra info'),
            {'fields': ('phone', 'address', 'city', 'language', 'currency', 'loyalty_points')},
        ),
    )


@admin.register(SocialIdentity)
class SocialIdentityAdmin(admin.ModelAdmin):
    list_display = ('provider', 'subject', 'user', 'email', 'email_verified', 'created_at')
    list_filter = ('provider', 'email_verified', 'created_at')
    search_fields = ('subject', 'email', 'user__email', 'user__username')
    readonly_fields = tuple(field.name for field in SocialIdentity._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
