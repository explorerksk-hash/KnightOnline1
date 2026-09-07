"""UI dokularini 2x buyuten filtre: Lanczos + hafif keskinlestirme.
   Alfa kanali ayri islenir ki kenarlarda halo olusmasin."""
from PIL import Image, ImageFilter


def x2(im):
    if im is None:
        return None
    w, h = im.size
    rgb = im.convert('RGBA')
    big = rgb.resize((w * 2, h * 2), Image.LANCZOS)
    r, g, b, a = big.split()
    rgbi = Image.merge('RGB', (r, g, b)).filter(
        ImageFilter.UnsharpMask(radius=1.2, percent=55, threshold=2))
    r, g, b = rgbi.split()
    return Image.merge('RGBA', (r, g, b, a))
