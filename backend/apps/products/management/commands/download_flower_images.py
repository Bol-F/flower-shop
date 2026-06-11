"""
Management command: python manage.py download_flower_images

Downloads real flower photos from Wikimedia Commons (public domain, free, no API key).
Searches the Commons API for each product, picks the best image, downloads at 900 px.
"""
import os
import time
import requests
from django.core.management.base import BaseCommand
from django.conf import settings

COMMONS_API = 'https://commons.wikimedia.org/w/api.php'
USER_AGENT  = 'FlowerShopProject/1.0 (educational; non-commercial)'

# ── Per-product: preferred known filename  +  fallback search query ───────────
FLOWER_MAP = {
    'crimson-velvet-rose': (
        'Red_rose.jpg',
        'red rose flower closeup macro'),
    'champagne-garden-rose': (
        'Rose_Amber_Flush_20070601.jpg',
        'rose cultivar cream'),
    'midnight-blue-rose': (
        'Blue_Rose_(3931263892).jpg',
        'purple blue rose flower'),
    'pink-whisper-spray-rose': (
        'Pink_roses_-_Flickr_-_maticsteve.jpg',
        'pink spray rose cluster'),
    'eternal-white-rose': (
        'White_rose.jpg',
        'white rose single closeup'),
    'parrot-tulip-fiesta': (
        'Tulipa_Estella_Rijnveld_2.jpg',
        'parrot tulip'),
    'double-dutch-peach-tulip': (
        'Tulipa_-_double_pink_(aka).jpg',
        'peach double tulip bloom'),
    'queen-of-night-tulip': (
        'Tulipa_-_Queen_of_Night.jpg',
        'Queen of Night dark tulip'),
    'rainbow-spring-mix': (
        'Keukenhof_tulips.jpg',
        'Keukenhof tulips'),
    'giant-helianthus': (
        'Sunflower_from_Silesia2.jpg',
        'sunflower closeup large bloom'),
    'teddy-bear-sunflower': (
        'Helianthus_annuus_3.jpg',
        'sunflower fluffy double bloom'),
    'autumn-rust-sunflower': (
        'Sunflower_Helianthus_annuus_Prado_Red.jpg',
        'sunflower red'),
    'bird-of-paradise': (
        'Bird_of_Paradise_(Strelitzia_Reginae).jpg',
        'strelitzia bird of paradise orange tropical'),
    'purple-vanda-orchid': (
        'Vanda_coerulea.jpg',
        'Vanda coerulea'),
    'king-protea': (
        'Protea_cynaroides_2.jpg',
        'Protea cynaroides'),
    'red-anthurium': (
        'Anthurium_andraeanum.jpg',
        'Anthurium andraeanum'),
    'heliconia-lobster-claw': (
        'Heliconia_rostrata_1.jpg',
        'heliconia lobster claw tropical red yellow'),
    'cherry-blossom-branch': (
        'Cherry_blossoms_in_Vancouver_3_crop.jpg',
        'cherry blossom sakura branch pink'),
    'lavender-dreams-bundle': (
        'Lavandula_angustifolia_Blütenstand.jpg',
        'lavender purple flower field'),
    'blush-peony-cloud': (
        'Pink_Peony_Flower_and_unopened_bud.jpg',
        'pink peony full bloom closeup'),
    'ranunculus-sunrise': (
        'Ranunculus_asiaticus_1.jpg',
        'Ranunculus asiaticus'),
    'romance-in-red': (
        'Bouquet_de_roses_roses.jpg',
        'red roses bouquet'),
    'garden-sunshine-bouquet': (
        'Sunflowers_in_a_vase.jpg',
        'sunflower bouquet bright yellow vase'),
    'pastel-paradise': (
        'Pink_flower_bouquet.jpg',
        'pink flower bouquet'),
    'eternal-love-premium': (
        'Flower_arrangement_-_geograph.org.uk.jpg',
        'flower arrangement'),
    'blue-cornflower-bundle': (
        'Centaurea_cyanus_-_Cornflower_-_Bleuet.jpg',
        'blue cornflower wildflower bouquet'),
    'dried-pampas-plume': (
        'Cortaderia_selloana_Pampas_grass.jpg',
        'pampas grass dried feathery plume'),
    'meadow-magic-mix': (
        'Wildflower_meadow.jpg',
        'wildflower meadow mixed colourful'),
}


