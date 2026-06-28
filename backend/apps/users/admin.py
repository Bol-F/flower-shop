from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'username', 'city', 'loyalty_points', 'is_staff', 'date_joined')
    search_fields = ('email', 'username')
    ordering = ('-date_joined',)
    fieldsets = BaseUserAdmin.fieldsets + (
        (_('Extra info'), {'fields': ('phone', 'address', 'city', 'language', 'currency', 'loyalty_points')}),
    )
