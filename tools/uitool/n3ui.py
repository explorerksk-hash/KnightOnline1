"""
n3ui.py - Open-KO / Knight Online N3 UI (.uif) ve doku (.dxt) okuyucu-yazici.

Format, src/N3Base/N3UIBase.cpp, N3UIImage.cpp, N3UIButton.cpp, N3UIStatic.cpp,
N3UIEdit.cpp, N3UIString.cpp, N3UIArea.cpp ve N3Texture.cpp icindeki Load()/Save()
kodundan birebir cikarilmistir (dosya format surumu 1264+).

Kullanim:
    from n3ui import *
    root = UIBase(id="Login")
    root.add(UIImage(id="img_bg", region=(0,0,1024,768), tex="UI\\bg.dxt", uv=(0,0,1,0.75)))
    root.save("Login.uif")

    dump("Login.uif")   # var olan bir .uif'i agac olarak yazdirir
"""
from __future__ import annotations

import struct
from dataclasses import dataclass, field
from typing import BinaryIO

# ---------------------------------------------------------------- sabitler
UI_TYPE_BASE, UI_TYPE_BUTTON, UI_TYPE_STATIC, UI_TYPE_PROGRESS, UI_TYPE_IMAGE, \
    UI_TYPE_SCROLLBAR, UI_TYPE_STRING, UI_TYPE_TRACKBAR, UI_TYPE_EDIT, UI_TYPE_AREA, \
    UI_TYPE_TOOLTIP, UI_TYPE_ICON, UI_TYPE_ICON_MANAGER, UI_TYPE_ICONSLOT, UI_TYPE_LIST = range(15)

UISTYLE_NONE = 0
UISTYLE_ALWAYSTOP = 0x1
UISTYLE_MODAL = 0x2
UISTYLE_FOCUS_UNABLE = 0x4
UISTYLE_BTN_NORMAL = 0x00010000
UISTYLE_BTN_CHECK = 0x00020000
UISTYLE_IMAGE_ANIMATE = 0x00010000
UISTYLE_STRING_MULTILINE = 0x0
UISTYLE_STRING_SINGLELINE = 0x00100000
UISTYLE_STRING_ALIGNLEFT = 0x00200000
UISTYLE_STRING_ALIGNRIGHT = 0x00400000
UISTYLE_STRING_ALIGNCENTER = 0x00800000
UISTYLE_STRING_ALIGNTOP = 0x01000000
UISTYLE_STRING_ALIGNBOTTOM = 0x02000000
UISTYLE_STRING_ALIGNVCENTER = 0x04000000
UISTYLE_EDIT_PASSWORD = 0x10000000
UISTYLE_EDIT_NUMBERONLY = 0x20000000

D3DFONT_BOLD = 1
D3DFONT_ITALIC = 2

BS_NORMAL, BS_DOWN, BS_ON, BS_DISABLE = 0, 1, 2, 3

# D3DFORMAT
D3DFMT_A8R8G8B8 = 21
D3DFMT_X8R8G8B8 = 22
D3DFMT_A1R5G5B5 = 25
D3DFMT_A4R4G4B4 = 26
D3DFMT_DXT1 = 0x31545844
D3DFMT_DXT3 = 0x33545844
D3DFMT_DXT5 = 0x35545844


def argb(r: int, g: int, b: int, a: int = 255) -> int:
    return ((a & 0xFF) << 24) | ((r & 0xFF) << 16) | ((g & 0xFF) << 8) | (b & 0xFF)


def hexcolor(s: str, a: int = 255) -> int:
    s = s.lstrip("#")
    return argb(int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), a)


# ---------------------------------------------------------------- binary yardimcilari
def _w_i32(f: BinaryIO, v: int) -> None:
    f.write(struct.pack("<i", v))


def _w_u32(f: BinaryIO, v: int) -> None:
    f.write(struct.pack("<I", v & 0xFFFFFFFF))


def _w_str(f: BinaryIO, s: str, enc: str = "cp1254") -> None:
    b = s.encode(enc) if s else b""
    _w_i32(f, len(b))
    if b:
        f.write(b)


def _w_rect(f: BinaryIO, r) -> None:
    f.write(struct.pack("<iiii", *[int(x) for x in r]))


def _r_i32(f: BinaryIO) -> int:
    return struct.unpack("<i", f.read(4))[0]


