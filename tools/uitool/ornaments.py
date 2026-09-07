"""ornaments.py - Klasik KO arayuzunun uzerine eklenecek altin suslemeler (prosedurel cizim).

Uretilenler bir atlas'a paketlenir; .uif'e UIImage olarak eklenir.
Parcalar: kose filigrani, ulus madalyonu, rune serit, civi, altin cizgi, cubuk ucu parlamasi.
"""
import math
from PIL import Image, ImageDraw, ImageFilter

GOLD = (201, 162, 39)
GOLD_HI = (232, 198, 84)
GOLD_LO = (140, 110, 26)
RED = (176, 46, 38)
S = 4  # supersample


def _new(w, h):
    return Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))


def _fin(img, w, h):
    return img.resize((w, h), Image.LANCZOS)


def corner(w=56, h=56, flip_x=False, flip_y=False):
    """Kose filigrani: kivrilan altin sarmal + damla."""
    im = _new(w, h); d = ImageDraw.Draw(im)
    W, H = w * S, h * S
    lw = max(2, int(1.7 * S))
    # dis hat
    d.line([(3 * S, 3 * S), (W - 6 * S, 3 * S)], fill=GOLD + (240,), width=lw)
    d.line([(3 * S, 3 * S), (3 * S, H - 6 * S)], fill=GOLD + (240,), width=lw)
    # ic sarmal (kucuk->buyuk yay)
    d.arc((3 * S, 3 * S, 27 * S, 27 * S), 180, 285, fill=GOLD_HI + (255,), width=lw)
    d.arc((9 * S, 9 * S, 41 * S, 41 * S), 182, 268, fill=GOLD + (200,), width=max(1, lw - S // 2))
    d.arc((15 * S, 15 * S, 27 * S, 27 * S), 200, 360, fill=GOLD_HI + (230,), width=max(1, lw - S // 2))
    # damla ucu
    d.polygon([(30 * S, 4 * S), (40 * S, 3 * S), (34 * S, 11 * S)], fill=GOLD + (215,))
    d.polygon([(4 * S, 30 * S), (3 * S, 40 * S), (11 * S, 34 * S)], fill=GOLD + (215,))
    d.ellipse((4 * S, 4 * S, 12 * S, 12 * S), fill=GOLD_HI + (255,))
    out = _fin(im, w, h)
    if flip_x: out = out.transpose(Image.FLIP_LEFT_RIGHT)
    if flip_y: out = out.transpose(Image.FLIP_TOP_BOTTOM)
    return out


def medallion(kind="karus", size=64):
    """Ulus madalyonu: altin halka + ulus sembolu."""
    im = _new(size, size); d = ImageDraw.Draw(im)
    W = size * S
    d.ellipse((2 * S, 2 * S, W - 2 * S, W - 2 * S), fill=(18, 19, 24, 235), outline=GOLD + (255,), width=int(2.2 * S))
    d.ellipse((6 * S, 6 * S, W - 6 * S, W - 6 * S), outline=GOLD_LO + (200,), width=max(1, S // 2))
    for i in range(12):  # cevre civileri
        a = i * math.pi / 6
        cx, cy = W / 2 + math.cos(a) * (W / 2 - 4 * S), W / 2 + math.sin(a) * (W / 2 - 4 * S)
        d.ellipse((cx - S, cy - S, cx + S, cy + S), fill=GOLD_HI + (255,))
    c = W / 2
    if kind == "karus":  # capraz balta + kama
        col = RED + (255,)
        d.line([(c - 14 * S, c + 14 * S), (c + 14 * S, c - 14 * S)], fill=col, width=int(2.4 * S))
        d.line([(c - 14 * S, c - 14 * S), (c + 14 * S, c + 14 * S)], fill=col, width=int(2.4 * S))
        d.ellipse((c - 5 * S, c - 5 * S, c + 5 * S, c + 5 * S), fill=GOLD + (255,))
    else:               # yildiz
        pts = []
        for i in range(10):
            r = (15 if i % 2 == 0 else 7) * S
            a = -math.pi / 2 + i * math.pi / 5
            pts.append((c + math.cos(a) * r, c + math.sin(a) * r))
        d.polygon(pts, fill=GOLD + (255,))
    return _fin(im, size, size)


def runes(w=192, h=14):
    """Kazima rune serit."""
    im = _new(w, h); d = ImageDraw.Draw(im)
    W, H = w * S, h * S
    lw = max(1, int(1.1 * S))
    d.line([(0, H // 2), (W, H // 2)], fill=GOLD_LO + (110,), width=lw)
    step = 16 * S
    for i, x in enumerate(range(step // 2, W - step // 2, step)):
        k = i % 4
        if k == 0:
            d.line([(x, 3 * S), (x, H - 3 * S)], fill=GOLD + (185,), width=lw)
            d.line([(x - 3 * S, 5 * S), (x + 3 * S, 5 * S)], fill=GOLD + (185,), width=lw)
        elif k == 1:
            d.line([(x - 3 * S, 3 * S), (x + 3 * S, H - 3 * S)], fill=GOLD + (185,), width=lw)
            d.line([(x + 3 * S, 3 * S), (x - 3 * S, H - 3 * S)], fill=GOLD + (185,), width=lw)
        elif k == 2:
            d.polygon([(x, 3 * S), (x + 3 * S, H // 2), (x, H - 3 * S), (x - 3 * S, H // 2)],
                      outline=GOLD + (185,), width=lw)
        else:
            d.line([(x, 3 * S), (x, H - 3 * S)], fill=GOLD + (185,), width=lw)
            d.line([(x, H // 2), (x + 4 * S, H // 2 - 3 * S)], fill=GOLD + (185,), width=lw)
    return _fin(im, w, h)


def stud(size=10):
    im = _new(size, size); d = ImageDraw.Draw(im)
    W = size * S
    d.ellipse((0, 0, W, W), fill=GOLD_LO + (255,))
    d.ellipse((int(W * .18), int(W * .18), int(W * .82), int(W * .82)), fill=GOLD + (255,))
    d.ellipse((int(W * .3), int(W * .26), int(W * .55), int(W * .5)), fill=GOLD_HI + (255,))
    return _fin(im, size, size)


def line_h(w=8, h=3):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.line([(0, h // 2), (w, h // 2)], fill=GOLD + (200,))
    return im


def wing(w=110, h=30, flip=False):
    """Kanat/defne dali flourish (baslik altina)."""
    im = _new(w, h); d = ImageDraw.Draw(im)
    W, H = w * S, h * S
    lw = max(2, int(1.4 * S))
    # dal: soldan saga yukselen yay
    pts = [(int(W * t), int(H * (0.86 - 0.62 * t ** 1.5))) for t in [i / 40 for i in range(41)]]
    d.line(pts, fill=GOLD + (225,), width=lw)
    for i in range(7):
        t = 0.10 + i * 0.13
        x = int(W * t); y = int(H * (0.86 - 0.62 * t ** 1.5))
        L = int((10 - i) * 1.5 * S)
        d.polygon([(x, y), (x + L, y - int(L * 0.85)), (x + int(L * 1.25), y - int(L * 0.1)), (x + int(L * 0.3), y + int(L * 0.35))],
                  fill=GOLD + (120 + i * 12,), outline=GOLD_HI + (190,))
    out = _fin(im, w, h)
    return out.transpose(Image.FLIP_LEFT_RIGHT) if flip else out


def bar_cap(w=10, h=16):
    """Cubuk ucu parlamasi."""
    im = _new(w, h); d = ImageDraw.Draw(im)
    W, H = w * S, h * S
    d.polygon([(0, 0), (W, H // 2), (0, H)], fill=GOLD_HI + (230,))
    return _fin(im, w, h).filter(ImageFilter.GaussianBlur(0.6))
