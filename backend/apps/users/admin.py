from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import SocialIdentity, User


class FlowerUserCreationForm(UserCreationForm):
    """Require the email login identity and reject case-variant duplicates."""

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email', 'username')

    def clean_email(self):
        email = User.objects.normalize_email(self.cleaned_data['email']).strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError(_('A user with this email already exists.'))
        return email


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = FlowerUserCreationForm
    add_fieldsets = (
        (
            None,
            {'classes': ('wide',), 'fields': ('email', 'username', 'password1', 'password2')},
        ),
    )
    list_display = (
        'email',
        'username',
        'city',
        'loyalty_points',
        'is_active',
        'is_staff',
        'date_joined',
    )
    list_filter = ('is_active', 'is_staff', 'language', 'currency')
    search_fields = ('email', 'username', 'phone')
    ordering = ('-date_joined',)
    readonly_fields = ('last_login', 'date_joined')
    fieldsets = BaseUserAdmin.fieldsets + (
        (
            _('Extra info'),
            {'fields': ('phone', 'address', 'city', 'language', 'currency', 'loyalty_points')},
        ),
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset if request.user.is_superuser else queryset.filter(is_staff=False)

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        if request.user.is_superuser:
            return fields
        return (*fields, 'loyalty_points', 'is_staff', 'is_superuser', 'groups', 'user_permissions')

    def has_change_permission(self, request, obj=None):
        if obj is not None and obj.is_staff and not request.user.is_superuser:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and obj.is_staff and not request.user.is_superuser:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(SocialIdentity)
class SocialIdentityAdmin(admin.ModelAdmin):
    list_display = (
        'provider',
        'issuer',
        'subject',
        'user',
        'email',
        'email_verified',
        'created_at',
    )
    list_filter = ('provider', 'email_verified', 'created_at')
    search_fields = ('issuer', 'subject', 'email', 'user__email', 'user__username')
    readonly_fields = tuple(field.name for field in SocialIdentity._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
