"""
Management command: python manage.py download_flower_images

Downloads real, high-quality flower photos from Pexels and saves them
to media/products/<slug>.jpg, then links each to its Product record.

Setup (one-time, free):
  1. Go to https://www.pexels.com/api/
  2. Click "Get Started" — sign up, it's free
  3. Copy your API key
  4. Add  PEXELS_API_KEY=your_key_here  to backend/.env
"""
import os
import time
import requests
from django.core.management.base import BaseCommand
from django.conf import settings

PEXELS_SEARCH = 'https://api.pexels.com/v1/search'

# ── Carefully chosen queries for natural, sharp photos ───────────────────────
FLOWER_QUERIES = {
    # Roses
    'crimson-velvet-rose':       'deep red rose closeup',
    'champagne-garden-rose':     'champagne blush garden rose',
    'midnight-blue-rose':        'dark purple blue rose',
    'pink-whisper-spray-rose':   'pink spray rose bunch',
    'eternal-white-rose':        'white rose glass dome preserved',
    # Tulips
    'parrot-tulip-fiesta':       'parrot tulip colorful',
    'double-dutch-peach-tulip':  'peach tulip double bloom',
    'queen-of-night-tulip':      'dark maroon black tulip',
    'rainbow-spring-mix':        'colorful tulip field mixed',
    # Sunflowers
    'giant-helianthus':          'giant sunflower closeup',
    'teddy-bear-sunflower':      'fluffy double sunflower',
    'autumn-rust-sunflower':     'rust orange sunflower autumn',
    # Exotic
    'bird-of-paradise':          'bird of paradise tropical flower',
    'purple-vanda-orchid':       'purple vanda orchid',
    'king-protea':               'king protea south africa flower',
    'red-anthurium':             'red anthurium tropical flower',
    'heliconia-lobster-claw':    'heliconia lobster claw tropical',
    # Seasonal
    'cherry-blossom-branch':     'cherry blossom branch sakura',
    'lavender-dreams-bundle':    'lavender bundle purple field',
    'blush-peony-cloud':         'pink peony closeup bloom',
    'ranunculus-sunrise':        'ranunculus coral peach flower',
    # Bouquets
    'romance-in-red':            'red roses romantic bouquet',
    'garden-sunshine-bouquet':   'sunflower mixed bouquet bright',
    'pastel-paradise':           'pastel flowers bouquet spring',
    'eternal-love-premium':      'luxury flower arrangement roses lilies',
    # Wildflowers
    'blue-cornflower-bundle':    'blue cornflower wildflower',
    'dried-pampas-plume':        'pampas grass dried plume',
    'meadow-magic-mix':          'wildflower meadow mixed bouquet',
}


def fetch_photo_url(query, api_key):
    """Return the best square-ish photo URL from Pexels for a given query."""
    headers = {'Authorization': api_key}
    params = {
        'query': query,
        'per_page': 3,
        'orientation': 'square',
    }
    resp = requests.get(PEXELS_SEARCH, headers=headers, params=params, timeout=15)
    resp.raise_for_status()
    photos = resp.json().get('photos', [])
    if not photos:
        return None
    # Prefer the largest square crop available
    return photos[0]['src'].get('large2x') or photos[0]['src']['large']


def download_image(url, dest_path):
    resp = requests.get(url, timeout=30, stream=True)
    resp.raise_for_status()
    with open(dest_path, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)


class Command(BaseCommand):
    help = 'Download real flower photos from Pexels and attach them to products'

    def handle(self, *args, **options):
        from apps.products.models import Product

        api_key = env_value('PEXELS_API_KEY')
        if not api_key:
            self.stderr.write(self.style.ERROR(
                '\nPEXELS_API_KEY is not set.\n'
                '\nGet a free key in 2 minutes:\n'
                '  1. Go to  https://www.pexels.com/api/\n'
                '  2. Sign up (free, no card)\n'
                '  3. Copy your API key\n'
                '  4. Add  PEXELS_API_KEY=your_key  to backend/.env\n'
                '  5. Run this command again\n'
            ))
            return

        dest_dir = os.path.join(settings.MEDIA_ROOT, 'products')
        os.makedirs(dest_dir, exist_ok=True)

        self.stdout.write(self.style.MIGRATE_HEADING(
            f'Downloading {len(FLOWER_QUERIES)} flower photos from Pexels…\n'
        ))

        ok = skipped = failed = 0

        for slug, query in FLOWER_QUERIES.items():
            try:
                product = Product.objects.get(slug=slug)
            except Product.DoesNotExist:
                self.stdout.write(f'  [{slug}] product not found — skip')
                skipped += 1
                continue

            try:
                photo_url = fetch_photo_url(query, api_key)
                if not photo_url:
                    self.stdout.write(self.style.WARNING(
                        f'  {product.name} — no photo found for "{query}"'
                    ))
                    skipped += 1
                    continue

                filename = f'{slug}.jpg'
                filepath = os.path.join(dest_dir, filename)
                download_image(photo_url, filepath)

                product.image = f'products/{filename}'
                product.save(update_fields=['image'])

                ok += 1
                self.stdout.write(
                    f'  {product.name:<35} {self.style.SUCCESS("✓")}'
                )

            except Exception as exc:
                self.stdout.write(self.style.ERROR(
                    f'  {product.name} — ERROR: {exc}'
                ))
                failed += 1

            # Pexels free tier: 200 req/hour — stay well within limits
            time.sleep(0.4)

        self.stdout.write('\n' + self.style.SUCCESS(
            f'Done — {ok} downloaded, {skipped} skipped, {failed} failed.'
        ))


def env_value(key):
    """Read a key from os.environ or django settings, returning None if absent."""
    import environ
    val = os.environ.get(key)
    if val:
        return val
    try:
        return getattr(settings, key)
    except AttributeError:
        return None
