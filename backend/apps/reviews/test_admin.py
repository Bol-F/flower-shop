from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory

from .admin import ReviewAdmin
from .models import Review


def test_review_admin_does_not_offer_unusable_add_form():
    review_admin = ReviewAdmin(Review, AdminSite())
    request = RequestFactory().get('/admin/reviews/review/')

    assert review_admin.has_add_permission(request) is False
    assert {'user', 'product', 'rating', 'body'} <= set(review_admin.readonly_fields)
