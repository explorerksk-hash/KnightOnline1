"""bakread.py - Sikistirilmamis bir SQL Server .bak icindeki veri sayfalarini okur.

SQL Server kurmadan tablo satirlarini cikarmak icin. Yedek dosyasi, veritabaninin
8 KB'lik sayfalarini neredeyse oldugu gibi tasir; tip 1 (veri) sayfalarindaki
kayitlari cozeriz.

Sayfa basligi (96 bayt), ilgilendigimiz alanlar:
    0  headerVersion (her zaman 1)
    1  type          (1 = veri sayfasi)
   22  slotCnt       (sayfadaki kayit sayisi, uint16)

Kayit duzeni (birincil kayit):
    0   durum baytlari A   bit4 = null haritasi var, bit5 = degisken sutun var
    1   durum baytlari B
    2-3 sabit veri sonu ofseti (uint16)
    4.. sabit uzunluklu sutunlar
    -   uint16 sutun sayisi
    -   null haritasi  ceil(n/8) bayt
    -   uint16 degisken sutun sayisi + her biri icin uint16 bitis ofseti
    -   degisken veri
"""
from __future__ import annotations

import struct
from collections import Counter, defaultdict

PAGE = 8192
HEADER = 96


def pages(data: bytes, page_type: int = 1):
    """Dosyadaki verilen tipteki sayfalari (ofset, bayt) olarak uretir."""
    for off in range(0, len(data) - PAGE + 1, PAGE):
        if data[off] == 1 and data[off + 1] == page_type:
            yield off, data[off:off + PAGE]


def slot_offsets(pg: bytes):
    """Sayfa sonundaki slot dizisinden kayit ofsetlerini dondurur."""
    slot_cnt = struct.unpack_from('<H', pg, 22)[0]
    if slot_cnt == 0 or slot_cnt > 800:
        return []
    out = []
    for i in range(slot_cnt):
        o = struct.unpack_from('<H', pg, PAGE - 2 * (i + 1))[0]
        if HEADER <= o < PAGE - 2 * slot_cnt:
            out.append(o)
    return out


def parse_record(pg: bytes, off: int):
    """Bir kaydi coz. Dondurur: (sabit_veri, sutun_sayisi, null_haritasi, [degisken_alanlar])
       Cozulemezse None."""
    if off + 4 > PAGE:
        return None

    status_a = pg[off]
    rec_type = (status_a >> 1) & 0x07
    if rec_type != 0:            # yalnizca birincil kayitlar
        return None

    fixed_end = struct.unpack_from('<H', pg, off + 2)[0]
    if not (4 < fixed_end <= PAGE) or off + fixed_end > PAGE:
        return None

    fixed = pg[off + 4:off + fixed_end]
    p = off + fixed_end

    has_nullmap = bool(status_a & 0x10)
    has_varcols = bool(status_a & 0x20)

    ncols = 0
    nullmap = b''
    if has_nullmap:
        if p + 2 > PAGE:
            return None
        ncols = struct.unpack_from('<H', pg, p)[0]
        p += 2
        if ncols == 0 or ncols > 1024:
            return None
        nb = (ncols + 7) // 8
        nullmap = pg[p:p + nb]
        p += nb

    varfields = []
    if has_varcols:
        if p + 2 > PAGE:
            return None
        nvar = struct.unpack_from('<H', pg, p)[0]
        p += 2
        if nvar > 1024:
            return None
        ends = []
        for i in range(nvar):
            if p + 2 > PAGE:
                return None
            ends.append(struct.unpack_from('<H', pg, p)[0] & 0x7FFF)
            p += 2
        start = p - off
        for e in ends:
            if e < start or off + e > PAGE:
                varfields.append(None)
            else:
                varfields.append(pg[off + start:off + e])
                start = e

    return fixed, ncols, nullmap, varfields


def is_null(nullmap: bytes, col_index: int) -> bool:
    """col_index 0 tabanli."""
    byte = col_index // 8
    if byte >= len(nullmap):
        return False
    return bool(nullmap[byte] & (1 << (col_index % 8)))


def scan(data: bytes):
    """Tum veri sayfalarindaki kayitlari sabit-uzunluga gore gruplar."""
    by_len = defaultdict(list)
    for off, pg in pages(data):
        for so in slot_offsets(pg):
            rec = parse_record(pg, so)
            if rec is None:
                continue
            by_len[len(rec[0])].append(rec)
    return by_len


if __name__ == '__main__':
    import sys
    raw = open(sys.argv[1], 'rb').read()
    groups = scan(raw)
    print(f'{sum(len(v) for v in groups.values())} kayit, {len(groups)} farkli sabit uzunluk')
    for n, recs in sorted(groups.items(), key=lambda kv: -len(kv[1]))[:25]:
        cols = Counter(r[1] for r in recs).most_common(1)[0]
        print(f'  sabit={n:4d} bayt  kayit={len(recs):6d}  sutun~{cols[0]}')
