"""Tum skill/item ikonlarini Real-ESRGAN ile 128x128'e buyutur.

Kullanim: python3 batch_icons.py <kaynak_dizin> <hedef_dizin> [limit]

- 32x32 skill ikonu -> 128x128 (model 4x, dogrudan)
- 64x64 item ikonu  -> 128x128 (model 4x = 256, sonra Lanczos ile 128)
Cikti formati A8R8G8B8; .dxt basligindaki orijinal ad korunur.
"""
import os, sys, time, struct

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image
from n3ui import load_dxt, save_dxt, _r_str, D3DFMT_A8R8G8B8
from upscale import upscale_rgba

TARGET = 128


def orig_name(path):
    with open(path, "rb") as f:
        return _r_str(f)


def main():
    src, dst = sys.argv[1], sys.argv[2]
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    os.makedirs(dst, exist_ok=True)

    files = sorted(f for f in os.listdir(src) if f.lower().endswith(".dxt"))
    if limit:
        files = files[:limit]

    t0 = time.time()
    done = skipped = 0
    for i, fn in enumerate(files, 1):
        sp = os.path.join(src, fn)
        dp = os.path.join(dst, fn)
        if os.path.exists(dp):
            done += 1
            continue
        try:
            im = load_dxt(sp)
        except Exception as e:
            print(f"ATLA {fn}: {e}", flush=True)
            skipped += 1
            continue

        if im.size[0] >= TARGET:
            big = im  # zaten yeterince buyuk
        else:
            big = upscale_rgba(im, 4)
            if big.size[0] != TARGET:
                big = big.resize((TARGET, TARGET), Image.LANCZOS)

        save_dxt(dp, big, name=orig_name(sp), fmt=D3DFMT_A8R8G8B8)
        done += 1
        if i % 25 == 0 or i == len(files):
            el = time.time() - t0
            print(f"{i}/{len(files)}  {el:.0f}s  kalan~{el / i * (len(files) - i) / 60:.1f}dk",
                  flush=True)

    print(f"BITTI islenen={done} atlanan={skipped} sure={time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
