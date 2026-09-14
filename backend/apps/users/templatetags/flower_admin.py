"""Small, permission-aware helpers for the flower shop's admin workspace."""

from urllib.parse import urlencode

from django import template
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db.models import F
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.contact.models import UserMessage
from apps.orders.models import Order
from apps.products.models import Product

register = template.Library()


def _admin_url(request, model, action='changelist', obj=None):
    opts = model._meta
    return reverse(
        f'admin:{opts.app_label}_{opts.model_name}_{action}',
        args=[obj.pk] if obj is not None else None,
        current_app=getattr(request, 'current_app', admin.site.name),
    )


def _visible_admin(request, model):
    model_admin = admin.site._registry.get(model)
    if (
        model_admin is not None
        and model_admin.has_module_permission(request)
        and model_admin.has_view_or_change_permission(request)
    ):
        return model_admin
    return None


def _filtered_url(url, **filters):
    return f'{url}?{urlencode(filters)}'


@register.simple_tag(takes_context=True)
def flower_dashboard(context):
    """Use the same permissions and row visibility as the registered admin views."""
    dashboard = {
        'today': timezone.localdate(),
        'cards': [],
        'recent_orders': [],
        'stock_items': [],
        'urls': {},
    }
    request = context.get('request')
    if request is None or not admin.site.has_permission(request):
        return dashboard

    order_admin = _visible_admin(request, Order)
    if order_admin is not None:
        orders = order_admin.get_queryset(request)
        orders_url = _admin_url(request, Order)
        dashboard['urls']['orders'] = orders_url
        try:
            dashboard['urls']['delivery_map'] = reverse(
                'admin:orders_order_delivery_map',
                current_app=getattr(request, 'current_app', admin.site.name),
            )
        except NoReverseMatch:
            pass
        delivery_statuses = [
            value for value in Order.Status.values if value != Order.Status.CANCELLED
        ]
        dashboard['cards'].extend(
            [
                {
                    'label': _('New orders'),
                    'value': orders.filter(status=Order.Status.PENDING).count(),
                    'detail': _('Awaiting confirmation'),
                    'url': _filtered_url(orders_url, status__exact=Order.Status.PENDING),
                    'tone': 'rose',
                },
                {
                    'label': _('Deliveries today'),
                    'value': orders.filter(
                        delivery_date=dashboard['today'], status__in=delivery_statuses
                    ).count(),
                    'detail': _('Scheduled for today'),
                    'url': _filtered_url(
                        orders_url,
                        delivery_date__exact=dashboard['today'].isoformat(),
                        status__in=','.join(delivery_statuses),
                    ),
                    'tone': 'sage',
                },
            ]
        )
        dashboard['recent_orders'] = [
            {
                'label': _('Order #%(number)s') % {'number': order.pk},
                'url': _admin_url(request, Order, 'change', order),
                'customer': order.user.get_full_name() or order.user.email,
                'status': order.get_status_display(),
                'status_code': order.status,
                'total': order.total_price,
                'delivery_date': order.delivery_date,
            }
            for order in orders.select_related('user').order_by('-created_at', '-pk')[:5]
        ]

    product_admin = _visible_admin(request, Product)
    if product_admin is not None:
        products = product_admin.get_queryset(request)
        products_url = _admin_url(request, Product)
        dashboard['urls']['products'] = products_url
        if product_admin.has_add_permission(request):
            dashboard['urls']['add_product'] = _admin_url(request, Product, 'add')
        low_stock = products.filter(is_available=True, stock__lte=F('low_stock_threshold'))
        low_stock_url = products_url
        if any(
            getattr(filter_class, 'parameter_name', None) == 'stock_level'
            for filter_class in product_admin.get_list_filter(request)
        ):
            low_stock_url = _filtered_url(products_url, stock_level='low')
        dashboard['urls']['stock'] = low_stock_url
        dashboard['cards'].extend(
            [
                {
                    'label': _('Available bouquets'),
                    'value': products.filter(is_available=True).count(),
                    'detail': _('Visible in your catalog'),
                    'url': _filtered_url(products_url, is_available__exact='1'),
                    'tone': 'plum',
                },
                {
                    'label': _('Stock alerts'),
                    'value': low_stock.count(),
                    'detail': _('Ready for a restock'),
                    'url': low_stock_url,
                    'tone': 'amber',
                },
            ]
        )
        dashboard['stock_items'] = [
            {
                'name': product.name,
                'url': _admin_url(request, Product, 'change', product),
                'stock': product.stock,
                'threshold': product.low_stock_threshold,
                'image_url': product.image.url if product.image else '',
            }
            for product in low_stock.order_by('stock', 'name', 'pk')[:5]
        ]

    user_model = get_user_model()
    if _visible_admin(request, user_model) is not None:
        dashboard['urls']['customers'] = _admin_url(request, user_model)
    if _visible_admin(request, UserMessage) is not None:
        dashboard['urls']['messages'] = _admin_url(request, UserMessage)

    return dashboard


@register.simple_tag
def flower_navigation(available_apps):
    """Regroup Django's already-authorized links without losing any model."""
    sections = [
        (_('Shop'), ('orders', 'products', 'categories')),
        (_('Operations'), ('marketplace',)),
        (_('Customers'), ('contact', 'users', 'reviews', 'cart')),
        (_('System'), ()),
    ]
    app_priority = {
        app_label: index
        for index, app_label in enumerate(
            (
                'orders',
                'products',
                'categories',
                'marketplace',
                'contact',
                'users',
                'reviews',
                'cart',
            )
        )
    }
    model_priority = {
        'order': 0,
        'deliveryzone': 1,
        'paymentattempt': 2,
        'paymentevent': 3,
        'notificationlog': 4,
        'city': 0,
        'vendor': 1,
        'courier': 2,
        'promocode': 3,
        'wishlistitem': 4,
        'user': 0,
        'socialidentity': 1,
    }
    icons = {
        'orders': 'orders',
        'products': 'flower',
        'categories': 'grid',
        'marketplace': 'delivery',
        'contact': 'message',
        'users': 'users',
        'reviews': 'star',
        'cart': 'bag',
    }
    system_models = {
        ('orders', 'paymentattempt'),
        ('orders', 'paymentevent'),
        ('orders', 'notificationlog'),
    }
    shop_priority = {
        ('orders', 'order'): 0,
        ('products', 'product'): 1,
        ('categories', 'category'): 2,
        ('orders', 'deliveryzone'): 3,
    }
    groups = [{'label': label, 'items': []} for label, _apps in sections]
    for app in sorted(
        available_apps or [],
        key=lambda item: (app_priority.get(item['app_label'], 99), str(item['name'])),
    ):
        app_label = app['app_label']
        group_index = next(
            (index for index, (_label, apps) in enumerate(sections) if app_label in apps),
            len(sections) - 1,
        )
        for model in sorted(
            app['models'],
            key=lambda item: (
                model_priority.get(item['object_name'].lower(), 99),
                str(item['name']),
            ),
        ):
            model_name = model['object_name'].lower()
            target_group = (
                len(sections) - 1 if (app_label, model_name) in system_models else group_index
            )
            groups[target_group]['items'].append(
                {
                    **model,
                    'app_label': app_label,
                    'model_name': model_name,
                    'icon': icons.get(app_label, 'settings'),
                }
            )
    groups[0]['items'].sort(
        key=lambda item: shop_priority.get((item['app_label'], item['model_name']), 99)
    )
    return [group for group in groups if group['items']]