def _r_u32(f: BinaryIO) -> int:
    return struct.unpack("<I", f.read(4))[0]


def _r_str(f: BinaryIO, enc: str = "cp1254") -> str:
    n = _r_i32(f)
    if n <= 0:
        return ""
    return f.read(n).decode(enc, errors="replace")


def _r_rect(f: BinaryIO):
    return struct.unpack("<iiii", f.read(16))


# ---------------------------------------------------------------- UI siniflari
@dataclass
class UIBase:
    id: str = ""
    region: tuple = (0, 0, 0, 0)          # left, top, right, bottom (ekran pikseli)
    movable: tuple = (0, 0, 0, 0)         # tutup surukleme alani
    style: int = UISTYLE_NONE
    reserved: int = 0                     # buton state / animasyon sirasi
    tooltip: str = ""
    snd_open: str = ""
    snd_close: str = ""
    name: str = ""                        # CN3BaseFileAccess m_szName (genelde bos)
    children: list = field(default_factory=list)   # alttan uste (son eklenen en ustte cizilir)

    ui_type = UI_TYPE_BASE

    # -- agac
    def add(self, *kids: "UIBase") -> "UIBase":
        for k in kids:
            self.children.append(k)
        return kids[0] if len(kids) == 1 else self

    def find(self, id_: str) -> "UIBase | None":
        for c in self.children:
            if c.id == id_:
                return c
            r = c.find(id_)
            if r is not None:
                return r
        return None

    def move(self, dx: int, dy: int) -> "UIBase":
        """Kendini ve tum cocuklari kaydirir (CN3UIBase::MoveOffset)."""
        l, t, r, b = self.region
        self.region = (l + dx, t + dy, r + dx, b + dy)
        l, t, r, b = self.movable
        self.movable = (l + dx, t + dy, r + dx, b + dy)
        self._move_extra(dx, dy)
        for c in self.children:
            c.move(dx, dy)
        return self

    def _move_extra(self, dx: int, dy: int) -> None:
        pass

    @property
    def width(self) -> int:
        return self.region[2] - self.region[0]

    @property
    def height(self) -> int:
        return self.region[3] - self.region[1]

    # -- yazma
    def _write_base(self, f: BinaryIO) -> None:
        _w_str(f, self.name)                         # CN3BaseFileAccess
        f.write(struct.pack("<hh", len(self.children), 0))  # 1264+: int16 count, int16 0
        # Yukleme AddChild()=push_front ile listenin BASINA ekler, Render ise listeyi
        # SONDAN basa gezer -> dosyadaki ILK cocuk ilk (en altta) cizilir.
        # Yani dosya sirasi = alttan uste; ekleme sirasinda yazilir.
        for c in self.children:
            _w_u32(f, c.ui_type)
            c.write(f)
        _w_str(f, self.id)
        _w_rect(f, self.region)
        _w_rect(f, self.movable)
        _w_u32(f, self.style)
        _w_u32(f, self.reserved)
        _w_str(f, self.tooltip)
        _w_str(f, self.snd_open)
        _w_str(f, self.snd_close)

    def _write_extra(self, f: BinaryIO) -> None:
        pass

    def write(self, f: BinaryIO) -> None:
        self._write_base(f)
        self._write_extra(f)

    def save(self, path: str) -> None:
        with open(path, "wb") as f:
            self.write(f)

    # -- okuma
    def _read_base(self, f: BinaryIO) -> None:
        self.name = _r_str(f)
        cnt, _ = struct.unpack("<hh", f.read(4))
        if cnt < 0 or cnt > 4096:
            raise ValueError("gecersiz child sayisi (1098 formati olabilir)")
        for _ in range(cnt):
            t = _r_u32(f)
            cls = _TYPE_MAP.get(t)
            if cls is None:
                raise ValueError(f"desteklenmeyen UI tipi {t}")
            c = cls()
            c.read(f)
            self.children.append(c)
        self.id = _r_str(f)
        self.region = _r_rect(f)
        self.movable = _r_rect(f)
        self.style = _r_u32(f)
        self.reserved = _r_u32(f)
        self.tooltip = _r_str(f)
        self.snd_open = _r_str(f)
        self.snd_close = _r_str(f)

    def _read_extra(self, f: BinaryIO) -> None:
        pass

    def read(self, f: BinaryIO) -> "UIBase":
        self._read_base(f)
        self._read_extra(f)
        return self

    @classmethod
    def load(cls, path: str) -> "UIBase":
        with open(path, "rb") as f:
            return cls().read(f)

    # -- dokum
    def describe(self) -> str:
        return ""

    def dump(self, indent: int = 0) -> str:
        pad = "  " * indent
        out = f"{pad}{type(self).__name__} id={self.id!r} region={self.region} style=0x{self.style:08X}"
        if self.reserved:
            out += f" reserved={self.reserved}"
        extra = self.describe()
        if extra:
            out += " " + extra
        lines = [out]
        for c in self.children:
            lines.append(c.dump(indent + 1))
        return "\n".join(lines)


