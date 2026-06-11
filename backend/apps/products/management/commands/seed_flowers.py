"""
Management command: python manage.py seed_flowers
Seeds the database with sample categories and flower products.
Safe to re-run — skips records that already exist by name.
"""
from django.core.management.base import BaseCommand
from apps.categories.models import Category
from apps.products.models import Product


CATEGORIES = [
    {
        'name': 'Roses',
        'description': 'Timeless classics. From velvety reds to blush garden varieties, roses are the language of love.',
    },
    {
        'name': 'Tulips',
        'description': 'Bold, cheerful, and available in every colour of the rainbow. A spring favourite.',
    },
    {
        'name': 'Sunflowers',
        'description': 'Bright, warm, and joyful. Sunflowers bring instant happiness to any room.',
    },
    {
        'name': 'Exotic & Tropical',
        'description': 'Rare blooms from the tropics. Bold shapes and electric colours that command attention.',
    },
    {
        'name': 'Seasonal Picks',
        'description': 'Hand-selected fresh-from-the-field blooms that celebrate each season at its peak.',
    },
    {
        'name': 'Bouquets & Arrangements',
        'description': 'Expertly composed arrangements ready to gift. No wrapping needed — just joy.',
    },
    {
        'name': 'Wildflowers',
        'description': 'Effortlessly natural. Untamed beauty plucked straight from meadows and fields.',
    },
]


