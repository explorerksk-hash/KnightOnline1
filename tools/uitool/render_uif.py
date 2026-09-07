"""render_uif.py - bir .uif dosyasini, dokularini okuyarak PNG'ye cizer (onizleme).
   python render_uif.py <uif> <client_assets_dir> <out.png> [--scale k] [--tex-filter modul:fonksiyon]
"""
import os, sys
from PIL import Image
from n3ui import UIBase, UIImage, UIButton, UIProgress, UIString, load_dxt, BS_NORMAL

_cache = {}


def get_tex(assets, name, filt=None):
    key = name.lower()
    if key in _cache:
        return _cache[key]
    rel = name.replace("\\", "/")
    p = os.path.join(assets, rel)
    if not os.path.exists(p):
        # buyuk/kucuk harf farkini her yol parcasi icin tolere et (Windows -> Linux)
        cur = assets
        for part in rel.split("/"):
            nxt = os.path.join(cur, part)
            if not os.path.exists(nxt) and os.path.isdir(cur):
                for f in os.listdir(cur):
                    if f.lower() == part.lower():
                        nxt = os.path.join(cur, f); break
            cur = nxt
        p = cur
    im = load_dxt(p) if os.path.exists(p) else None
    if im is not None and filt:
        im = filt(im)
    _cache[key] = im
    return im


def render(root, assets, scale=1.0, filt=None, bg=(36, 40, 34, 255), size=None, offset=(0, 0)):
    W = size[0] if size else int(root.width * scale) + 2
    H = size[1] if size else int(root.height * scale) + 2
    canvas = Image.new("RGBA", (W, H), bg)
    ox, oy = offset

    def draw(n):
        if isinstance(n, UIImage) and n.tex:
            tex = get_tex(assets, n.tex, filt)
            if tex is None:
                return
            u0, v0, u1, v1 = n.uv
            tw, th = tex.size
            box = (round(u0 * tw), round(v0 * th), round(u1 * tw), round(v1 * th))
            if box[2] <= box[0] or box[3] <= box[1]:
                return
            crop = tex.crop(box)
            w, h = max(1, int(n.width * scale)), max(1, int(n.height * scale))
            if crop.size != (w, h):
                crop = crop.resize((w, h), Image.BILINEAR)
            canvas.alpha_composite(crop, (int((n.region[0] - root.region[0]) * scale) + ox,
                                          int((n.region[1] - root.region[1]) * scale) + oy))
        if isinstance(n, UIButton):
            for c in n.children:
                if isinstance(c, UIImage) and c.reserved == BS_NORMAL:
                    draw(c)
            for c in n.children:
                if not isinstance(c, UIImage):
                    draw(c)
            return
        if isinstance(n, UIProgress):
            for want in (0, 1):  # once arka plan (bos), sonra dolgu
                for c in n.children:
                    if isinstance(c, UIImage) and c.reserved == want:
                        draw(c)
            return
        for c in n.children:
            draw(c)

    draw(root)
    return canvas


if __name__ == "__main__":
    uif, assets, out = sys.argv[1:4]
    scale = float(sys.argv[sys.argv.index("--scale") + 1]) if "--scale" in sys.argv else 1.0
    root = UIBase.load(uif)
    render(root, assets, scale).save(out)
    print("yazildi", out, root.region)
