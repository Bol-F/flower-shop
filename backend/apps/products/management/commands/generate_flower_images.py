"""
Management command: python manage.py generate_flower_images
Generates stylized WebP flower images using Pillow and links them to products.
Safe to re-run — overwrites existing generated images.
"""
import math
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from PIL import Image, ImageDraw, ImageFilter

SIZE = 600


# ── Drawing helpers ────────────────────────────────────────────────────────────

def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    return tuple(int(lerp(c1[i], c2[i], max(0.0, min(1.0, t)))) for i in range(3))


def radial_bg(draw, cx, cy, radius, inner, outer):
    """Paint a soft radial gradient background."""
    for r in range(radius, 0, -2):
        t = r / radius
        color = lerp_color(inner, outer, t)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)


def petal_polygon(cx, cy, angle_rad, length, width, curve=0.18):
    """Return (x,y) list forming a smooth petal polygon."""
    pts_right, pts_left = [], []
    steps = 28
    for i in range(steps + 1):
        t = i / steps
        profile = math.sin(math.pi * t) * (1 + curve * math.sin(2 * math.pi * t))
        r = width * profile
        d = length * t
        bx = cx + d * math.cos(angle_rad)
        by = cy + d * math.sin(angle_rad)
        pts_right.append((bx - r * math.sin(angle_rad), by + r * math.cos(angle_rad)))
        pts_left.append((bx + r * math.sin(angle_rad), by - r * math.cos(angle_rad)))
    return pts_right + list(reversed(pts_left))


def draw_petals(draw, cx, cy, n, length, width, color_tip, color_base, offset_deg=0):
    for i in range(n):
        angle = math.radians(360 / n * i + offset_deg)
        base = lerp_color(color_base, color_tip, 0.2)
        pts = petal_polygon(cx, cy, angle, length, width)
        if pts:
            draw.polygon(pts, fill=base)
        # Highlight layer (narrower, lighter)
        hi_pts = petal_polygon(cx, cy, angle, length * 0.85, width * 0.45)
        hi_color = lerp_color(color_tip, (255, 255, 255), 0.3)
        if hi_pts:
            draw.polygon(hi_pts, fill=hi_color)


def draw_center(draw, cx, cy, radius, inner, outer):
    for r in range(radius, 0, -1):
        t = r / radius
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=lerp_color(inner, outer, t))


