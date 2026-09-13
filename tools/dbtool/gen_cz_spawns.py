"""gen_cz_spawns.py - Colony Zone (Ronark Land) icin K_NPCPOS spawn satirlari uretir.

Neden gerekli: OpenKO v0.1.2 veritabaninda 6901-6964 araligindaki 42 canavar
(Deruvish, Apostle, Harpy, Troll, Stone golem, Riote, Atross, DARK MARE ...)
tanimli ama K_NPCPOS'ta HICBIR satiri yok. Yani CZ'de tek bir canavar spawn
olmuyor. Bu betik o eksigi kapatir.

Yerlesim uydurma degil, araziden turetilir:
  * .smd yukseklik haritasindan egim hesaplanir; dik yamac ve su disarida birakilir
  * mevcut NPC kayitlarinin (us, muhafiz, kapi) cevresi bos birakilir
  * canavar seviyesi usse olan uzakliga gore secilir: kenarlarda dusuk,
    haritanin ortasinda yuksek - KO'nun kendi CZ mantigi
  * patronlar (Riote, Atross, DARK MARE) merkeze yakin, tek tek, uzun respawn

Kullanim:
    python gen_cz_spawns.py <bak> <smd> <zoneId> <cikti.sql> [--json onizleme.json]
"""
from __future__ import annotations

import json
import struct
import sys

import numpy as np

sys.path.insert(0, __file__.rsplit('/', 1)[0])
from tables import load as load_tables

# --- CZ kadrosu: (sSid, ad, seviye, kac tane bir grupta, respawn sn, katman) ---
# katman 0 = usse yakin (dusuk), 1 = orta, 2 = merkez (yuksek), 3 = patron
ROSTER = [
    (6950, 'Lobo',          45, 5,  30, 0),
    (6951, 'Lupus',         50, 5,  30, 0),
    (6903, 'Death knight',  45, 5,  30, 0),
    (6905, 'Watcher',       46, 5,  30, 0),
    (6906, 'Blood seeker',  50, 5,  35, 0),

    (6952, 'Lycaon',        55, 5,  35, 1),
    (6910, 'Cardinal',      55, 5,  35, 1),
    (6959, 'Duke',          55, 5,  35, 1),
    (6911, 'Haunga',        60, 4,  40, 1),
    (6913, 'Deruvish',      60, 4,  40, 1),
    (6957, 'bone collecter',60, 4,  40, 1),
    (6960, 'Bishop',        60, 4,  40, 1),
    (6954, 'Barkirra',      60, 4,  40, 1),

    (6961, 'Bach',          65, 3,  45, 2),
    (6962, 'Javana',        65, 3,  45, 2),
    (6915, 'Troll',         70, 3,  50, 2),
    (6917, 'Apostle',       70, 3,  50, 2),
    (6928, 'Harpy',         70, 3,  50, 2),
    (6955, 'Lesath',        75, 3,  50, 2),
    (6956, 'Shaula',        75, 3,  50, 2),
    (6918, 'Troll Warrior', 80, 2,  60, 2),
    (6919, 'Raven Harpy',   80, 2,  60, 2),
    (6958, 'Dragon tooth',  80, 2,  60, 2),

    (6914, 'Riote',         70, 1, 1800, 3),
    (6920, 'Atross',        85, 1, 1800, 3),
    (6963, 'Samma',         90, 1, 1800, 3),
    (6923, 'DARK MARE',    145, 1, 3600, 3),
]

CELL = 48          # spawn dikdortgeni kenar uzunlugu (dunya birimi)
CLEAR_NPC = 70     # mevcut NPC'lerin cevresinde bos birakilacak yaricap
EDGE = 60          # harita kenarindan pay


def kmeans(pts, k, iters=40, seed=0):
    """Kucuk, bagimliliksiz k-means (scipy yok)."""
    rng = np.random.default_rng(seed)
    cent = pts[rng.choice(len(pts), k, replace=False)].copy()
    for _ in range(iters):
        lab = np.argmin(((pts[:, None, :] - cent[None, :, :]) ** 2).sum(-1), axis=1)
        for i in range(k):
            sel = pts[lab == i]
            if len(sel):
                cent[i] = sel.mean(axis=0)
    return cent


def read_terrain(path):
    raw = open(path, 'rb').read()
    n, unit = struct.unpack_from('<if', raw, 0)
    h = np.frombuffer(raw, '<f4', count=n * n, offset=8).reshape(n, n).astype(np.float64)
    h = np.nan_to_num(h, nan=0.0, posinf=0.0, neginf=0.0)
    h[h < 1e-6] = 0.0
    return n, unit, h


