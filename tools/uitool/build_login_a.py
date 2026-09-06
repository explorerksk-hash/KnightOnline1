"""
build_login_a.py - "Login A" tasarimini oyun icine tasir.

Uretir (cikti klasoru: --out, varsayilan ./out):
    UI/openko_login_bg.dxt     1024x1024 arka plan (ekrana gerilir)
    UI/openko_login_atlas.dxt  1024x1024  panel/buton/yazi atlasi
    UI/Login_OpenKO.uif        CUILogIn_1298'in bekledigi ID'lerle tam login ekrani
    preview.png                1024x768 onizleme (oyunun cizecegi hali)

Calistir:  python build_login_a.py --out P:/Projeler/openko/assets/Client
Gerekli:   pip install pillow numpy   (+ fonts/Cinzel.ttf, fonts/NotoSans.ttf)
"""
from __future__ import annotations

import argparse
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from n3ui import (UIBase, UIButton, UIEdit, UIImage, UIString, hexcolor, save_dxt,
                  UISTYLE_EDIT_PASSWORD, UISTYLE_STRING_ALIGNCENTER, UISTYLE_STRING_ALIGNLEFT,
                  UISTYLE_STRING_ALIGNVCENTER, UISTYLE_STRING_SINGLELINE, UISTYLE_STRING_ALIGNTOP,
                  BS_NORMAL, BS_DOWN, BS_ON, BS_DISABLE)

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(HERE, "fonts")

# ------------------------------------------------------------------ tasarim sistemi
BG = (14, 15, 18)
PANEL = (24, 26, 32)
BORDER = (42, 46, 56)
GOLD = (201, 162, 39)
GOLD_HI = (224, 185, 58)
GOLD_LO = (168, 134, 31)
TEXT = (232, 230, 223)
MUTED = (154, 160, 171)
RED = (184, 54, 43)
GREEN = (143, 191, 60)
DISABLED = (70, 74, 84)

TEX_BG = "UI\\openko_login_bg.dxt"
TEX_ATLAS = "UI\\openko_login_atlas.dxt"
GAME_FONT = "Segoe UI"

W, H = 1024, 768  # temel yerlesim; kod img_bg'yi gercek cozunurluge gerer


def font(name: str, size: int, weight: str | None = None) -> ImageFont.FreeTypeFont:
    path = os.path.join(FONT_DIR, name)
    f = ImageFont.truetype(path, size)
    if weight:
        try:
            f.set_variation_by_name(weight)
        except Exception:
            pass
    return f


def cinzel(size, weight="Bold"):
    return font("Cinzel.ttf", size, weight)


def noto(size, weight="Regular"):
    return font("NotoSans.ttf", size, weight)


# ------------------------------------------------------------------ cizim yardimcilari
def text_sprite(txt, fnt, color, tracking=0.0, pad=4, glow=None, shadow=None):
    """Harf araligi destekli, kirpilmis RGBA yazi sprite'i."""
    scale = 1
    # olcum
    widths = [fnt.getlength(ch) for ch in txt]
    tr = tracking * fnt.size
    total = sum(widths) + tr * (len(txt) - 1)
    asc, desc = fnt.getmetrics()
    w = int(math.ceil(total)) + pad * 2 + (12 if glow else 0)
    h = asc + desc + pad * 2 + (12 if glow else 0)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x0 = pad + (6 if glow else 0)
    y0 = pad + (6 if glow else 0)

    def draw_run(draw, ox, oy, col):
        x = ox
        for ch, cw in zip(txt, widths):
            draw.text((x, oy), ch, font=fnt, fill=col)
            x += cw + tr

    if glow:
        g = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw_run(ImageDraw.Draw(g), x0, y0, glow)
        g = g.filter(ImageFilter.GaussianBlur(6))
        img.alpha_composite(g)
    if shadow:
        s = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw_run(ImageDraw.Draw(s), x0, y0 + 2, shadow)
        s = s.filter(ImageFilter.GaussianBlur(2))
        img.alpha_composite(s)
    draw_run(d, x0, y0, color + (255,))
    bbox = img.getbbox()
    return img.crop(bbox) if bbox else img


def rounded_box(size, fill, outline=None, radius=3, outline_w=1):
    w, h = size
    s = 4  # supersample
    img = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, w * s - 1, h * s - 1), radius=radius * s, fill=fill,
                        outline=outline, width=outline_w * s if outline else 0)
    return img.resize((w, h), Image.LANCZOS)


