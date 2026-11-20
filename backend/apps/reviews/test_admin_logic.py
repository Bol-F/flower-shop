import pytest
from django.urls import reverse

from apps.reviews.models import Review
from apps.users.models import User


@pytest.mark.django_db
@pytest.mark.parametrize('query', [None, 'garden-roses', 'Fragrant', 'reviewer@example.test'])
def test_admin_review_list_and_search_use_the_stored_product_slug(client, query):
    staff = User.objects.create_superuser(
        username='review-admin', email='review-admin@example.test', password='test-only-password'
    )
    reviewer = User.objects.create_user(username='reviewer', email='reviewer@example.test')
    review = Review.objects.create(
        user=reviewer, product='garden-roses', rating=5, body='Fragrant flowers'
    )
    client.force_login(staff)

    response = client.get(reverse('admin:reviews_review_changelist'), {'q': query} if query else {})

    assert response.status_code == 200
    assert review in response.context['cl'].result_list