def build(bak, smd, zone_id):
    n, unit, h = read_terrain(smd)
    world = int((n - 1) * unit)
    gy, gx = np.gradient(h)
    slope = np.hypot(gx, gy)

    _, pos = load_tables(open(bak, 'rb').read())
    existing = [((p['LeftX'] + p['RightX']) / 2, (p['TopZ'] + p['BottomZ']) / 2)
                for p in pos if p['ZoneId'] == zone_id]
    if not existing:
        raise SystemExit(f'zone {zone_id} icin mevcut NPC kaydi yok, us konumlari bilinemiyor')

    # Iki us: mevcut NPC'lerin en uzak iki kumesi (harita kosegeni boyunca)
    pts = np.array(existing)
    base_a = pts[np.argmin(pts[:, 0] + pts[:, 1])]      # sol-ust
    base_b = pts[np.argmax(pts[:, 0] + pts[:, 1])]      # sag-alt
    centre = np.array([world / 2, world / 2])

    def ok(cx, cz):
        """Dikdortgenin merkezi spawn icin uygun mu?"""
        if not (EDGE < cx < world - EDGE and EDGE < cz < world - EDGE):
            return False
        gxi, gzi = int(cx / unit), int(cz / unit)
        r = max(1, int((CELL / 2) / unit))
        sub_h = h[max(0, gzi - r):gzi + r + 1, max(0, gxi - r):gxi + r + 1]
        sub_s = slope[max(0, gzi - r):gzi + r + 1, max(0, gxi - r):gxi + r + 1]
        if sub_h.size == 0 or sub_h.min() < 1.0:      # su
            return False
        if sub_s.mean() > 1.2 or sub_s.max() > 3.0:   # dik yamac
            return False
        for ex, ez in existing:                        # us / muhafiz cevresi
            if abs(ex - cx) < CLEAR_NPC and abs(ez - cz) < CLEAR_NPC:
                return False
        return True

    # Aday hucreler
    cands = []
    step = CELL + 12
    for cz in range(EDGE, world - EDGE, step):
        for cx in range(EDGE, world - EDGE, step):
            if ok(cx, cz):
                d_base = min(np.hypot(cx - base_a[0], cz - base_a[1]),
                             np.hypot(cx - base_b[0], cz - base_b[1]))
                d_cent = np.hypot(cx - centre[0], cz - centre[1])
                cands.append((cx, cz, d_base, d_cent))

    if not cands:
        raise SystemExit('uygun spawn alani bulunamadi')

    # Ayni canavari bir arada tut: adaylari kume kume ayirip her kumeye tek tur
    # canavar veriyoruz. Gercek CZ'de "Deruvish bolgesi", "Harpy bolgesi" vardir;
    # dagitik yerlestirme oyuncuya rastgele ve yapay gelir.
    pts = np.array([[c[0], c[1]] for c in cands], dtype=float)
    normals = [m for m in ROSTER if m[5] != 3]
    k = min(len(normals), len(cands))
    centroids = kmeans(pts, k, seed=7)

    labels = np.argmin(((pts[:, None, :] - centroids[None, :, :]) ** 2).sum(-1), axis=1)

    # Her kumenin usse uzakligi -> dusuk seviye usse yakin, yuksek merkeze dogru
    cl_dist = []
    for ci in range(k):
        sel = pts[labels == ci]
        if len(sel) == 0:
            cl_dist.append((ci, 1e9))
            continue
        cx, cz = sel.mean(axis=0)
        d = min(np.hypot(cx - base_a[0], cz - base_a[1]),
                np.hypot(cx - base_b[0], cz - base_b[1]))
        cl_dist.append((ci, d))
    cl_dist.sort(key=lambda t: t[1])

    pool = sorted(normals, key=lambda m: m[2])        # seviyeye gore
    rows = []
    for (ci, _), mon in zip(cl_dist, pool):
        sid, name, lvl, cnt, resp, _ = mon
        for cx, cz in pts[labels == ci]:
            rows.append(make_row(zone_id, sid, name, lvl, cnt, resp, cx, cz))

    # Patronlar: merkeze yakin ama birbirinden uzak, tek tek duran noktalar
    by_centre = sorted(cands, key=lambda c: c[3])
    bosses, taken = [], []
    for c in by_centre:
        if all(np.hypot(c[0] - u[0], c[1] - u[1]) > 180 for u in taken):
            bosses.append(c)
            taken.append(c)
        if len(bosses) == 4:
            break

    for (sid, name, lvl, cnt, resp, _), (cx, cz, _, _) in zip([m for m in ROSTER if m[5] == 3], bosses):
        rows.append(make_row(zone_id, sid, name, lvl, cnt, resp, cx, cz, boss=True))

    return rows, world