def button_sprites(label, size, fnt, tracking=0.2):
    """4 durum: normal, down, on(hover), disable."""
    w, h = size
    out = {}
    for state, (bg, fg) in {
        BS_NORMAL: (GOLD, BG), BS_ON: (GOLD_HI, BG), BS_DOWN: (GOLD_LO, BG),
        BS_DISABLE: (DISABLED, (120, 124, 134)),
    }.items():
        box = rounded_box((w, h), bg + (255,), radius=3)
        t = text_sprite(label, fnt, fg, tracking=tracking)
        box.alpha_composite(t, ((w - t.width) // 2, (h - t.height) // 2 - 1))
        out[state] = box
    return out


def link_sprites(label, fnt):
    """Metin-buton: 4 durum, sadece renk degisir."""
    cols = {BS_NORMAL: GOLD, BS_ON: GOLD_HI, BS_DOWN: GOLD_LO, BS_DISABLE: DISABLED}
    sp = {k: text_sprite(label, fnt, c) for k, c in cols.items()}
    # ayni boyuta getir
    mw = max(s.width for s in sp.values())
    mh = max(s.height for s in sp.values())
    for k, s in sp.items():
        canvas = Image.new("RGBA", (mw, mh), (0, 0, 0, 0))
        canvas.alpha_composite(s, (0, 0))
        sp[k] = canvas
    return sp


def field_sprite(size, icon):
    w, h = size
    box = rounded_box((w, h), (14, 15, 18, 180), outline=BORDER + (255,), radius=3)
    s = 4
    ic = Image.new("RGBA", (16 * s, 16 * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(ic)
    lw = int(1.8 * s)
    col = MUTED + (255,)
    if icon == "user":
        d.ellipse((8 * s, 2 * s, 16 * s, 10 * s), outline=col, width=lw)
        d.arc((2 * s, 10 * s, 22 * s, 30 * s), 180, 360, fill=col, width=lw)
    else:  # lock
        d.rounded_rectangle((3 * s, 8 * s, 15 * s, 15 * s), radius=1 * s, outline=col, width=lw)
        d.arc((5 * s, 2 * s, 13 * s, 12 * s), 180, 360, fill=col, width=lw)
    ic = ic.resize((16, 16), Image.LANCZOS)
    box.alpha_composite(ic, (16, (h - 16) // 2))
    return box


def emblem_sprite(kind):
    """Soyut ulus amblemi: Karus (kirmizi) / El Morad (altin)."""
    s = 4
    W_, H_ = 160, 280
    img = Image.new("RGBA", (W_ * s, H_ * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    col = (RED if kind == "karus" else GOLD) + (150,)
    lw = int(1.5 * s)

    def P(x, y):
        return (x / 220 * W_ * s, y / 380 * H_ * s)

    shield = [P(110, 10), P(200, 60), P(200, 200), P(190, 270), P(160, 330), P(110, 370),
              P(60, 330), P(30, 270), P(20, 200), P(20, 60)]
    d.polygon(shield, outline=col, width=lw)
    inner = [P(110, 60), P(160, 90), P(160, 200), P(150, 250), P(130, 290), P(110, 315),
             P(90, 290), P(70, 250), P(60, 200), P(60, 90)]
    d.polygon(inner, outline=col[:3] + (90,), width=lw)
    if kind == "karus":
        d.line([P(110, 110), P(110, 270)], fill=col, width=lw + s)
        d.line([P(75, 190), P(145, 190)], fill=col, width=lw + s)
    else:
        d.ellipse([P(40, 120), P(180, 260)], outline=col[:3] + (90,), width=lw)
        star = [P(110, 120), P(128, 172), P(184, 172), P(139, 205), P(156, 258), P(110, 226),
                P(64, 258), P(81, 205), P(36, 172), P(92, 172)]
        d.polygon(star, outline=col, width=lw + 1)
    return img.resize((W_, H_), Image.LANCZOS)


def arrow_sprite():
    s = 8
    img = Image.new("RGBA", (10 * s, 12 * s), (0, 0, 0, 0))
    ImageDraw.Draw(img).polygon([(1 * s, 1 * s), (9 * s, 6 * s), (1 * s, 11 * s)], fill=GOLD + (255,))
    return img.resize((10, 12), Image.LANCZOS)


def background_image():
    """CSS'teki radial-gradient sahnesinin birebir raster hali (1024x768 -> 1024x1024 doku)."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    fx, fy = xx / W, yy / H

    def radial(cx, cy, rx, ry, color, alpha, fade=0.65):
        dist = np.sqrt(((fx - cx) / rx) ** 2 + ((fy - cy) / ry) ** 2)
        a = np.clip(1.0 - dist / fade, 0, 1) * alpha
        return np.array(color, np.float32)[None, None, :], a[..., None]

    # dikey taban gecisi
    stops = [(0.0, (11, 12, 15)), (0.55, (20, 22, 27)), (1.0, (14, 15, 18))]
    img = np.zeros((H, W, 3), np.float32)
    for i in range(len(stops) - 1):
        (p0, c0), (p1, c1) = stops[i], stops[i + 1]
        t = np.clip((fy - p0) / (p1 - p0), 0, 1)[..., None]
        m = ((fy >= p0) & (fy <= p1))[..., None]
        img = np.where(m, np.array(c0, np.float32) * (1 - t) + np.array(c1, np.float32) * t, img)
    for (c, a) in [radial(0.5, 1.0, 0.7, 0.4, (30, 33, 40), 0.9, 0.7),
                   radial(0.10, 0.55, 0.45, 0.6, RED, 0.35),
                   radial(0.90, 0.55, 0.45, 0.6, GOLD, 0.30)]:
        img = img * (1 - a) + c * a
    # ufuk cizgisi
    hy = int(H * 0.62)
    line = np.clip(1 - np.abs(fx - 0.5) * 2, 0, 1) * 0.18
    img[hy] = img[hy] * (1 - line[hy][:, None]) + np.array(TEXT, np.float32) * line[hy][:, None]
    # vinyet
    dist = np.sqrt(((fx - 0.5) / 0.7) ** 2 + ((fy - 0.45) / 0.7) ** 2)
    v = np.clip((dist - 0.4) / 0.6, 0, 1) * 0.85
    img = img * (1 - v[..., None]) + np.array((5, 6, 8), np.float32) * v[..., None]

    tex = Image.new("RGBA", (1024, 1024), BG + (255,))
    tex.paste(Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert("RGBA"), (0, 0))
    return tex


# ------------------------------------------------------------------ atlas paketleyici
class Atlas:
    def __init__(self, size=(1024, 1024)):
        self.img = Image.new("RGBA", size, (0, 0, 0, 0))
        self.size = size
        self.x = self.y = self.shelf_h = 0
        self.rects: dict[str, tuple] = {}

    def put(self, name, sprite, pad=2):
        w, h = sprite.size
        if self.x + w + pad > self.size[0]:
            self.x, self.y, self.shelf_h = 0, self.y + self.shelf_h + pad, 0
        if self.y + h + pad > self.size[1]:
            raise RuntimeError(f"atlas doldu: {name}")
        self.img.alpha_composite(sprite, (self.x, self.y))
        self.rects[name] = (self.x, self.y, w, h)
        self.x += w + pad
        self.shelf_h = max(self.shelf_h, h)
        return name

    def uv(self, name):
        x, y, w, h = self.rects[name]
        return (x / self.size[0], y / self.size[1], (x + w) / self.size[0], (y + h) / self.size[1])

    def wh(self, name):
        return self.rects[name][2:]

    def image(self, id_, name, x, y, w=None, h=None, tex=TEX_ATLAS, **kw):
        sw, sh = self.wh(name)
        w = w or sw
        h = h or sh
        return UIImage(id=id_, region=(x, y, x + w, y + h), tex=tex, uv=self.uv(name), **kw)


# ------------------------------------------------------------------ ana insa
def build(out_dir: str):
    ui_dir = os.path.join(out_dir, "UI")
    os.makedirs(ui_dir, exist_ok=True)
    A = Atlas()

    # --- sprite'lar
    A.put("sw_panel", Image.new("RGBA", (8, 8), PANEL + (220,)))
    A.put("sw_border", Image.new("RGBA", (8, 8), BORDER + (255,)))
    A.put("sw_row", Image.new("RGBA", (8, 8), (14, 15, 18, 120)))
    A.put("sw_bar", Image.new("RGBA", (8, 8), GOLD + (230,)))
    A.put("sw_dot", rounded_box((8, 8), GREEN + (255,), radius=4))

    A.put("title", text_sprite("OPEN-KO", cinzel(54, "Bold"), TEXT, tracking=0.3,
                               glow=(0, 0, 0, 160), shadow=(0, 0, 0, 200)))
    A.put("subtitle", text_sprite("KARUS  ·  EL MORAD  ·  MORADON", noto(11, "Medium"), MUTED, tracking=0.18))
    A.put("h_login", text_sprite("GİRİŞ", cinzel(18, "Bold"), TEXT, tracking=0.12))
    A.put("h_login_sub", text_sprite("Hesabınızla oturum açın", noto(13), MUTED))
    A.put("lbl_id", text_sprite("HESAP", noto(11, "Medium"), MUTED, tracking=0.18))
    A.put("lbl_pw", text_sprite("ŞİFRE", noto(11, "Medium"), MUTED, tracking=0.18))
    A.put("field_id", field_sprite((364, 44), "user"))
    A.put("field_pw", field_sprite((364, 44), "lock"))
    for st, sp in button_sprites("GİRİŞ YAP", (364, 52), cinzel(17, "Bold"), 0.24).items():
        A.put(f"btn_login_{st}", sp)
    A.put("txt_noacc", text_sprite("Hesabın yok mu?", noto(13), MUTED))
    for st, sp in link_sprites("Kayıt ol", noto(13, "SemiBold")).items():
        A.put(f"lnk_join_{st}", sp)
    for st, sp in link_sprites("Ayarlar", noto(12, "Medium")).items():
        A.put(f"lnk_opt_{st}", sp)
    for st, sp in link_sprites("Çıkış", noto(12, "Medium")).items():
        A.put(f"lnk_exit_{st}", sp)
    A.put("footer", text_sprite("Open-KO  ·  1.298 tabanlı özgür sunucu", noto(12), MUTED))
    A.put("emblem_karus", emblem_sprite("karus"))
    A.put("emblem_elmorad", emblem_sprite("elmorad"))

    A.put("h_server", text_sprite("SUNUCU SEÇ", cinzel(18, "Bold"), TEXT, tracking=0.12))
    A.put("h_server_sub", text_sprite("Yukarı / aşağı ile seç, Enter ile bağlan", noto(13), MUTED))
    A.put("arrow", arrow_sprite())
    for st, sp in button_sprites("BAĞLAN", (364, 48), cinzel(16, "Bold"), 0.24).items():
        A.put(f"btn_connect_{st}", sp)

    A.put("h_notice", text_sprite("DUYURU", cinzel(18, "Bold"), TEXT, tracking=0.12))
    for st, sp in button_sprites("TAMAM", (160, 40), cinzel(14, "Bold"), 0.2).items():
        A.put(f"btn_ok_{st}", sp)

    save_dxt(os.path.join(ui_dir, "openko_login_atlas.dxt"), A.img)
    A.img.save(os.path.join(out_dir, "openko_login_atlas.png"))
    bg = background_image()
    save_dxt(os.path.join(ui_dir, "openko_login_bg.dxt"), bg)

    # --- yardimcilar
    def panel(parent, x, y, w, h):
        parent.add(A.image("img_fill", "sw_panel", x, y, w, h))
        parent.add(A.image("img_bd_t", "sw_border", x, y, w, 1))
        parent.add(A.image("img_bd_b", "sw_border", x, y + h - 1, w, 1))
        parent.add(A.image("img_bd_l", "sw_border", x, y, 1, h))
        parent.add(A.image("img_bd_r", "sw_border", x + w - 1, y, 1, h))

    def button(id_, prefix, x, y, w=None, h=None):
        b = UIButton(id=id_)
        sw, sh = A.wh(f"{prefix}_{BS_NORMAL}")
        w, h = w or sw, h or sh
        b.region = (x, y, x + w, y + h)
        b.click = b.region
        for st in (BS_NORMAL, BS_DOWN, BS_ON, BS_DISABLE):
            b.add(A.image(f"img_{st}", f"{prefix}_{st}", x, y, w, h, reserved=st))
        return b

    def string(id_, x, y, w, h, size=13, color=TEXT, bold=False, single=True, align="left"):
        st = UISTYLE_STRING_SINGLELINE if single else 0
        st |= {"left": UISTYLE_STRING_ALIGNLEFT, "center": UISTYLE_STRING_ALIGNCENTER}[align]
        st |= UISTYLE_STRING_ALIGNVCENTER if single else UISTYLE_STRING_ALIGNTOP
        return UIString(id=id_, region=(x, y, x + w, y + h), style=st, font=GAME_FONT,
                        font_height=size, bold=bold, color=hexcolor("%02x%02x%02x" % color))

    def edit(id_, x, y, w, h, password=False):
        e = UIEdit(id=id_, region=(x, y, x + w, y + h),
                   style=UISTYLE_EDIT_PASSWORD if password else 0)
        e.add(string("str", x, y, w, h, size=14, color=TEXT))
        return e

    # --- kok
    root = UIBase(id="Login_OpenKO", region=(0, 0, W, H))
    root.add(A.image("img_bg", "title", 0, 0, W, H, tex=TEX_BG))
    root.find("img_bg").uv = (0.0, 0.0, 1.0, H / 1024)
    tw, th = A.wh("title")
    root.add(A.image("img_title", "title", (W - tw) // 2, 84))
    sw_, sh_ = A.wh("subtitle")
    root.add(A.image("img_subtitle", "subtitle", (W - sw_) // 2, 84 + th + 10))
    root.add(A.image("img_emblem_l", "emblem_karus", 96, 240))
    root.add(A.image("img_emblem_r", "emblem_elmorad", W - 96 - 160, 240))
    root.add(A.image("img_footer", "footer", 32, H - 40))

    # --- Group_LogIn (420x392)
    PW_, PH_ = 420, 392
    px, py = (W - PW_) // 2, 250
    g = UIBase(id="Group_LogIn", region=(px, py, px + PW_, py + PH_))
    panel(g, px, py, PW_, PH_)
    g.add(A.image("img_h", "h_login", px + 28, py + 22))
    g.add(A.image("img_h_sub", "h_login_sub", px + 28, py + 50))
    g.add(A.image("img_lbl_id", "lbl_id", px + 28, py + 88))
    g.add(A.image("img_field_id", "field_id", px + 28, py + 106))
    g.add(edit("Edit_ID", px + 72, py + 108, 308, 40))
    g.add(A.image("img_lbl_pw", "lbl_pw", px + 28, py + 166))
    g.add(A.image("img_field_pw", "field_pw", px + 28, py + 184))
    g.add(edit("Edit_PW", px + 72, py + 186, 308, 40, password=True))
    g.add(button("btn_ok", "btn_login", px + 28, py + 250))
    nw, nh = A.wh("txt_noacc")
    jw, jh = A.wh(f"lnk_join_{BS_NORMAL}")
    total = nw + 6 + jw
    sx = px + (PW_ - total) // 2
    g.add(A.image("img_noacc", "txt_noacc", sx, py + 318))
    g.add(button("btn_homepage", "lnk_join", sx + nw + 6, py + 318))
    g.add(A.image("img_div", "sw_border", px + 28, py + 352, PW_ - 56, 1))
    g.add(button("btn_option", "lnk_opt", px + 28, py + 364))
    ew, eh = A.wh(f"lnk_exit_{BS_NORMAL}")
    g.add(button("btn_cancel", "lnk_exit", px + PW_ - 28 - ew, py + 364))
    root.add(g)

    # --- premium yazisi (sunucu listesiyle birlikte gorunur)
    root.add(string("premium", (W - 400) // 2, H - 70, 400, 20, size=12, color=MUTED, align="center"))

    # --- Group_ServerList_01 (420x380)
    SW_, SH_ = 420, 380
    sx_, sy_ = (W - SW_) // 2, (H - SH_) // 2
    s = UIBase(id="Group_ServerList_01", region=(sx_, sy_, sx_ + SW_, sy_ + SH_))
    panel(s, sx_, sy_, SW_, SH_)
    s.add(A.image("img_h", "h_server", sx_ + 28, sy_ + 22))
    s.add(A.image("img_h_sub", "h_server_sub", sx_ + 28, sy_ + 52))
    ROW_H, ROWS_VISIBLE = 26, 8
    for i in range(20):
        ry = sy_ + 80 + i * ROW_H
        rx = sx_ + 28
        row = UIBase(id=f"server_{i + 1}", region=(rx, ry, rx + 364, ry + ROW_H))
        row.add(A.image("img_row", "sw_row", rx, ry, 364, ROW_H))
        row.add(string("List_Server", rx + 28, ry, 200, ROW_H, size=14, color=TEXT))
        for j in range(12):  # yogunluk cubuklari "1".."12"
            bx = rx + 236 + j * 10
            row.add(A.image(str(j + 1), "sw_bar", bx, ry + 8, 6, 10))
        s.add(row)
        s.add(A.image(f"img_arrow{i + 1}", "arrow", rx + 8, ry + 7))
    s.add(button("Btn_Connect", "btn_connect", sx_ + 28, sy_ + 80 + ROWS_VISIBLE * ROW_H + 20))
    root.add(s)

    # --- Duyuru gruplari
    def notice(idx, n_blocks):
        NW_ = 420 if n_blocks == 1 else (480 if n_blocks == 2 else 520)
        block_h = 120
        NH_ = 60 + n_blocks * block_h + 20 + 40 + 30
        nx, ny = (W - NW_) // 2, (H - NH_) // 2
        n = UIBase(id=f"Group_Notice_{idx}", region=(nx, ny, nx + NW_, ny + NH_))
        panel(n, nx, ny, NW_, NH_)
        n.add(A.image("img_h", "h_notice", nx + 28, ny + 22))
        for b in range(n_blocks):
            by = ny + 60 + b * block_h
            n.add(string(f"text_notice_name_{b + 1:02d}", nx + 28, by, NW_ - 56, 20, size=14, color=GOLD, bold=True))
            n.add(string(f"text_notice_{b + 1:02d}", nx + 28, by + 26, NW_ - 56, block_h - 32, size=13,
                         color=TEXT, single=False))
        n.add(button("btn_ok", "btn_ok", nx + (NW_ - 160) // 2, ny + NH_ - 30 - 40))
        return n

    root.add(notice(1, 1), notice(2, 2), notice(3, 3))

    uif_path = os.path.join(ui_dir, "Login_OpenKO.uif")
    root.save(uif_path)

    # --- onizleme (oyunun cizecegi hali; String'ler yaklasik)
    render_preview(root, A, bg, os.path.join(out_dir, "preview_login.png"), show=("Group_LogIn",))
    render_preview(root, A, bg, os.path.join(out_dir, "preview_serverlist.png"),
                   show=("Group_ServerList_01",), fake_servers=("Ares", "Pathos"))
    return uif_path


def render_preview(root, A, bg, path, show=(), fake_servers=()):
    canvas = Image.new("RGBA", (W, H), BG + (255,))
    hidden_groups = {"Group_LogIn", "Group_ServerList_01", "Group_Notice_1", "Group_Notice_2", "Group_Notice_3"}
    ui_font = noto(14)

    def draw(node, visible=True):
        if node.id in hidden_groups and node.id not in show:
            return
        if node.id.startswith("server_"):
            idx = int(node.id.split("_")[1])
            if idx > len(fake_servers):
                return
        if node.id.startswith("img_arrow"):
            idx = int(node.id[len("img_arrow"):])
            if idx > len(fake_servers):
                return
        if isinstance(node, UIImage):
            tex = bg if node.tex == TEX_BG else A.img
            u0, v0, u1, v1 = node.uv
            tw, th = tex.size
            crop = tex.crop((round(u0 * tw), round(v0 * th), round(u1 * tw), round(v1 * th)))
            if crop.size != (node.width, node.height) and node.width > 0 and node.height > 0:
                crop = crop.resize((node.width, node.height), Image.BILINEAR)
            canvas.alpha_composite(crop, (node.region[0], node.region[1]))
        elif isinstance(node, UIString) and node.id == "List_Server":
            idx = int(node_parent_id(node).split("_")[1])
            name = fake_servers[idx - 1]
            col = GREEN if idx == 1 else TEXT
            ImageDraw.Draw(canvas).text((node.region[0], node.region[1] + 4), name, font=ui_font, fill=col + (255,))
        elif isinstance(node, UIButton):
            # sadece normal durum
            for c in node.children:
                if isinstance(c, UIImage) and c.reserved == BS_NORMAL:
                    draw(c)
            for c in node.children:
                if not isinstance(c, UIImage):
                    draw(c)
            return
        for c in node.children:
            draw(c)

    parent_of = {}

    def index(n):
        for c in n.children:
            parent_of[id(c)] = n
            index(c)

    index(root)

    def node_parent_id(n):
        return parent_of[id(n)].id

    draw(root)
    canvas.convert("RGB").save(path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "out"))
    a = ap.parse_args()
    p = build(a.out)
    print("yazildi:", p)