@dataclass
class UIImage(UIBase):
    tex: str = ""
    uv: tuple = (0.0, 0.0, 1.0, 1.0)
    anim_frame: float = 0.0
    ui_type = UI_TYPE_IMAGE

    def _write_extra(self, f):
        _w_str(f, self.tex)
        f.write(struct.pack("<ffff", *self.uv))
        f.write(struct.pack("<f", self.anim_frame))

    def _read_extra(self, f):
        self.tex = _r_str(f)
        self.uv = struct.unpack("<ffff", f.read(16))
        self.anim_frame = struct.unpack("<f", f.read(4))[0]

    def describe(self):
        return f"tex={self.tex!r} uv={tuple(round(x, 4) for x in self.uv)}"


@dataclass
class UIString(UIBase):
    font: str = "Segoe UI"
    font_height: int = 12
    bold: bool = False
    italic: bool = False
    color: int = 0xFFFFFFFF
    text: str = ""
    line_spacing: int = 0
    ui_type = UI_TYPE_STRING

    def _write_extra(self, f):
        _w_str(f, self.font)
        _w_u32(f, self.font_height)
        _w_u32(f, (D3DFONT_BOLD if self.bold else 0) | (D3DFONT_ITALIC if self.italic else 0))
        _w_u32(f, self.color)
        _w_str(f, self.text)
        _w_i32(f, self.line_spacing)

    def _read_extra(self, f):
        self.font = _r_str(f)
        if self.font:
            self.font_height = _r_u32(f)
            fl = _r_u32(f)
            self.bold, self.italic = bool(fl & 1), bool(fl & 2)
        self.color = _r_u32(f)
        self.text = _r_str(f)
        self.line_spacing = _r_i32(f)

    def describe(self):
        return f"font={self.font!r}/{self.font_height} color=0x{self.color:08X} text={self.text!r}"


@dataclass
class UIButton(UIBase):
    click: tuple | None = None        # tiklama alani; None -> region
    snd_on: str = ""
    snd_click: str = ""
    style: int = UISTYLE_BTN_NORMAL
    ui_type = UI_TYPE_BUTTON

    def _move_extra(self, dx, dy):
        if self.click:
            l, t, r, b = self.click
            self.click = (l + dx, t + dy, r + dx, b + dy)

    def _write_extra(self, f):
        _w_rect(f, self.click or self.region)
        _w_str(f, self.snd_on)
        _w_str(f, self.snd_click)

    def _read_extra(self, f):
        self.click = _r_rect(f)
        self.snd_on = _r_str(f)
        self.snd_click = _r_str(f)


@dataclass
class UIStatic(UIBase):
    snd_click: str = ""
    ui_type = UI_TYPE_STATIC

    def _write_extra(self, f):
        _w_str(f, self.snd_click)

    def _read_extra(self, f):
        self.snd_click = _r_str(f)


@dataclass
class UIEdit(UIStatic):
    snd_typing: str = ""
    ui_type = UI_TYPE_EDIT

    def _write_extra(self, f):
        UIStatic._write_extra(self, f)
        _w_str(f, self.snd_typing)

    def _read_extra(self, f):
        UIStatic._read_extra(self, f)
        self.snd_typing = _r_str(f)


@dataclass
class UIArea(UIBase):
    area_type: int = 0
    ui_type = UI_TYPE_AREA

    def _write_extra(self, f):
        _w_i32(f, self.area_type)

    def _read_extra(self, f):
        self.area_type = _r_i32(f)


