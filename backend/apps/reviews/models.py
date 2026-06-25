from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class Review(models.Model):
    """A customer's star rating + comment for a catalog product.

    Reviews are keyed by the storefront product slug. Keeping this as a
    string lets reviews work for API-backed products and for offline demo
    products. One review per user per product — re-submitting updates it.
    """
    product = models.CharField(_('product'), max_length=100, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_('user'),
    )
    rating = models.PositiveSmallIntegerField(
        _('rating'),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    body = models.TextField(_('comment'), blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('user', 'product')
        verbose_name = _('Review')
        verbose_name_plural = _('Reviews')

    def __str__(self):
        return f'[{self.product}] {self.user.email} · {self.rating}★'
