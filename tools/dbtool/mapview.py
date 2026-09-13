"""mapview.py - Bir .smd sunucu haritasini ve uzerindeki K_NPCPOS kayitlarini PNG'ye cizer.

    python mapview.py <zoneId> <smd> <bak> <cikti.png> [--spawn spawn.json]

Arazi .smd basliktan okunur: int32 grid boyutu, float birim mesafe, ardindan
grid*grid adet float yukseklik (z dis, x ic dongu). Oyun dunyasi koordinatlari
(grid-1)*birim genisligindedir.

Renkler: yukseklik acik/koyu yesil, dik egim koyulastirilmis, su mavi.
Kirmizi halka = mevcut NPC kaydi, sari dikdortgen = onerilen spawn alani.
"""
from __future__ import annotations

import json
import struct
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, __file__.rsplit('/', 1)[0])
from tables import load as load_tables


def read_terrain(path: str):
    raw = open(path, 'rb').read()
    n, unit = struct.unpack_from('<if', raw, 0)
    h = np.frombuffer(raw, '<f4', count=n * n, offset=8).reshape(n, n).astype(np.float64)
    h = np.nan_to_num(h, nan=0.0, posinf=0.0, neginf=0.0)
    h[h < 1e-6] = 0.0
    return n, unit, h


def slope_of(h: np.ndarray):
    gy, gx = np.gradient(h)
    return np.hypot(gx, gy)


def render(n, unit, h, slope):
    world = int((n - 1) * unit)
    k = int(unit)
    hh = np.kron(h, np.ones((k, k)))[:world, :world]
    ss = np.kron(slope, np.ones((k, k)))[:world, :world]

    lo, hi = 60.0, 140.0
    t = np.clip((hh - lo) / (hi - lo), 0, 1)
    r = (60 + t * 150).astype(np.uint8)
    g = (85 + t * 110).astype(np.uint8)
    b = (55 + t * 100).astype(np.uint8)

    steep = ss > 2.5
    r[steep] //= 2
    g[steep] //= 2
    b[steep] //= 2

    water = hh < 1.0
    r[water], g[water], b[water] = 30, 50, 90

    return Image.fromarray(np.dstack([r, g, b]), 'RGB'), world


def main():
    zone_id = int(sys.argv[1])
    smd, bak, out = sys.argv[2], sys.argv[3], sys.argv[4]

    n, unit, h = read_terrain(smd)
    slope = slope_of(h)
    img, world = render(n, unit, h, slope)
    d = ImageDraw.Draw(img)

    _, pos = load_tables(open(bak, 'rb').read())
    rows = [p for p in pos if p['ZoneId'] == zone_id]
    for p in rows:
        x = (p['LeftX'] + p['RightX']) // 2
        z = (p['TopZ'] + p['BottomZ']) // 2
        col = (255, 80, 80) if p['ActType'] >= 100 else (120, 200, 255)
        d.ellipse([x - 4, z - 4, x + 4, z + 4], outline=col, width=2)

    if '--spawn' in sys.argv:
        spawns = json.load(open(sys.argv[sys.argv.index('--spawn') + 1]))
        for s in spawns:
            d.rectangle([s['LeftX'], s['TopZ'], s['RightX'], s['BottomZ']],
                        outline=(255, 215, 60), width=2)
            d.text((s['LeftX'] + 3, s['TopZ'] + 3), f"{s['Name']} x{s['NumNpc']}",
                   fill=(255, 240, 170))

    d.text((10, 10), f'zone {zone_id}  {smd.rsplit("/", 1)[-1]}  {world}x{world}',
           fill=(255, 255, 255))
    d.text((10, 26), 'kirmizi=NPC  mavi=mob  sari=onerilen spawn', fill=(230, 230, 230))
    img.save(out)
    print('yazildi', out, img.size, f'{len(rows)} mevcut kayit')


if __name__ == '__main__':
    main()