@dataclass
class UIProgress(UIBase):
    """N3UIProgress: ek veri yok, sadece child imgeler."""
    ui_type = UI_TYPE_PROGRESS


@dataclass
class UIScrollBar(UIBase):
    """N3UIScrollBar: ek veri yok; child butonlar reserved ile (0 up,1 down,2 middle...)."""
    ui_type = UI_TYPE_SCROLLBAR


@dataclass
class UITrackBar(UIBase):
    """N3UITrackBar: ek veri yok; child imgeler reserved ile."""
    ui_type = UI_TYPE_TRACKBAR


@dataclass
class UIList(UIBase):
    font: str = "Segoe UI"
    font_height: int = 12
    color: int = 0xFFFFFFFF
    bold: bool = False
    italic: bool = False
    ui_type = UI_TYPE_LIST

    def _write_extra(self, f):
        _w_str(f, self.font)
        if self.font:
            _w_u32(f, self.font_height)
            _w_u32(f, self.color)
            _w_u32(f, 1 if self.bold else 0)
            _w_u32(f, 1 if self.italic else 0)

    def _read_extra(self, f):
        self.font = _r_str(f)
        if self.font:
            self.font_height = _r_u32(f)
            self.color = _r_u32(f)
            self.bold = bool(_r_u32(f))
            self.italic = bool(_r_u32(f))

    def describe(self):
        return f"font={self.font!r}/{self.font_height} color=0x{self.color:08X}"


_TYPE_MAP = {
    UI_TYPE_BASE: UIBase,
    UI_TYPE_IMAGE: UIImage,
    UI_TYPE_STRING: UIString,
    UI_TYPE_BUTTON: UIButton,
    UI_TYPE_STATIC: UIStatic,
    UI_TYPE_EDIT: UIEdit,
    UI_TYPE_AREA: UIArea,
    UI_TYPE_PROGRESS: UIProgress,
    UI_TYPE_SCROLLBAR: UIScrollBar,
    UI_TYPE_TRACKBAR: UITrackBar,
    UI_TYPE_LIST: UIList,
}


def dump(path: str) -> str:
    return UIBase.load(path).dump()


# ---------------------------------------------------------------- .dxt yazici
def save_dxt(path: str, img, name: str = "") -> None:
    """PIL RGBA gorseli sikistirmasiz A8R8G8B8 .dxt (NTF v3, mipmap yok) olarak yazar.

    Boyutlar 2'nin kuvveti olmali (256/512/1024). 512+ icin motorun bekledigi
    256*256*2 baytlik ek 'voodoo' blogu da eklenir.
    """
    img = img.convert("RGBA")
    w, h = img.size
    for d in (w, h):
        if d & (d - 1):
            raise ValueError(f"doku boyutu 2'nin kuvveti olmali: {w}x{h}")
    # R,G,B,A -> little-endian A8R8G8B8 = bayt sirasi B,G,R,A
    b, g, r, a = img.split()[2], img.split()[1], img.split()[0], img.split()[3]
    from PIL import Image
    bgra = Image.merge("RGBA", (b, g, r, a)).tobytes()
    with open(path, "wb") as f:
        _w_str(f, name)
        f.write(b"NTF" + bytes([3]))
        f.write(struct.pack("<iiIi", w, h, D3DFMT_A8R8G8B8, 0))
        f.write(bgra)
        if w >= 512 and h >= 512:
            f.write(b"\0" * (256 * 256 * 2))