def make_row(zone_id, sid, name, lvl, cnt, resp, cx, cz, boss=False):
    half = (CELL // 3) if boss else (CELL // 2)
    left, right = int(cx - half), int(cx + half)
    top, bottom = int(cz + half), int(cz - half)      # TopZ > BottomZ (mevcut satirlardaki duzen)
    return {
        'ZoneID': zone_id, 'NpcID': sid, 'Name': name, 'Level': lvl,
        'ActType': 1, 'RegenType': 0, 'DungeonFamily': 0, 'SpecialType': 0,
        'TrapNumber': 0,
        'LeftX': left, 'TopZ': top, 'RightX': right, 'BottomZ': bottom,
        # Mevcut calisan satirlardaki esleme birebir taklit edilir
        'LimitMinZ': left, 'LimitMinX': top + 1, 'LimitMaxX': right, 'LimitMaxZ': bottom - 2,
        'NumNPC': cnt, 'RegTime': resp, 'byDirection': 0, 'DotCnt': 0,
    }


COLS = ['ZoneID', 'NpcID', 'ActType', 'RegenType', 'DungeonFamily', 'SpecialType',
        'TrapNumber', 'LeftX', 'TopZ', 'RightX', 'BottomZ',
        'LimitMinZ', 'LimitMinX', 'LimitMaxX', 'LimitMaxZ',
        'NumNPC', 'RegTime', 'byDirection', 'DotCnt']


def to_sql(rows, zone_id):
    out = [
        '-- Colony Zone (Ronark Land) canavar spawn verisi',
        '-- Uretildi: tools/dbtool/gen_cz_spawns.py',
        '--',
        '-- OpenKO v0.1.2 veritabaninda 6901-6964 araligindaki CZ canavarlari tanimli',
        '-- ama K_NPCPOS\'ta hic satiri yoktu; bu yuzden bolgede tek bir mob cikmiyordu.',
        '-- Konumlar .smd yukseklik haritasindan turetildi: su ve dik yamac elendi,',
        '-- mevcut NPC/us cevresi bos birakildi, seviye usse uzakliga gore artiyor.',
        '',
        'USE KN_online;',
        'GO',
        '',
        'BEGIN TRANSACTION;',
        '',
        f'-- Ayni betigin tekrar calistirilabilmesi icin once bu bolgenin uretilmis',
        f'-- canavar satirlari silinir (NPC/muhafiz kayitlari ActType>=100, dokunulmaz).',
        f'DELETE FROM K_NPCPOS WHERE ZoneID = {zone_id} AND NpcID BETWEEN 6901 AND 6964;',
        '',
    ]
    collist = ', '.join(f'[{c}]' for c in COLS)
    for r in rows:
        vals = ', '.join(str(r[c]) for c in COLS)
        out.append(f'INSERT INTO K_NPCPOS ({collist}) VALUES ({vals});'
                   f'  -- {r["Name"]} lv{r["Level"]} x{r["NumNPC"]}')
    total = sum(r['NumNPC'] for r in rows)
    out += ['', 'COMMIT;', 'GO', '',
            f'-- {len(rows)} spawn alani, toplam {total} canavar']
    return '\n'.join(out) + '\n'


def main():
    bak, smd, zone_id, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
    rows, world = build(bak, smd, zone_id)
    open(out, 'w', encoding='utf-8').write(to_sql(rows, zone_id))

    if '--json' in sys.argv:
        json.dump([{'LeftX': r['LeftX'], 'TopZ': r['BottomZ'], 'RightX': r['RightX'],
                    'BottomZ': r['TopZ'], 'Name': r['Name'], 'NumNpc': r['NumNPC']}
                   for r in rows],
                  open(sys.argv[sys.argv.index('--json') + 1], 'w'))

    from collections import Counter
    c = Counter(r['Name'] for r in rows)
    print(f'zone {zone_id}: {len(rows)} spawn alani, {sum(r["NumNPC"] for r in rows)} canavar')
    for name, k in c.most_common():
        lvl = next(r['Level'] for r in rows if r['Name'] == name)
        print(f'   {name:16s} lv{lvl:3d}  {k:3d} alan')


if __name__ == '__main__':
    main()
