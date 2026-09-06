"""n3tbl.py - KO .tbl sifresini cozer/uygular ve satirlari okur (CN3TableBaseImpl + CN3TableBase)."""
import struct, sys

DT_NONE, DT_CHAR, DT_BYTE, DT_SHORT, DT_WORD, DT_INT, DT_DWORD, DT_STRING, DT_FLOAT, DT_DOUBLE = range(10)
_SIZES = {DT_CHAR: 1, DT_BYTE: 1, DT_SHORT: 2, DT_WORD: 2, DT_INT: 4, DT_DWORD: 4, DT_FLOAT: 4, DT_DOUBLE: 8}
_FMT = {DT_CHAR: 'b', DT_BYTE: 'B', DT_SHORT: 'h', DT_WORD: 'H', DT_INT: 'i', DT_DWORD: 'I', DT_FLOAT: 'f', DT_DOUBLE: 'd'}


def decrypt(data: bytes) -> bytes:
    key_r, c1, c2 = 0x0816, 0x6081, 0x1608
    out = bytearray(len(data))
    for i, b in enumerate(data):
        out[i] = b ^ (key_r >> 8)
        key_r = ((b + key_r) * c1 + c2) & 0xFFFF
    return bytes(out)


def encrypt(data: bytes) -> bytes:
    key_r, c1, c2 = 0x0816, 0x6081, 0x1608
    out = bytearray(len(data))
    for i, p in enumerate(data):
        c = p ^ (key_r >> 8)
        out[i] = c
        key_r = ((c + key_r) * c1 + c2) & 0xFFFF
    return bytes(out)


def read_rows(plain: bytes, enc='cp1254'):
    off = 0
    n = struct.unpack_from('<i', plain, off)[0]; off += 4
    types = list(struct.unpack_from('<%di' % n, plain, off)); off += 4 * n
    rc = struct.unpack_from('<i', plain, off)[0]; off += 4
    rows = []
    for _ in range(rc):
        row = []
        for t in types:
            if t == DT_STRING:
                ln = struct.unpack_from('<i', plain, off)[0]; off += 4
                row.append(plain[off:off + ln].decode(enc, 'replace')); off += ln
            else:
                row.append(struct.unpack_from('<' + _FMT[t], plain, off)[0]); off += _SIZES[t]
        rows.append(row)
    return types, rows


if __name__ == '__main__':
    types, rows = read_rows(decrypt(open(sys.argv[1], 'rb').read()))
    print('types:', types)
    for r in rows:
        print(r)
