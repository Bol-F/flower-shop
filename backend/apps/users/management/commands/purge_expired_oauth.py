from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.users.models import (
    OAuthExchangeCode,
    OAuthLinkExchangeCode,
    OAuthLoginAttempt,
)


class Command(BaseCommand):
    help = 'Delete expired OAuth attempts and one-time exchange codes.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Report expired rows without deleting them.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        now = timezone.now()
        querysets = (
            ('login attempts', OAuthLoginAttempt.objects.filter(expires_at__lte=now)),
            ('login exchange codes', OAuthExchangeCode.objects.filter(expires_at__lte=now)),
            ('link exchange codes', OAuthLinkExchangeCode.objects.filter(expires_at__lte=now)),
        )
        counts = {label: queryset.count() for label, queryset in querysets}
        if not options['dry_run']:
            for _, queryset in querysets:
                queryset.delete()
        action = 'Would delete' if options['dry_run'] else 'Deleted'
        summary = ', '.join(f'{count} {label}' for label, count in counts.items())
        self.stdout.write(self.style.SUCCESS(f'{action} {summary}.'))
