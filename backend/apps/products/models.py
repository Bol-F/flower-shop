from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from apps.categories.models import Category


class Product(models.Model):
    name = models.CharField(_('name'), max_length=200)
    slug = models.SlugField(_('slug'), unique=True, blank=True)
    description = models.TextField(_('description'))
    price = models.DecimalField(_('price'), max_digits=10, decimal_places=2)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name=_('category'),
    )
    image = models.ImageField(_('image'), upload_to='products/', blank=True, null=True)
    stock = models.PositiveIntegerField(_('stock'), default=0)
    is_available = models.BooleanField(_('is available'), default=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('Product')
        verbose_name_plural = _('Products')
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def is_in_stock(self):
        return self.stock > 0

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
