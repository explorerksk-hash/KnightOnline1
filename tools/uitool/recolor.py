"""recolor.py - Klasik KO arayuz dokularini yumusak maskelerle yeniden renklendirir.

Sert esik yerine agirlik (0..1) kullanir: benek/artefakt olusmaz.
Varyantlar: celik, obsidyen, bronz, gumus, altin_cerceve
"""
import numpy as np
from PIL import Image, ImageFilter


def _hsv(im):
    a = np.array(im.split()[3])
    hsv = np.array(im.convert("RGB").convert("HSV"), np.float32) / 255.0
    return hsv[..., 0], hsv[..., 1], hsv[..., 2], a


def _pack(H, S, V, a):
    arr = (np.dstack([H % 1.0, np.clip(S, 0, 1), np.clip(V, 0, 1)]) * 255).astype(np.uint8)
    out = Image.fromarray(arr, "HSV").convert("RGB").convert("RGBA")
    out.putalpha(Image.fromarray(a))
    return out


def _band(x, lo, hi, soft=0.06):
    """lo..hi araliginda 1, kenarlarda yumusak inis."""
    return np.clip((x - (lo - soft)) / soft, 0, 1) * np.clip(((hi + soft) - x) / soft, 0, 1)


def _smooth(w, r=1.6):
    """Maskeyi bulaniklastirir: piksel piksel benek/gurultu olusmaz."""
    from PIL import Image, ImageFilter
    im = Image.fromarray((np.clip(w, 0, 1) * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(r))
    return np.asarray(im, np.float32) / 255.0


def variant(name):
    def f(im):
        H, S, V, a = _hsv(im)
        # bej/kemik/kahve metal cerceve: sicak hue, orta doygunluk, orta-yuksek parlaklik
        w_frame = _band(H, 0.03, 0.17, 0.03) * _band(S, 0.06, 0.60, 0.08) * np.clip((V - 0.12) / 0.15, 0, 1)
        # gri metal butonlar
        w_grey = np.clip((0.10 - S) / 0.06, 0, 1) * _band(V, 0.22, 0.92, 0.08)
        w_frame, w_grey = _smooth(w_frame), _smooth(w_grey)
        if name == "celik":                        # koyu celik govde, altin kenar vurgusu
            H = H * (1 - w_frame) + 0.60 * w_frame
            S = S * (1 - 0.45 * w_frame)
            V = V * (1 - 0.38 * w_frame)
        elif name == "obsidyen":                   # neredeyse siyah, cok koyu
            H = H * (1 - w_frame) + 0.62 * w_frame
            S = S * (1 - 0.65 * w_frame)
            V = V * (1 - 0.58 * w_frame)
            V = V * (1 - 0.35 * w_grey)
        elif name == "bronz":                      # sicak bronz, KO'ya yakin ama derin
            H = H * (1 - w_frame) + 0.085 * w_frame
            S = S * (1 - w_frame) + np.clip(S * 1.5, 0, 0.75) * w_frame
            V = V * (1 - 0.28 * w_frame)
        elif name == "gumus":                      # soguk gumus/gri
            S = S * (1 - 0.85 * w_frame)
            V = V * (1 - 0.18 * w_frame)
        elif name == "altin":                      # zengin altin cerceve
            H = H * (1 - w_frame) + 0.115 * w_frame
            S = S * (1 - w_frame) + np.clip(S * 1.8, 0, 0.85) * w_frame
            V = V * (1 - 0.10 * w_frame)
        return _pack(H, S, V, a)
    return f


def hd(im, sharp=38):
    w, h = im.size
    up = im.resize((w * 2, h * 2), Image.LANCZOS)
    rgb = up.convert("RGB").filter(ImageFilter.UnsharpMask(radius=1.1, percent=sharp, threshold=3))
    out = rgb.convert("RGBA")
    out.putalpha(up.split()[3])
    return out


def make(name, hd_pass=True):
    v = variant(name)
    return (lambda im: hd(v(im))) if hd_pass else v


def bars(im, size=512):
    """Statebar dokusundaki HP satirini kirmiziya, EXP satirini altina ceker (login ile uyum)."""
    import numpy as np
    from PIL import Image
    if im.size != (size, size):
        return im
    H, S, V, a = _hsv(im)
    rows = np.arange(im.size[1])[:, None] * np.ones((1, im.size[0]))
    def band(v0, v1):
        return (rows >= v0 * size - 1) & (rows <= v1 * size + 1)
    hp = band(0.7676, 0.7930) | band(0.6992, 0.7246)   # HP + HP_drop
    ex = band(0.7246, 0.7500)                          # EXP
    H = np.where(hp, 0.995, H); S = np.where(hp, np.clip(S * 1.15, 0, 0.95), S)
    H = np.where(ex, 0.118, H); S = np.where(ex, np.clip(S * 1.1, 0, 0.9), S)
    return _pack(H, S, V, a)


def make2(name, bar_fix=True, hd_pass=True):
    v = variant(name) if name else (lambda x: x)
    def f(im):
        out = v(im)
        if bar_fix:
            out = bars(out)
        return hd(out) if hd_pass else out
    return f