def make_flower(
    bg=(255, 245, 250),
    bg_edge=(230, 215, 225),
    petal_tip=(220, 20, 60),
    petal_base=(180, 10, 40),
    center_inner=(255, 200, 0),
    center_outer=(180, 100, 0),
    n_petals=8,
    petal_length=185,
    petal_width=62,
    center_radius=52,
    second_layer=False,
    second_color=None,
    second_offset=22,
):
    img = Image.new('RGB', (SIZE, SIZE), bg)
    draw = ImageDraw.Draw(img)
    cx = cy = SIZE // 2

    radial_bg(draw, cx, cy, SIZE // 2 - 4, bg, bg_edge)

    if second_layer and second_color:
        sc1, sc2 = second_color
        draw_petals(draw, cx, cy, n_petals, petal_length * 0.92, petal_width * 0.70,
                    sc1, sc2, offset_deg=second_offset)

    draw_petals(draw, cx, cy, n_petals, petal_length, petal_width, petal_tip, petal_base)
    draw_center(draw, cx, cy, center_radius, center_inner, center_outer)

    img = img.filter(ImageFilter.GaussianBlur(radius=1.2))
    enhancer_color = __import__('PIL.ImageEnhance', fromlist=['Color']).Color(img)
    img = enhancer_color.enhance(1.3)
    return img


def make_sunflower():
    """Specialised sunflower with many thin yellow rays and a large brown disc."""
    img = Image.new('RGB', (SIZE, SIZE), (255, 252, 225))
    draw = ImageDraw.Draw(img)
    cx = cy = SIZE // 2

    radial_bg(draw, cx, cy, SIZE // 2 - 4, (255, 252, 225), (235, 220, 180))

    # Ray petals (16 long, thin)
    draw_petals(draw, cx, cy, 16, 205, 48,
                (255, 200, 0), (220, 140, 0), offset_deg=0)
    # Inner layer (offset 11°)
    draw_petals(draw, cx, cy, 16, 165, 36,
                (255, 215, 30), (230, 160, 10), offset_deg=11)

    # Brown disc
    draw_center(draw, cx, cy, 72, (90, 50, 10), (50, 25, 5))
    # Disc texture dots
    for dx in range(-40, 41, 14):
        for dy in range(-40, 41, 14):
            if dx * dx + dy * dy < 1600:
                draw.ellipse([cx + dx - 4, cy + dy - 4, cx + dx + 4, cy + dy + 4],
                             fill=(110, 65, 15))

    img = img.filter(ImageFilter.GaussianBlur(radius=1.0))
    return img


def make_orchid():
    """Flat-faced orchid with 5 rounded petals and a contrasting lip."""
    img = Image.new('RGB', (SIZE, SIZE), (245, 240, 255))
    draw = ImageDraw.Draw(img)
    cx = cy = SIZE // 2

    radial_bg(draw, cx, cy, SIZE // 2 - 4, (245, 240, 255), (215, 200, 240))

    # 5 wide flat petals
    draw_petals(draw, cx, cy, 5, 190, 82,
                (160, 100, 220), (100, 50, 180), offset_deg=90)

    # Lip / labellum (white with purple streaks — drawn as a wider short petal)
    lip = petal_polygon(cx, cy, math.radians(270), 120, 90)
    if lip:
        draw.polygon(lip, fill=(245, 230, 255))
    # Lip detail streaks
    for offset in (-18, 0, 18):
        streak = petal_polygon(cx, cy + 10, math.radians(270), 80, 12)
        if streak:
            draw.polygon(streak, fill=(140, 60, 200))

    draw_center(draw, cx, cy, 30, (255, 220, 50), (200, 150, 20))

    img = img.filter(ImageFilter.GaussianBlur(radius=1.1))
    return img


def make_bird_of_paradise():
    """Tropical: bold orange 'beak' petals emerging from a blue spathe."""
    img = Image.new('RGB', (SIZE, SIZE), (240, 255, 245))
    draw = ImageDraw.Draw(img)
    cx = cy = SIZE // 2

    radial_bg(draw, cx, cy, SIZE // 2 - 4, (240, 255, 245), (190, 235, 210))

    # Blue-purple bract (large flat shape)
    bract = petal_polygon(cx, cy, math.radians(250), 200, 70)
    if bract:
        draw.polygon(bract, fill=(60, 40, 160))

    # Orange petals shooting upward
    for angle_deg, col in [(70, (255, 120, 0)), (90, (255, 80, 0)), (110, (255, 150, 0))]:
        pts = petal_polygon(cx, cy, math.radians(angle_deg), 195, 40)
        if pts:
            draw.polygon(pts, fill=col)

    # Teal accent
    acc = petal_polygon(cx, cy, math.radians(82), 160, 22)
    if acc:
        draw.polygon(acc, fill=(0, 170, 160))

    draw_center(draw, cx, cy, 22, (255, 230, 50), (200, 130, 0))

    img = img.filter(ImageFilter.GaussianBlur(radius=1.2))
    return img


def make_protea():
    """King Protea: layered stiff bracts radiating outward, dusty pink."""
    img = Image.new('RGB', (SIZE, SIZE), (255, 248, 245))
    draw = ImageDraw.Draw(img)
    cx = cy = SIZE // 2

    radial_bg(draw, cx, cy, SIZE // 2 - 4, (255, 248, 245), (235, 215, 210))

    # Three layers of bracts getting longer
    for layer_len, layer_w, layer_col, layer_n, off in [
        (120, 28, (200, 155, 145), 20, 0),
        (160, 32, (220, 170, 160), 18, 10),
        (195, 36, (235, 190, 178), 16, 20),
    ]:
        draw_petals(draw, cx, cy, layer_n, layer_len, layer_w,
                    layer_col, lerp_color(layer_col, (150, 80, 70), 0.4), offset_deg=off)

    # Fluffy white centre tuft
    for _ in range(60):
        import random
        random.seed(_ * 7)
        rx = cx + random.randint(-30, 30)
        ry = cy + random.randint(-30, 30)
        draw.ellipse([rx - 5, ry - 5, rx + 5, ry + 5], fill=(250, 245, 240))

    img = img.filter(ImageFilter.GaussianBlur(radius=1.3))
    return img


# ── Flower specs ───────────────────────────────────────────────────────────────

FLOWER_SPECS = {
    # Roses
    'crimson-velvet-rose': lambda: make_flower(
        bg=(255, 240, 245), bg_edge=(220, 190, 200),
        petal_tip=(180, 10, 35), petal_base=(120, 5, 20),
        center_inner=(255, 200, 50), center_outer=(200, 120, 0),
        n_petals=12, petal_length=170, petal_width=58, center_radius=44,
        second_layer=True, second_color=((200, 15, 40), (140, 8, 25)), second_offset=15,
    ),
    'champagne-garden-rose': lambda: make_flower(
        bg=(255, 252, 248), bg_edge=(230, 215, 200),
        petal_tip=(245, 215, 185), petal_base=(210, 170, 140),
        center_inner=(255, 230, 180), center_outer=(200, 160, 100),
        n_petals=14, petal_length=162, petal_width=60, center_radius=40,
        second_layer=True, second_color=((235, 205, 175), (195, 158, 128)), second_offset=13,
    ),
    'midnight-blue-rose': lambda: make_flower(
        bg=(230, 225, 248), bg_edge=(180, 170, 220),
        petal_tip=(70, 30, 160), petal_base=(40, 10, 110),
        center_inner=(200, 160, 255), center_outer=(100, 60, 180),
        n_petals=12, petal_length=168, petal_width=58, center_radius=44,
        second_layer=True, second_color=((90, 40, 180), (50, 15, 120)), second_offset=15,
    ),
    'pink-whisper-spray-rose': lambda: make_flower(
        bg=(255, 245, 250), bg_edge=(240, 210, 225),
        petal_tip=(255, 182, 193), petal_base=(230, 140, 160),
        center_inner=(255, 220, 230), center_outer=(220, 150, 170),
        n_petals=10, petal_length=148, petal_width=52, center_radius=36,
    ),
    'eternal-white-rose': lambda: make_flower(
        bg=(250, 250, 252), bg_edge=(220, 220, 230),
        petal_tip=(248, 248, 250), petal_base=(210, 210, 220),
        center_inner=(255, 250, 240), center_outer=(200, 195, 210),
        n_petals=14, petal_length=165, petal_width=58, center_radius=40,
        second_layer=True, second_color=((238, 238, 245), (200, 200, 215)), second_offset=13,
    ),
    # Tulips
    'parrot-tulip-fiesta': lambda: make_flower(
        bg=(255, 248, 235), bg_edge=(235, 215, 185),
        petal_tip=(220, 60, 20), petal_base=(180, 130, 0),
        center_inner=(255, 230, 50), center_outer=(200, 160, 0),
        n_petals=6, petal_length=195, petal_width=78, center_radius=40,
        second_layer=True, second_color=((100, 180, 40), (60, 130, 20)), second_offset=30,
    ),
    'double-dutch-peach-tulip': lambda: make_flower(
        bg=(255, 245, 235), bg_edge=(235, 210, 185),
        petal_tip=(255, 160, 100), petal_base=(220, 110, 60),
        center_inner=(255, 210, 150), center_outer=(210, 140, 80),
        n_petals=6, petal_length=190, petal_width=80, center_radius=42,
        second_layer=True, second_color=((245, 150, 90), (210, 100, 50)), second_offset=30,
    ),
    'queen-of-night-tulip': lambda: make_flower(
        bg=(235, 225, 240), bg_edge=(190, 175, 205),
        petal_tip=(55, 15, 55), petal_base=(30, 5, 30),
        center_inner=(110, 40, 80), center_outer=(60, 15, 40),
        n_petals=6, petal_length=195, petal_width=80, center_radius=42,
    ),
    'rainbow-spring-mix': lambda: make_flower(
        bg=(250, 248, 255), bg_edge=(220, 210, 240),
        petal_tip=(255, 100, 150), petal_base=(180, 50, 200),
        center_inner=(255, 230, 50), center_outer=(200, 160, 0),
        n_petals=10, petal_length=165, petal_width=56, center_radius=40,
        second_layer=True, second_color=((100, 180, 255), (50, 100, 220)), second_offset=18,
    ),
    # Sunflowers
    'giant-helianthus': make_sunflower,
    'teddy-bear-sunflower': lambda: make_flower(
        bg=(255, 252, 220), bg_edge=(235, 220, 170),
        petal_tip=(255, 195, 0), petal_base=(220, 145, 0),
        center_inner=(110, 65, 15), center_outer=(60, 30, 5),
        n_petals=18, petal_length=145, petal_width=52, center_radius=68,
        second_layer=True, second_color=((245, 185, 10), (210, 135, 0)), second_offset=10,
    ),
    'autumn-rust-sunflower': lambda: make_flower(
        bg=(255, 245, 230), bg_edge=(235, 210, 175),
        petal_tip=(195, 70, 20), petal_base=(140, 40, 5),
        center_inner=(70, 35, 5), center_outer=(40, 15, 0),
        n_petals=14, petal_length=180, petal_width=58, center_radius=55,
        second_layer=True, second_color=((215, 90, 30), (160, 55, 10)), second_offset=13,
    ),
    # Exotic
    'bird-of-paradise': make_bird_of_paradise,
    'purple-vanda-orchid': make_orchid,
    'king-protea': make_protea,
    'red-anthurium': lambda: make_flower(
        bg=(255, 240, 240), bg_edge=(235, 200, 200),
        petal_tip=(200, 10, 20), petal_base=(150, 5, 10),
        center_inner=(255, 230, 50), center_outer=(210, 170, 0),
        n_petals=1, petal_length=210, petal_width=140, center_radius=18,
    ),
    'heliconia-lobster-claw': lambda: make_flower(
        bg=(235, 255, 240), bg_edge=(185, 230, 200),
        petal_tip=(220, 30, 30), petal_base=(160, 15, 15),
        center_inner=(255, 220, 0), center_outer=(200, 160, 0),
        n_petals=5, petal_length=200, petal_width=55, center_radius=30,
        second_layer=True, second_color=((255, 200, 0), (210, 150, 0)), second_offset=36,
    ),
    # Seasonal
    'cherry-blossom-branch': lambda: make_flower(
        bg=(255, 248, 252), bg_edge=(245, 220, 235),
        petal_tip=(255, 192, 210), petal_base=(235, 155, 180),
        center_inner=(255, 220, 230), center_outer=(230, 160, 180),
        n_petals=5, petal_length=170, petal_width=72, center_radius=30,
    ),
    'lavender-dreams-bundle': lambda: make_flower(
        bg=(245, 240, 255), bg_edge=(210, 195, 240),
        petal_tip=(155, 100, 200), petal_base=(110, 60, 160),
        center_inner=(220, 200, 255), center_outer=(160, 120, 210),
        n_petals=20, petal_length=135, petal_width=30, center_radius=28,
    ),
    'blush-peony-cloud': lambda: make_flower(
        bg=(255, 245, 250), bg_edge=(245, 215, 230),
        petal_tip=(255, 190, 210), petal_base=(230, 145, 170),
        center_inner=(255, 225, 235), center_outer=(225, 165, 185),
        n_petals=16, petal_length=168, petal_width=66, center_radius=50,
        second_layer=True, second_color=((245, 175, 200), (220, 130, 160)), second_offset=11,
    ),
    'ranunculus-sunrise': lambda: make_flower(
        bg=(255, 248, 240), bg_edge=(240, 215, 185),
        petal_tip=(255, 155, 80), petal_base=(225, 100, 40),
        center_inner=(255, 225, 100), center_outer=(210, 160, 30),
        n_petals=18, petal_length=155, petal_width=54, center_radius=40,
        second_layer=True, second_color=((245, 140, 65), (215, 90, 30)), second_offset=10,
    ),
    # Bouquets
    'romance-in-red': lambda: make_flower(
        bg=(255, 235, 240), bg_edge=(230, 190, 205),
        petal_tip=(190, 15, 30), petal_base=(130, 5, 15),
        center_inner=(255, 200, 50), center_outer=(195, 120, 0),
        n_petals=12, petal_length=172, petal_width=60, center_radius=46,
        second_layer=True, second_color=((240, 240, 250), (200, 200, 220)), second_offset=15,
    ),
    'garden-sunshine-bouquet': lambda: make_flower(
        bg=(255, 252, 220), bg_edge=(235, 220, 170),
        petal_tip=(255, 200, 0), petal_base=(210, 140, 0),
        center_inner=(80, 45, 5), center_outer=(45, 20, 0),
        n_petals=14, petal_length=180, petal_width=58, center_radius=56,
        second_layer=True, second_color=((100, 190, 60), (60, 140, 30)), second_offset=13,
    ),
    'pastel-paradise': lambda: make_flower(
        bg=(252, 248, 255), bg_edge=(230, 215, 248),
        petal_tip=(255, 195, 215), petal_base=(200, 150, 220),
        center_inner=(255, 230, 200), center_outer=(210, 170, 140),
        n_petals=10, petal_length=165, petal_width=62, center_radius=44,
        second_layer=True, second_color=((200, 235, 255), (150, 190, 240)), second_offset=18,
    ),
    'eternal-love-premium': lambda: make_flower(
        bg=(245, 238, 255), bg_edge=(210, 190, 240),
        petal_tip=(160, 20, 100), petal_base=(100, 10, 60),
        center_inner=(255, 210, 50), center_outer=(200, 140, 0),
        n_petals=12, petal_length=178, petal_width=62, center_radius=48,
        second_layer=True, second_color=((255, 240, 245), (230, 200, 220)), second_offset=15,
    ),
    # Wildflowers
    'blue-cornflower-bundle': lambda: make_flower(
        bg=(235, 245, 255), bg_edge=(190, 215, 245),
        petal_tip=(60, 100, 220), petal_base=(30, 60, 180),
        center_inner=(50, 80, 200), center_outer=(20, 40, 140),
        n_petals=14, petal_length=155, petal_width=38, center_radius=32,
    ),
    'dried-pampas-plume': lambda: make_flower(
        bg=(252, 248, 240), bg_edge=(230, 218, 195),
        petal_tip=(235, 220, 195), petal_base=(195, 175, 148),
        center_inner=(210, 190, 160), center_outer=(165, 140, 110),
        n_petals=22, petal_length=195, petal_width=28, center_radius=24,
    ),
    'meadow-magic-mix': lambda: make_flower(
        bg=(240, 252, 238), bg_edge=(195, 230, 188),
        petal_tip=(180, 210, 90), petal_base=(120, 170, 40),
        center_inner=(255, 225, 50), center_outer=(200, 160, 10),
        n_petals=8, petal_length=162, petal_width=58, center_radius=38,
        second_layer=True, second_color=((255, 150, 80), (210, 100, 30)), second_offset=22,
    ),
}


class Command(BaseCommand):
    help = 'Generate WebP flower images and attach them to products'

    def handle(self, *args, **options):
        from apps.products.models import Product

        dest_dir = os.path.join(settings.MEDIA_ROOT, 'products')
        os.makedirs(dest_dir, exist_ok=True)

        self.stdout.write(self.style.MIGRATE_HEADING('Generating flower images…'))

        generated = 0
        not_found = 0

        for slug, generator in FLOWER_SPECS.items():
            try:
                product = Product.objects.get(slug=slug)
            except Product.DoesNotExist:
                self.stdout.write(f'  No product with slug "{slug}" — skip')
                not_found += 1
                continue

            filename = f'{slug}.webp'
            filepath = os.path.join(dest_dir, filename)

            img = generator()
            img.save(filepath, 'WEBP', quality=88)

            product.image = f'products/{filename}'
            product.save(update_fields=['image'])
            generated += 1
            self.stdout.write(f'  {product.name} → {self.style.SUCCESS("OK")}')

        self.stdout.write(
            self.style.SUCCESS(
                f'\nDone. {generated} images generated, {not_found} slugs not found.'
            )
        )
