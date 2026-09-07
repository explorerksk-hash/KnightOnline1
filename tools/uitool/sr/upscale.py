"""Real-ESRGAN (anime 6B) ile RGBA ikon/doku buyutme.

RGB ve ALFA ayri gecirilir:
  - Saydam bolgelerdeki renk cogu ikonda siyahtir; dogrudan buyutulurse kenarlarda
    koyu hale olusur. Once alfaya gore renk "yayilir" (edge bleed), sonra buyutulur.
  - Alfa 3 kanala kopyalanip ayni agdan gecirilir; kenarlar boylece keskin kalir.
"""
import sys, os
import numpy as np
import torch
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rrdbnet import RRDBNet

_model = None


def model(weights='/tmp/realesrgan.pth'):
    global _model
    if _model is None:
        sd = torch.load(weights, map_location='cpu', weights_only=True)
        sd = sd.get('params_ema', sd.get('params', sd))
        m = RRDBNet(nb=6)
        m.load_state_dict(sd)
        m.eval()
        torch.set_num_threads(os.cpu_count() or 4)
        _model = m
    return _model


def _bleed(rgb, a, iters=6):
    """Saydam piksellere komsu opak renkleri yay (kenar halosunu onler)."""
    rgb = rgb.astype(np.float32).copy()
    w = (a > 8).astype(np.float32)
    for _ in range(iters):
        if w.min() > 0.5:
            break
        num = np.zeros_like(rgb)
        den = np.zeros_like(w)
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            sr = np.roll(np.roll(rgb, dy, 0), dx, 1)
            sw = np.roll(np.roll(w, dy, 0), dx, 1)
            num += sr * sw[..., None]
            den += sw
        fill = den > 0
        new_w = np.clip(w + fill, 0, 1)
        upd = (w < 0.5) & fill
        rgb[upd] = (num[upd] / den[upd][..., None])
        w = new_w
    return np.clip(rgb, 0, 255).astype(np.uint8)


@torch.no_grad()
def _run(arr_u8):
    """arr_u8: HxWx3 uint8 -> 4x buyutulmus HxWx3 uint8"""
    x = torch.from_numpy(arr_u8).float().div_(255).permute(2, 0, 1).unsqueeze(0)
    y = model()(x).clamp_(0, 1)
    return (y.squeeze(0).permute(1, 2, 0).numpy() * 255).round().astype(np.uint8)


def upscale_rgba(im, factor=4):
    """PIL RGBA -> factor kat buyutulmus PIL RGBA. Model 4x; factor<4 ise sonra kucultulur."""
    im = im.convert('RGBA')
    w, h = im.size
    arr = np.array(im)
    rgb, a = arr[..., :3], arr[..., 3]

    rgb_out = _run(_bleed(rgb, a))
    a_out = _run(np.repeat(a[..., None], 3, axis=2))[..., 0]

    out = np.dstack([rgb_out, a_out])
    res = Image.fromarray(out, 'RGBA')
    if factor != 4:
        res = res.resize((w * factor, h * factor), Image.LANCZOS)
    return res
