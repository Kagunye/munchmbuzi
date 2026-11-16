"""Redraw the QR code inside the red "Scan me" badge as a crisp, scannable code.

    python tools/make_qr.py                       # links to the menu page
    python tools/make_qr.py https://example.com   # any other link (e.g. an ordering page)

Updates static/img/qr.png and the news post copy in media/news/.
"""
import sys
from pathlib import Path

import qrcode
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
URL = sys.argv[1] if len(sys.argv) > 1 else "https://www.mbuzimunch.com/menu/"
BOX = (94, 91, 210, 207)  # where the code sits inside the 304x305 badge

targets = [ROOT / "static/img/qr.png"] + sorted((ROOT / "media/news").glob("*qr*.png"))
for path in targets:
    badge = Image.open(path).convert("RGBA")
    x0, y0, x1, y1 = BOX
    size = x1 - x0

    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=2)
    qr.add_data(URL)
    qr.make(fit=True)
    code = qr.make_image(fill_color="#111111", back_color="white").convert("RGBA")
    code = code.resize((size, size), Image.NEAREST)

    # white tile with slightly rounded corners, so it reads as a clean sticker on the badge
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1], radius=8, fill=255)
    badge.paste(code, (x0, y0), mask)
    badge.save(path, optimize=True)
    print("updated", path.relative_to(ROOT), "->", URL)
