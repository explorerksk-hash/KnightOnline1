"""classic_hd.py - Klasik KO arayuz dokularini 'HD + koyu/altin' yapar.
   hd(im)      : 2x Lanczos + hafif keskinlestirme
   recolor(im) : bej/kemik cerceveleri koyu celige, pembe hover'lari altina ceker; cubuk renklerine dokunmaz
"""
import numpy as np
from PIL import Image, ImageFilter


def hd(im: Image.Image) -> Image.Image:
    w, h = im.size
    up = im.resize((w * 2, h * 2), Image.LANCZOS)
    rgb = up.convert("RGB").filter(ImageFilter.UnsharpMask(radius=1.2, percent=60, threshold=2))
    out = rgb.convert("RGBA")
    out.putalpha(up.split()[3])
    return out


def recolor(im: Image.Image, steel_dark=0.62, steel_sat=0.55, gold_hue=44 / 360, gold_sat=0.62) -> Image.Image:
    hsv = np.array(im.convert("RGBA").convert("RGB").convert("HSV"), np.float32) / 255.0
    a = np.array(im.split()[3])
    H, S, V = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    # bej / kemik / kahverengi metal: sicak ton, dusuk-orta doygunluk
    warm = (H > 15 / 360) & (H < 60 / 360) & (S > 0.08) & (S < 0.55) & (V > 0.18)
    V = np.where(warm, V * steel_dark, V)
    S = np.where(warm, S * steel_sat, S)
    H = np.where(warm, 215 / 360, H)  # hafif mavi-gri celik
    # pembe (hover/basili) butonlar: kirmizimsi, acik
    pink = ((H < 15 / 360) | (H > 330 / 360)) & (S > 0.12) & (S < 0.6) & (V > 0.55)
    H = np.where(pink, gold_hue, H)
    S = np.where(pink, gold_sat, S)
    V = np.where(pink, V * 0.92, V)
    out = Image.fromarray((np.dstack([H, S, V]) * 255).clip(0, 255).astype(np.uint8), "HSV").convert("RGB").convert("RGBA")
    out.putalpha(Image.fromarray(a))
    return out


def hd_recolor(im):
    return hd(recolor(im))
