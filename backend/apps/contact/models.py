from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class UserMessage(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='admin_messages',
        verbose_name=_('user'),
    )
    subject = models.CharField(_('subject'), max_length=200)
    body = models.TextField(_('message body'))
    is_read = models.BooleanField(_('is read'), default=False)
    admin_reply = models.TextField(_('admin reply'), blank=True)
    replied_at = models.DateTimeField(_('replied at'), null=True, blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('User message')
        verbose_name_plural = _('User messages')

    def __str__(self):
        return f'[{self.user.email}] {self.subject}'
