from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'user_email', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('product', 'user__email', 'user__username', 'body')
    readonly_fields = ('user', 'product', 'rating', 'body', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    list_per_page = 25

    @admin.display(description=_('From'), ordering='user__email')
    def user_email(self, obj):
        return obj.user.email
