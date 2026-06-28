from django.contrib import admin
from django.urls import path, re_path, include
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.utils.translation import gettext_lazy as _
from django.views.static import serve as serve_media

admin.site.site_header = _('Bloom & Petal administration')
admin.site.site_title = _('Bloom & Petal admin')
admin.site.index_title = _('Dashboard')

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),  # set_language view
    path('api/auth/', include('apps.users.urls')),
    path('api/categories/', include('apps.categories.urls')),
    path('api/products/', include('apps.products.urls')),
    path('api/cart/', include('apps.cart.urls')),
    path('api/orders/', include('apps.orders.urls')),
    path('api/marketplace/', include('apps.marketplace.urls')),
    path('api/contact/', include('apps.contact.urls')),
    path('api/reviews/', include('apps.reviews.urls')),
]

# /admin/ stays English (default), /ru/admin/ and /uz/admin/ switch language
urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    prefix_default_language=False,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # Serve product photos in production too — fine at this scale; move
    # media to S3/Cloudinary if uploads ever grow beyond seeded images.
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve_media,
                {'document_root': settings.MEDIA_ROOT}),
    ]
