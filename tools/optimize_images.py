"""Resize and re-compress the site's photos so pages load fast and scroll smoothly.

    python tools/optimize_images.py           # optimise in place
    python tools/optimize_images.py --dry-run # just report

Each folder gets a maximum size matching how big the photos are shown
(with headroom for sharp/retina screens). Files that are already small
enough are left alone, so running it twice does nothing.
"""
import sys
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
DRY = "--dry-run" in sys.argv

# (glob, max long edge in px, JPEG quality)
RULES = [
    ("static/img/*.jpg", 1600, 78),          # hero slides, dish photos, branch photos
    ("static/img/party/*.jpg", 800, 78),     # sliding banner (shown ~500px tall)
    ("static/img/social/*.jpg", 900, 78),    # Instagram grid / strips
    ("static/img/reels/*.jpg", 720, 76),     # video posters
    ("static/img/art/*.jpg", 1100, 82),      # framed artworks
    ("media/dishes/*.jpg", 900, 78),         # menu circles, dish grid, drinks row
    ("media/branches/*.jpg", 1400, 78),      # branch photos
    ("media/branches/video/*.jpg", 720, 76), # branch reel posters
    ("media/news/*.jpg", 1400, 80),          # news photos
]

total_before = total_after = 0
for pattern, max_edge, quality in RULES:
    for path in sorted(ROOT.glob(pattern)):
        before = path.stat().st_size
        im = Image.open(path)
        im = ImageOps.exif_transpose(im).convert("RGB")
        w, h = im.size
        needs_resize = max(w, h) > max_edge
        if needs_resize:
            im.thumbnail((max_edge, max_edge), Image.LANCZOS)
        # only rewrite if it's oversized or clearly under-compressed
        if not needs_resize and before < im.size[0] * im.size[1] * 0.18:
            total_before += before; total_after += before
            continue
        if DRY:
            print(f"would optimise {path.relative_to(ROOT)} {w}x{h} {before // 1024}KB")
            total_before += before; total_after += before
            continue
        tmp = path.with_suffix(".tmp.jpg")
        im.save(tmp, "JPEG", quality=quality, optimize=True, progressive=True)
        after = tmp.stat().st_size
        if after < before:
            tmp.replace(path)
        else:
            tmp.unlink()
            after = before
        total_before += before; total_after += after
        print(f"{path.relative_to(ROOT)}: {w}x{h} -> {im.size[0]}x{im.size[1]}, {before // 1024}KB -> {after // 1024}KB")

print(f"\nTotal: {total_before / 1048576:.1f}MB -> {total_after / 1048576:.1f}MB")
