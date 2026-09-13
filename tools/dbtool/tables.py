"""tables.py - .bak icinden K_MONSTER ve K_NPCPOS satirlarini cozer.

Sutun duzenleri deps/db-models icindeki uretilmis model siniflarindan alinmistir;
SQL Server sabit uzunluklu sutunlari tanimlanma sirasina gore fiziksel olarak
saklar, bu yuzden sira birebir uyar. Sabit bolumun toplam uzunlugu kaydin
kendi basliginda yazili oldugu icin dogru tabloyu bulmak icin guvenilir bir
parmak izi olarak kullanilabilir (K_MONSTER 96 bayt, K_NPCPOS 51 bayt).
"""
from __future__ import annotations

import struct

from bakread import scan, is_null

# (ad, struct formati) - yalnizca sabit uzunluklu sutunlar, tanimlanma sirasinda
MONSTER = [
    ('MonsterId', '<h'), ('PictureId', '<h'), ('Size', '<h'),
    ('Weapon1', '<i'), ('Weapon2', '<i'),
    ('Group', '<B'), ('ActType', '<B'), ('Type', '<B'), ('Family', '<B'),
    ('Rank', '<B'), ('Title', '<B'),
    ('SellingGroup', '<i'), ('Level', '<h'), ('Exp', '<i'), ('Loyalty', '<i'),
    ('HitPoints', '<i'), ('ManaPoints', '<h'), ('Attack', '<h'), ('Armor', '<h'),
    ('HitRate', '<h'), ('EvadeRate', '<h'), ('Damage', '<h'), ('AttackDelay', '<h'),
    ('WalkSpeed', '<B'), ('RunSpeed', '<B'), ('StandTime', '<h'),
    ('Magic1', '<i'), ('Magic2', '<i'), ('Magic3', '<i'),
    ('FireResist', '<h'), ('ColdResist', '<h'), ('LightningResist', '<h'),
    ('MagicResist', '<h'), ('DiseaseResist', '<h'), ('PoisonResist', '<h'),
    ('LightResist', '<h'), ('Bulk', '<h'),
    ('AttackRange', '<B'), ('SearchRange', '<B'), ('TracingRange', '<B'),
    ('Money', '<i'), ('Item', '<h'),
    ('DirectAttack', '<B'), ('MagicAttack', '<B'), ('MoneyType', '<B'),
]
MONSTER_FIXED = 96
MONSTER_COLS = 46          # Name degisken sutunu dahil

NPCPOS = [
    ('ZoneId', '<h'), ('NpcId', '<i'),
    ('ActType', '<B'), ('RegenType', '<B'), ('DungeonFamily', '<B'),
    ('SpecialType', '<B'), ('TrapNumber', '<B'),
    ('LeftX', '<i'), ('TopZ', '<i'), ('RightX', '<i'), ('BottomZ', '<i'),
    ('LimitMinZ', '<i'), ('LimitMinX', '<i'), ('LimitMaxX', '<i'), ('LimitMaxZ', '<i'),
    ('NumNpc', '<B'), ('RespawnTime', '<h'), ('Direction', '<i'),
    ('PathPointCount', '<B'),
]
NPCPOS_FIXED = 51
NPCPOS_COLS = 20           # Path degisken sutunu dahil


def _decode_fixed(fixed: bytes, layout):
    off = 0
    row = {}
    for name, fmt in layout:
        size = struct.calcsize(fmt)
        row[name] = struct.unpack_from(fmt, fixed, off)[0]
        off += size
    return row


def _text(raw):
    if raw is None:
        return None
    # varchar; kontrol karakterlerinde kes
    s = raw.split(b'\x00')[0]
    try:
        return s.decode('cp1254').strip()
    except Exception:
        return s.decode('latin-1', 'replace').strip()


def load(raw: bytes):
    """(monsters, npcpos) dondurur."""
    groups = scan(raw)

    monsters = []
    for fixed, ncols, nullmap, varf in groups.get(MONSTER_FIXED, []):
        if ncols != MONSTER_COLS:
            continue
        row = _decode_fixed(fixed, MONSTER)
        row['Name'] = _text(varf[0]) if varf else None
        monsters.append(row)

    npcpos = []
    for fixed, ncols, nullmap, varf in groups.get(NPCPOS_FIXED, []):
        if ncols != NPCPOS_COLS:
            continue
        row = _decode_fixed(fixed, NPCPOS)
        row['Path'] = _text(varf[0]) if varf else None
        npcpos.append(row)

    return monsters, npcpos


if __name__ == '__main__':
    import sys
    mons, pos = load(open(sys.argv[1], 'rb').read())
    print(f'K_MONSTER: {len(mons)} satir, K_NPCPOS: {len(pos)} satir')
    named = [m for m in mons if m['Name']]
    print(f'isimli canavar: {len(named)}')
    for m in sorted(named, key=lambda r: r['Level'])[:5]:
        print(f"  sSid={m['MonsterId']:6d} lv{m['Level']:3d} hp{m['HitPoints']:7d}  {m['Name']}")
