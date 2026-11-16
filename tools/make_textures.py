"""Generate the vintage "white dirt" textures as small PNG tiles.

PNG tiles are far cheaper for browsers to paint than SVG feTurbulence filters.
Run from the project root:  python tools/make_textures.py
Tweak the percentages below to make the wear lighter or heavier.
"""
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter

OUT = Path(__file__).resolve().parent.parent / "static" / "img" / "texture"
OUT.mkdir(parents=True, exist_ok=True)


def tileable(img):
    """Blend the image with its half-offset copy so the tile wraps without seams."""
    w, h = img.size
    shifted = ImageChops.offset(img, w // 2, h // 2)
    mask = Image.radial_gradient("L").resize((w, h))
    return Image.composite(img, shifted, mask)


def cutoff(img, top_percent):
    """Grey value above which the brightest `top_percent` % of pixels sit."""
    hist = img.histogram()
    target = sum(hist) * top_percent / 100
    acc = 0
    for v in range(255, -1, -1):
        acc += hist[v]
        if acc >= target:
            return v
    return 0


def field(size, blur, sigma=90):
    return tileable(Image.effect_noise(size, sigma)).filter(ImageFilter.GaussianBlur(blur))


def specks(size, blur, percent, colour, soft=6):
    n = field((size, size), blur)
    t = cutoff(n, percent)
    alpha = n.point(lambda v: 255 if v >= t else max(0, 255 - (t - v) * (255 // soft)))
    img = Image.new("RGBA", (size, size), colour + (0,))
    img.putalpha(alpha)
    return img


# White dirt: fine specks + a few blotches (like the distressed goat-stamp logo)
dirt = Image.alpha_composite(specks(420, 0.7, 3.5, (255, 255, 255)), specks(420, 2.6, 1.6, (255, 255, 255), soft=4))
dirt.save(OUT / "dirt-white.png", optimize=True)

# Brown dirt for aged paper
specks(420, 1.6, 1.8, (96, 70, 42), soft=4).save(OUT / "dirt-brown.png", optimize=True)

# Film grain: small tile, low alpha, quantised to keep it light
g = Image.effect_noise((160, 160), 70)
grain = Image.new("RGBA", (160, 160), (24, 16, 8, 0))
grain.putalpha(g.point(lambda v: min(255, abs(v - 128) // 3 * 2)))
grain.quantize(64).convert("RGBA").save(OUT / "grain.png", optimize=True)

# Horizontal scratches
s = Image.effect_noise((600, 8), 100).resize((600, 600), Image.BICUBIC)
t = cutoff(s, 2.2)
scr = Image.new("RGBA", (600, 600), (255, 255, 255, 0))
scr.putalpha(s.point(lambda v: 190 if v >= t else 0))
scr.save(OUT / "scratch-white.png", optimize=True)

# Worn-stamp mask (for mask-image): opaque, with ~9% irregular holes
w = field((320, 320), 1.2)
t = cutoff(w, 9)
worn = Image.new("RGBA", (320, 320), (0, 0, 0, 255))
worn.putalpha(w.point(lambda v: 0 if v >= t else min(255, (t - v) * 40)))
worn.save(OUT / "worn.png", optimize=True)

# Film dust: a few light and dark specks plus short hair-like fibres
import random

random.seed(7)
from PIL import ImageDraw

dust = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
d = ImageDraw.Draw(dust)
for _ in range(140):
    x, y = random.randrange(512), random.randrange(512)
    r = random.choice([0.6, 0.8, 1, 1.2, 1.6, 2.2])
    light = random.random() < 0.6
    col = (255, 248, 230, random.randint(120, 220)) if light else (20, 12, 6, random.randint(110, 200))
    d.ellipse([x - r, y - r, x + r, y + r], fill=col)
for _ in range(9):  # fibres
    x, y = random.randrange(512), random.randrange(512)
    pts = [(x, y)]
    for _ in range(random.randint(3, 6)):
        x += random.randint(-9, 9); y += random.randint(-9, 9); pts.append((x, y))
    d.line(pts, fill=(255, 248, 230, 150) if random.random() < 0.5 else (20, 12, 6, 140), width=1)
dust.save(OUT / "dust.png", optimize=True)

# Vertical film scratches (sparse, varying strength)
sv = Image.new("RGBA", (640, 400), (0, 0, 0, 0))
d = ImageDraw.Draw(sv)
for _ in range(7):
    x = random.randrange(640)
    top, bottom = random.randrange(0, 120), random.randrange(260, 400)
    a = random.randint(60, 150)
    d.line([(x, top), (x + random.randint(-3, 3), bottom)], fill=(255, 250, 235, a), width=1)
for _ in range(2):
    x = random.randrange(640)
    d.line([(x, 0), (x + random.randint(-2, 2), 400)], fill=(30, 18, 8, 90), width=1)
sv.save(OUT / "scratch-v.png", optimize=True)

for f in sorted(OUT.glob("*.png")):
    a = Image.open(f).getchannel("A")
    h = a.histogram()
    print(f"{f.name:20} {f.stat().st_size // 1024:>3} KB  visible {100 * sum(h[1:]) / sum(h):5.1f}%")