def load_dxt(path: str):
    """.dxt -> PIL RGBA. Sikistirmasiz (A8R8G8B8/X8R8G8B8/A4R4G4B4/A1R5G5B5) ve DXT1/3/5 (mipmap'siz)."""
    import numpy as np
    from PIL import Image
    with open(path, "rb") as f:
        _r_str(f)
        magic = f.read(4)
        if magic[:3] != b"NTF":
            raise ValueError("NTF degil")
        w, h, fmt, mip = struct.unpack("<iiIi", f.read(16))
        if fmt in (D3DFMT_A8R8G8B8, D3DFMT_X8R8G8B8):
            raw = np.frombuffer(f.read(w * h * 4), np.uint8).reshape(h, w, 4)
            b, g, r, a = raw[..., 0], raw[..., 1], raw[..., 2], raw[..., 3]
            if fmt == D3DFMT_X8R8G8B8:
                a = np.full_like(a, 255)
            return Image.fromarray(np.dstack([r, g, b, a]), "RGBA")
        if fmt in (D3DFMT_A4R4G4B4, D3DFMT_A1R5G5B5):
            raw = np.frombuffer(f.read(w * h * 2), "<u2").reshape(h, w).astype(np.uint32)
            if fmt == D3DFMT_A4R4G4B4:
                a = ((raw >> 12) & 0xF) * 17; r = ((raw >> 8) & 0xF) * 17
                g = ((raw >> 4) & 0xF) * 17; b = (raw & 0xF) * 17
            else:
                a = ((raw >> 15) & 1) * 255; r = ((raw >> 10) & 0x1F) * 255 // 31
                g = ((raw >> 5) & 0x1F) * 255 // 31; b = (raw & 0x1F) * 255 // 31
            return Image.fromarray(np.dstack([r, g, b, a]).astype(np.uint8), "RGBA")
        if fmt in (D3DFMT_DXT1, D3DFMT_DXT3, D3DFMT_DXT5):
            bs = 8 if fmt == D3DFMT_DXT1 else 16
            data = f.read((w // 4) * (h // 4) * bs)
            return _decode_bc(data, w, h, fmt)
        raise ValueError(f"desteklenmeyen format {fmt}")


def _decode_bc(data: bytes, w: int, h: int, fmt: int):
    import numpy as np
    from PIL import Image
    out = np.zeros((h, w, 4), np.uint8)
    bs = 8 if fmt == D3DFMT_DXT1 else 16
    i = 0
    for by in range(0, h, 4):
        for bx in range(0, w, 4):
            blk = data[i:i + bs]; i += bs
            alpha = np.full((4, 4), 255, np.uint8)
            if fmt == D3DFMT_DXT3:
                av = int.from_bytes(blk[:8], "little")
                for k in range(16):
                    alpha[k // 4, k % 4] = ((av >> (4 * k)) & 0xF) * 17
                blk = blk[8:]
            elif fmt == D3DFMT_DXT5:
                a0, a1 = blk[0], blk[1]
                bits = int.from_bytes(blk[2:8], "little")
                tbl = [a0, a1] + ([(a0 * (6 - j) + a1 * (j + 1)) // 7 for j in range(6)] if a0 > a1
                                  else [(a0 * (4 - j) + a1 * (j + 1)) // 5 for j in range(4)] + [0, 255])
                for k in range(16):
                    alpha[k // 4, k % 4] = tbl[(bits >> (3 * k)) & 7]
                blk = blk[8:]
            c0, c1 = struct.unpack("<HH", blk[:4])
            idx = int.from_bytes(blk[4:8], "little")

            def rgb(c):
                return ((c >> 11) * 255 // 31, ((c >> 5) & 0x3F) * 255 // 63, (c & 0x1F) * 255 // 31)
            p0, p1 = rgb(c0), rgb(c1)
            if fmt != D3DFMT_DXT1 or c0 > c1:
                pal = [p0, p1, tuple((2 * a + b) // 3 for a, b in zip(p0, p1)), tuple((a + 2 * b) // 3 for a, b in zip(p0, p1))]
                pa = [255, 255, 255, 255]
            else:
                pal = [p0, p1, tuple((a + b) // 2 for a, b in zip(p0, p1)), (0, 0, 0)]
                pa = [255, 255, 255, 0]
            for k in range(16):
                sel = (idx >> (2 * k)) & 3
                y, x = by + k // 4, bx + k % 4
                out[y, x, :3] = pal[sel]
                out[y, x, 3] = min(alpha[k // 4, k % 4], pa[sel]) if fmt == D3DFMT_DXT1 else alpha[k // 4, k % 4]
    return Image.fromarray(out, "RGBA")


def read_dxt_header(path: str) -> dict:
    with open(path, "rb") as f:
        name = _r_str(f)
        magic = f.read(4)
        w, h, fmt, mip = struct.unpack("<iiIi", f.read(16))
    return {"name": name, "magic": magic, "width": w, "height": h, "format": fmt, "mipmap": mip}


if __name__ == "__main__":
    import sys
    for p in sys.argv[1:]:
        if p.lower().endswith(".dxt"):
            print(read_dxt_header(p))
            load_dxt(p).save(p.rsplit(".", 1)[0] + ".png")
        else:
            print(dump(p))