PRODUCTS = [
    # ── Roses ─────────────────────────────────────────────────────────────────
    {
        'name': 'Crimson Velvet Rose',
        'category': 'Roses',
        'description': (
            'The quintessential rose. Deep scarlet petals with a texture so rich they almost look painted. '
            'Each stem is cut at its peak and conditioned for maximum vase life. '
            'Perfect for anniversaries, Valentine\'s Day, or whenever words fall short.'
        ),
        'price': '24.99',
        'stock': 45,
    },
    {
        'name': 'Champagne Garden Rose',
        'category': 'Roses',
        'description': (
            'Creamy blush tones melt from petal to petal in this lush garden rose. '
            'With a spiral bloom twice the size of a standard rose and a soft honey scent, '
            'it is the premier choice for weddings and elegant table centres.'
        ),
        'price': '29.99',
        'stock': 30,
    },
    {
        'name': 'Midnight Blue Rose',
        'category': 'Roses',
        'description': (
            'An extraordinary rarity. Through careful cultivation, these roses achieve a deep violet-blue '
            'that borders on impossible in nature. Each one is a conversation piece. '
            'Limited stock — they are as fleeting as they are beautiful.'
        ),
        'price': '39.99',
        'stock': 15,
    },
    {
        'name': 'Pink Whisper Spray Rose',
        'category': 'Roses',
        'description': (
            'A single stem bursting with a dozen tiny blush-pink buds, each one a miniature rose in its own right. '
            'Spray roses fill out arrangements with soft cloud-like clusters and last exceptionally long in the vase.'
        ),
        'price': '18.99',
        'stock': 60,
    },
    {
        'name': 'Eternal White Rose',
        'category': 'Roses',
        'description': (
            'A preserved white rose treated to last for months without water. '
            'Presented in a sleek glass dome — a modern take on Beauty and the Beast\'s enchanted rose. '
            'The gift that does not wilt.'
        ),
        'price': '49.99',
        'stock': 20,
    },
    # ── Tulips ────────────────────────────────────────────────────────────────
    {
        'name': 'Parrot Tulip Fiesta',
        'category': 'Tulips',
        'description': (
            'Ruffled, fringed, and gloriously theatrical. Parrot tulips are the rebels of the tulip world — '
            'their twisted petals are streaked with red, orange, yellow, and green all at once. '
            'No two stems are identical.'
        ),
        'price': '22.99',
        'stock': 40,
    },
    {
        'name': 'Double Dutch Peach Tulip',
        'category': 'Tulips',
        'description': (
            'So full they are almost mistaken for peonies. Double Dutch tulips grow layer upon layer of '
            'warm peach petals from a single bud, creating a lush domed bloom. '
            'Grown in the fields of Holland and flown in twice weekly.'
        ),
        'price': '19.99',
        'stock': 55,
    },
    {
        'name': 'Queen of Night Tulip',
        'category': 'Tulips',
        'description': (
            'The darkest tulip in existence. This heritage variety dates to 17th-century Dutch flower markets. '
            'Its petals are a deep mahogany-black with a velvet sheen that catches the light at every angle. '
            'Dramatic and unforgettable.'
        ),
        'price': '26.99',
        'stock': 25,
    },
    {
        'name': 'Rainbow Spring Mix',
        'category': 'Tulips',
        'description': (
            'Ten stems. Ten colours. One spectacular burst of spring. '
            'This curated mix includes reds, corals, purples, yellows, and whites '
            'hand-picked to complement each other perfectly. '
            'The easiest way to fill a room with colour.'
        ),
        'price': '21.99',
        'stock': 70,
    },
    # ── Sunflowers ────────────────────────────────────────────────────────────
    {
        'name': 'Giant Helianthus',
        'category': 'Sunflowers',
        'description': (
            'The original. A face the size of a dinner plate, golden ray petals radiating from a rich brown disc. '
            'These are field-grown, stem-cut at full height, and arrive with the warmth of a summer afternoon '
            'built right in. They simply make people smile.'
        ),
        'price': '16.99',
        'stock': 80,
    },
    {
        'name': 'Teddy Bear Sunflower',
        'category': 'Sunflowers',
        'description': (
            'A dwarf variety with an impossibly fluffy double bloom — more pompom than flower. '
            'The compact golden head sits atop a sturdy short stem and is utterly irresistible. '
            'A favourite for children\'s gifts and cosy kitchen arrangements.'
        ),
        'price': '19.99',
        'stock': 65,
    },
    {
        'name': 'Autumn Rust Sunflower',
        'category': 'Sunflowers',
        'description': (
            'A mood sunflower. The petals shift from deep burnt orange at the tips through coppery rust '
            'to an almost burgundy base. Grown from a heritage heirloom seed, these pair beautifully '
            'with dahlias and dried grasses for a rich autumnal palette.'
        ),
        'price': '18.99',
        'stock': 50,
    },
    # ── Exotic & Tropical ─────────────────────────────────────────────────────
    {
        'name': 'Bird of Paradise',
        'category': 'Exotic & Tropical',
        'description': (
            'Named for the exotic bird it resembles. Vivid orange petals burst from a purple-blue bract '
            'like a crested tropical bird taking flight. '
            'A single stem completely transforms a room. Native to South Africa, grown in Spain.'
        ),
        'price': '44.99',
        'stock': 20,
    },
    {
        'name': 'Purple Vanda Orchid',
        'category': 'Exotic & Tropical',
        'description': (
            'Grown in suspended baskets with no soil, Vanda orchids are among the rarest in cultivation. '
            'This variety\'s blooms are a deep amethyst-violet, flat and perfectly symmetrical, '
            'with a waxy sheen that seems almost artificial. Arrives in a keepsake glass vase.'
        ),
        'price': '54.99',
        'stock': 12,
    },
    {
        'name': 'King Protea',
        'category': 'Exotic & Tropical',
        'description': (
            'South Africa\'s national flower and one of the oldest flowering plants on earth. '
            'The King Protea\'s bowl-shaped bloom can reach 30 cm across, surrounded by a crown '
            'of stiff, pointed bracts in dusty pink and cream. Bold, prehistoric, magnificent.'
        ),
        'price': '38.99',
        'stock': 18,
    },
    {
        'name': 'Red Anthurium',
        'category': 'Exotic & Tropical',
        'description': (
            'A heart-shaped spathe of lacquered cherry-red with a golden spadix arrow at its centre. '
            'Anthuriums last an extraordinary 3–4 weeks in the vase and need almost no care. '
            'They symbolise hospitality and abundance across Central America.'
        ),
        'price': '32.99',
        'stock': 25,
    },
    {
        'name': 'Heliconia Lobster Claw',
        'category': 'Exotic & Tropical',
        'description': (
            'Architectural, electric, theatrical. The Heliconia\'s waxy red-and-yellow bracts stack '
            'like a dragon\'s spine up a metre-long stem. One stem alone is a complete installation. '
            'Beloved by interior designers and anyone who likes their flowers to make a statement.'
        ),
        'price': '42.99',
        'stock': 15,
    },
    # ── Seasonal Picks ────────────────────────────────────────────────────────
    {
        'name': 'Cherry Blossom Branch',
        'category': 'Seasonal Picks',
        'description': (
            'The Japanese symbol of impermanence and fleeting beauty. '
            'Forced-bloom branches loaded with pale pink sakura arrive just as the buds are about to open, '
            'giving you days of watching them unfurl. A meditative, deeply beautiful decoration.'
        ),
        'price': '34.99',
        'stock': 30,
    },
    {
        'name': 'Lavender Dreams Bundle',
        'category': 'Seasonal Picks',
        'description': (
            'Cut fresh from sun-drenched Provençal-style fields, this bundle of 30 fragrant lavender stems '
            'fills an entire room with a calm, herbaceous scent. Hang it to dry and it keeps its fragrance '
            'for months — the decoration that keeps giving.'
        ),
        'price': '27.99',
        'stock': 45,
    },
    {
        'name': 'Blush Peony Cloud',
        'category': 'Seasonal Picks',
        'description': (
            'Available only ten weeks a year. When peonies bloom, the world takes notice. '
            'These blush-pink varieties open into enormous, tissue-layered clouds with a scent '
            'that is equal parts rose, jasmine, and something entirely their own. '
            'Order fast — they sell out every season without exception.'
        ),
        'price': '36.99',
        'stock': 28,
    },
    {
        'name': 'Ranunculus Sunrise',
        'category': 'Seasonal Picks',
        'description': (
            'Hundreds of paper-thin petals stacked into a perfect globe of warm coral and peach. '
            'Ranunculus are the secret weapon of florists — they photograph like no other flower '
            'and open slowly over a week, changing shape and colour as they bloom.'
        ),
        'price': '31.99',
        'stock': 35,
    },
    # ── Bouquets & Arrangements ───────────────────────────────────────────────
    {
        'name': 'Romance in Red',
        'category': 'Bouquets & Arrangements',
        'description': (
            'Twelve Crimson Velvet Roses nestled in a cloud of gypsophila and eucalyptus, '
            'wrapped in black kraft paper with a satin ribbon. '
            'The classic romantic gift, perfected. Includes a blank gift card.'
        ),
        'price': '59.99',
        'stock': 20,
    },
    {
        'name': 'Garden Sunshine Bouquet',
        'category': 'Bouquets & Arrangements',
        'description': (
            'Giant Helianthus sunflowers, electric-yellow gerberas, and feathery eucalyptus — '
            'this arrangement radiates pure warmth. Wrapped in brown craft and sunflower-yellow ribbon. '
            'Impossible to receive without smiling.'
        ),
        'price': '52.99',
        'stock': 18,
    },
    {
        'name': 'Pastel Paradise',
        'category': 'Bouquets & Arrangements',
        'description': (
            'A dreamy cloud of soft colours: Double Dutch peach tulips, Blush Peony Cloud, '
            'white freesias, and lilac waxflower. Soft, romantic, and gender-neutral. '
            'Our most-photographed arrangement on social media three years running.'
        ),
        'price': '64.99',
        'stock': 15,
    },
    {
        'name': 'Eternal Love Premium',
        'category': 'Bouquets & Arrangements',
        'description': (
            'Our showpiece. Long-stem red roses, white oriental lilies, a single Purple Vanda Orchid, '
            'and sprays of ruscus and trailing ivy — composed into an architectural statement arrangement. '
            'Arrives in a signature black-and-gold Bloom & Petal box. For the moments that matter most.'
        ),
        'price': '89.99',
        'stock': 10,
    },
    # ── Wildflowers ───────────────────────────────────────────────────────────
    {
        'name': 'Blue Cornflower Bundle',
        'category': 'Wildflowers',
        'description': (
            'Twenty stems of vivid electric-blue cornflowers — the same flowers that grow along '
            'European country roadsides in summer. Unassuming, honest, and utterly charming. '
            'The antidote to fussy floristry.'
        ),
        'price': '22.99',
        'stock': 50,
    },
    {
        'name': 'Dried Pampas Plume',
        'category': 'Wildflowers',
        'description': (
            'Three feathery ivory pampas plumes, sustainably harvested and naturally dried. '
            'Endlessly on-trend, pampas grass adds movement and texture to any space '
            'and requires zero care. Arrange once, enjoy for years.'
        ),
        'price': '34.99',
        'stock': 35,
    },
    {
        'name': 'Meadow Magic Mix',
        'category': 'Wildflowers',
        'description': (
            'A wild, unstructured mix of whatever is blooming beautifully this week: '
            'anemones, scabiosa, nigella, sweet peas, and whatever else the fields are offering. '
            'No two bunches are the same — every one is a surprise. Truly seasonal, truly local.'
        ),
        'price': '28.99',
        'stock': 42,
    },
]


class Command(BaseCommand):
    help = 'Seed the database with sample flower categories and products'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('Seeding flower shop data…'))

        # ── Categories ────────────────────────────────────────────────────────
        cat_map = {}
        for data in CATEGORIES:
            cat, created = Category.objects.get_or_create(
                name=data['name'],
                defaults={'description': data['description']},
            )
            cat_map[cat.name] = cat
            status = self.style.SUCCESS('created') if created else 'already exists'
            self.stdout.write(f'  Category "{cat.name}" — {status}')

        # ── Products ──────────────────────────────────────────────────────────
        created_count = 0
        for data in PRODUCTS:
            category = cat_map.get(data['category'])
            _, created = Product.objects.get_or_create(
                name=data['name'],
                defaults={
                    'description': data['description'],
                    'price': data['price'],
                    'stock': data['stock'],
                    'category': category,
                    'is_available': True,
                },
            )
            if created:
                created_count += 1
                self.stdout.write(f'  Product "{data["name"]}" — {self.style.SUCCESS("created")}')
            else:
                self.stdout.write(f'  Product "{data["name"]}" — already exists')

        self.stdout.write(
            self.style.SUCCESS(
                f'\nDone. {len(CATEGORIES)} categories, {created_count} new products added.'
            )
        )