def search_commons(query, limit=8):
    """Return the first JPEG/PNG filename found for a query."""
    r = requests.get(COMMONS_API, timeout=15, headers={'User-Agent': USER_AGENT},
                     params={
                         'action': 'query',
                         'list': 'search',
                         'srsearch': query,
                         'srnamespace': 6,
                         'srlimit': limit,
                         'format': 'json',
                     })
    r.raise_for_status()
    for item in r.json().get('query', {}).get('search', []):
        title = item['title']
        if any(title.lower().endswith(ext) for ext in ('.jpg', '.jpeg', '.png')):
            return title.replace('File:', '', 1)
    return None


def get_thumb_url(filename, width=900):
    """Resolve a Commons filename to a resized thumbnail URL."""
    r = requests.get(COMMONS_API, timeout=15, headers={'User-Agent': USER_AGENT},
                     params={
                         'action': 'query',
                         'titles': f'File:{filename}',
                         'prop': 'imageinfo',
                         'iiprop': 'url',
                         'iiurlwidth': width,
                         'format': 'json',
                     })
    r.raise_for_status()
    for page in r.json().get('query', {}).get('pages', {}).values():
        infos = page.get('imageinfo', [])
        if infos:
            return infos[0].get('thumburl') or infos[0].get('url')
    return None


def save_image(url, path, retries=4):
    for attempt in range(retries):
        try:
            r = requests.get(url, timeout=45, stream=True,
                             headers={'User-Agent': USER_AGENT})
            if r.status_code == 429:
                retry_after = int(r.headers.get('Retry-After', 0) or 0)
                time.sleep(max(retry_after, 15 * (attempt + 1)))
                continue
            r.raise_for_status()
            with open(path, 'wb') as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
            return
        except requests.RequestException:
            if attempt == retries - 1:
                raise
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f'still rate-limited after {retries} attempts: {url}')


class Command(BaseCommand):
    help = 'Download real flower photos from Wikimedia Commons (no API key needed)'

    def handle(self, *args, **options):
        from apps.products.models import Product

        dest = os.path.join(settings.MEDIA_ROOT, 'products')
        os.makedirs(dest, exist_ok=True)

        self.stdout.write(self.style.MIGRATE_HEADING(
            f'\nDownloading {len(FLOWER_MAP)} flower photos from Wikimedia Commons…\n'
        ))

        ok = failed = 0

        for slug, (preferred_file, fallback_query) in FLOWER_MAP.items():
            try:
                product = Product.objects.get(slug=slug)
            except Product.DoesNotExist:
                self.stdout.write(f'  [{slug}] not found in DB — skip')
                continue

            dest_filename = f'{slug}.jpg'
            dest_path = os.path.join(dest, dest_filename)

            # Resume support: keep good files from a previous run
            if os.path.exists(dest_path) and os.path.getsize(dest_path) > 10_000:
                product.image = f'products/{dest_filename}'
                product.save(update_fields=['image'])
                ok += 1
                self.stdout.write(f'  {product.name:<38} already on disk ✓')
                continue

            try:
                thumb_url = get_thumb_url(preferred_file)

                # Preferred file not found → search dynamically
                if not thumb_url:
                    filename = search_commons(fallback_query)
                    if filename:
                        thumb_url = get_thumb_url(filename)

                if not thumb_url:
                    self.stdout.write(self.style.WARNING(
                        f'  {product.name:<38} no image found'
                    ))
                    failed += 1
                    continue

                save_image(thumb_url, dest_path)
                product.image = f'products/{dest_filename}'
                product.save(update_fields=['image'])
                ok += 1
                self.stdout.write(f'  {product.name:<38} {self.style.SUCCESS("✓")}')

            except Exception as exc:
                self.stdout.write(self.style.ERROR(
                    f'  {product.name:<38} ERROR: {exc}'
                ))
                failed += 1

            time.sleep(3)   # be polite to the API — avoid 429 rate limits

        self.stdout.write('\n' + self.style.SUCCESS(
            f'Done — {ok} downloaded,  {failed} failed.'
        ))
