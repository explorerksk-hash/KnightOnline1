"""
build_hud_a.py - Oyun ici HUD (durum cubugu + mini harita, hedef cubugu, hotkey bari)
Login A ile ayni gorsel dilde.

Uretir:
    UI/openko_hud_atlas.dxt      512x512 atlas
    UI/StateBar_OpenKO.uif       CUIStateBar  (Progress_HP/MSP/ExpC/ExpP, Text_*, Group_MiniMap...)
    UI/TargetBar_OpenKO.uif      CUITargetBar (pro_target, text_target, Progress_HP_slow/drop/lasting)
    UI/HotKey_OpenKO.uif         CUIHotKeyDlg (Area "0".."7", String "0".."7" ve "10".."17", btn_up/btn_down)
    preview_hud.png              1024x768 onizleme

Calistir:  python build_hud_a.py --out P:/Projeler/openko/assets/Client
"""
from __future__ import annotations

import argparse
import os

from PIL import Image, ImageDraw

from n3ui import (UIArea, UIBase, UIButton, UIImage, UIProgress, UIString, hexcolor, save_dxt,
                  UISTYLE_STRING_ALIGNCENTER, UISTYLE_STRING_ALIGNLEFT, UISTYLE_STRING_ALIGNRIGHT,
                  UISTYLE_STRING_ALIGNVCENTER, UISTYLE_STRING_SINGLELINE, UISTYLE_STRING_ALIGNBOTTOM,
                  BS_NORMAL, BS_DOWN, BS_ON, BS_DISABLE)
from build_login_a import (Atlas, BG, BORDER, GOLD, GOLD_HI, GOLD_LO, MUTED, PANEL, TEXT, RED, GREEN,
                           DISABLED, GAME_FONT, HERE, W, H, cinzel, noto, rounded_box, text_sprite)

TEX = "UI\\openko_hud_atlas.dxt"
UI_AREA_TYPE_SKILL_HOTKEY = 8
IMAGETYPE_BKGND, IMAGETYPE_FRGND = 0, 1

HP = (196, 52, 46)
MP = (58, 111, 216)
POISON = (140, 70, 200)
DROP = (230, 120, 40)
LASTING = (60, 170, 120)


def bar_sprite(size, color):
    """Dikey parlaklik gecisli ilerleme cubugu dolgusu."""
    w, h = size
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h - 1)
        k = 1.18 - 0.36 * t
        c = tuple(min(255, int(v * k)) for v in color)
        d.line([(0, y), (w, y)], fill=c + (255,))
    d.line([(0, 0), (w, 0)], fill=(255, 255, 255, 70))
    return img


def slot_sprite(label):
    box = rounded_box((40, 40), (14, 15, 18, 200), outline=BORDER + (255,), radius=3)
    t = text_sprite(label, noto(9, "SemiBold"), MUTED, tracking=0.05)
    box.alpha_composite(t, (4, 3))
    return box


def glyph_button(glyph, size=(20, 20)):
    """glyph: metin ya da "up"/"down" (ucgen cizilir)."""
    out = {}
    for st, (bg, fg) in {BS_NORMAL: (PANEL, GOLD), BS_ON: (BORDER, GOLD_HI), BS_DOWN: (BG, GOLD_LO),
                         BS_DISABLE: (PANEL, DISABLED)}.items():
        box = rounded_box(size, bg + (230,), outline=BORDER + (255,), radius=3)
        if glyph in ("up", "down"):
            s = 8
            tri = Image.new("RGBA", (size[0] * s, size[1] * s), (0, 0, 0, 0))
            cx, cy = size[0] * s // 2, size[1] * s // 2
            w, h = 4 * s, 3 * s
            pts = [(cx - w, cy + h), (cx + w, cy + h), (cx, cy - h)] if glyph == "up" else \
                  [(cx - w, cy - h), (cx + w, cy - h), (cx, cy + h)]
            ImageDraw.Draw(tri).polygon(pts, fill=fg + (255,))
            box.alpha_composite(tri.resize(size, Image.LANCZOS))
        else:
            t = text_sprite(glyph, noto(12, "Bold"), fg)
            box.alpha_composite(t, ((size[0] - t.width) // 2, (size[1] - t.height) // 2))
        out[st] = box
    return out


def build(out_dir):
    ui_dir = os.path.join(out_dir, "UI")
    os.makedirs(ui_dir, exist_ok=True)
    A = Atlas((512, 512))
    A.put("sw_panel", Image.new("RGBA", (8, 8), PANEL + (215,)))
    A.put("sw_border", Image.new("RGBA", (8, 8), BORDER + (255,)))
    A.put("sw_track", Image.new("RGBA", (8, 8), (10, 11, 14, 230)))
    A.put("bar_hp", bar_sprite((192, 12), HP))
    A.put("bar_mp", bar_sprite((192, 12), MP))
    A.put("bar_exp", bar_sprite((192, 8), GOLD))
    A.put("bar_expc", bar_sprite((192, 4), GOLD_LO))
    A.put("bar_poison", bar_sprite((192, 12), POISON))
    A.put("bar_drop", bar_sprite((192, 12), DROP))
    A.put("bar_lasting", bar_sprite((192, 12), LASTING))
    A.put("bar_target", bar_sprite((296, 10), HP))
    A.put("lbl_hp", text_sprite("HP", noto(10, "Bold"), GOLD, tracking=0.08))
    A.put("lbl_mp", text_sprite("MP", noto(10, "Bold"), GOLD, tracking=0.08))
    A.put("lbl_exp", text_sprite("EXP", noto(10, "Bold"), GOLD, tracking=0.08))
    A.put("lbl_target", text_sprite("HEDEF", noto(9, "SemiBold"), MUTED, tracking=0.18))
    for i in range(8):
        A.put(f"slot_{i}", slot_sprite(f"F{i + 1}"))
    for st, sp in glyph_button("+").items():
        A.put(f"btn_zin_{st}", sp)
    for st, sp in glyph_button("−").items():
        A.put(f"btn_zout_{st}", sp)
    for st, sp in glyph_button("up", (24, 18)).items():
        A.put(f"btn_up_{st}", sp)
    for st, sp in glyph_button("down", (24, 18)).items():
        A.put(f"btn_down_{st}", sp)
    A.put("map_ph", Image.new("RGBA", (8, 8), (20, 22, 27, 255)))

    save_dxt(os.path.join(ui_dir, "openko_hud_atlas.dxt"), A.img)
    A.img.save(os.path.join(out_dir, "openko_hud_atlas.png"))

    def img(id_, name, x, y, w=None, h=None, **kw):
        return A.image(id_, name, x, y, w, h, tex=TEX, **kw)

    def panel(parent, x, y, w, h):
        parent.add(img("img_fill", "sw_panel", x, y, w, h))
        parent.add(img("img_bd_t", "sw_border", x, y, w, 1))
        parent.add(img("img_bd_b", "sw_border", x, y + h - 1, w, 1))
        parent.add(img("img_bd_l", "sw_border", x, y, 1, h))
        parent.add(img("img_bd_r", "sw_border", x + w - 1, y, 1, h))

    def string(id_, x, y, w, h, size=11, color=TEXT, bold=False, align="left", valign="vcenter"):
        st = UISTYLE_STRING_SINGLELINE
        st |= {"left": UISTYLE_STRING_ALIGNLEFT, "center": UISTYLE_STRING_ALIGNCENTER,
               "right": UISTYLE_STRING_ALIGNRIGHT}[align]
        st |= {"vcenter": UISTYLE_STRING_ALIGNVCENTER, "bottom": UISTYLE_STRING_ALIGNBOTTOM}[valign]
        return UIString(id=id_, region=(x, y, x + w, y + h), style=st, font=GAME_FONT, font_height=size,
                        bold=bold, color=hexcolor("%02x%02x%02x" % color))

    def progress(id_, bar, x, y, w, h, track=True):
        p = UIProgress(id=id_, region=(x, y, x + w, y + h))
        if track:
            p.add(img("img_bk", "sw_track", x, y, w, h, reserved=IMAGETYPE_BKGND))
        else:
            # gorunmez arka plan (ust uste binen zehir/dusus cubuklari icin)
            p.add(UIImage(id="img_bk", region=(x, y, x + w, y + h), tex="", reserved=IMAGETYPE_BKGND))
        p.add(img("img_fr", bar, x, y, w, h, reserved=IMAGETYPE_FRGND))
        return p

    def button(id_, prefix, x, y):
        b = UIButton(id=id_)
        w, h = A.wh(f"{prefix}_{BS_NORMAL}")
        b.region = (x, y, x + w, y + h)
        b.click = b.region
        for st in (BS_NORMAL, BS_DOWN, BS_ON, BS_DISABLE):
            b.add(img(f"img_{st}", f"{prefix}_{st}", x, y, w, h, reserved=st))
        return b

    # ------------------------------------------------ StateBar (sol ust)
    sb = UIBase(id="StateBar_OpenKO", region=(0, 0, 320, 100))
    panel(sb, 8, 8, 304, 84)
    BX, BW = 48, 192
    sb.add(img("img_lbl_hp", "lbl_hp", 20, 19))
    sb.add(progress("Progress_HP", "bar_hp", BX, 18, BW, 12))
    sb.add(progress("Progress_HP_slow", "bar_poison", BX, 18, BW, 12, track=False))
    sb.add(progress("Progress_HP_drop", "bar_drop", BX, 18, BW, 12, track=False))
    sb.add(progress("Progress_HP_lasting", "bar_lasting", BX, 18, BW, 12, track=False))
    sb.add(string("Text_HP", BX, 17, BW, 14, size=10, bold=True, align="center"))
    sb.add(img("img_lbl_mp", "lbl_mp", 20, 39))
    sb.add(progress("Progress_MSP", "bar_mp", BX, 38, BW, 12))
    sb.add(string("Text_MSP", BX, 37, BW, 14, size=10, bold=True, align="center"))
    sb.add(img("img_lbl_exp", "lbl_exp", 20, 57))
    sb.add(progress("Progress_ExpP", "bar_exp", BX, 58, BW, 8))
    sb.add(progress("Progress_ExpC", "bar_expc", BX, 68, BW, 4))
    sb.add(string("Text_ExpP", BX + BW + 6, 56, 60, 14, size=10, color=MUTED))
    sb.add(string("string_fps", BX + BW + 6, 17, 60, 14, size=10, color=MUTED, align="right"))
    sb.add(string("SystemTime", BX + BW + 6, 37, 60, 14, size=10, color=MUTED, align="right"))
    sb.add(string("Text_Position", 20, 76, 160, 12, size=10, color=MUTED))
    sb.add(string("Text_Version", 200, 76, 100, 12, size=10, color=MUTED, align="right"))
    mm = UIBase(id="Group_MiniMap", region=(8, 100, 180, 272))
    panel(mm, 8, 100, 172, 172)
    mm.add(UIImage(id="Img_MiniMap", region=(12, 104, 176, 268), tex="", uv=(0, 0, 1, 1)))
    mm.add(button("Btn_ZoomIn", "btn_zin", 154, 246))
    mm.add(button("Btn_ZoomOut", "btn_zout", 132, 246))
    sb.add(mm)
    sb.save(os.path.join(ui_dir, "StateBar_OpenKO.uif"))

    # ------------------------------------------------ TargetBar (ust orta; kod X'i ortalar)
    tb = UIBase(id="TargetBar_OpenKO", region=(0, 0, 320, 56))
    panel(tb, 0, 8, 320, 44)
    tb.add(img("img_lbl_target", "lbl_target", 12, 14))
    tb.add(string("text_target", 48, 12, 260, 14, size=12, bold=True, align="center"))
    tb.add(progress("pro_target", "bar_target", 12, 32, 296, 10))
    tb.add(progress("Progress_HP_slow", "bar_poison", 12, 32, 296, 10, track=False))
    tb.add(progress("Progress_HP_drop", "bar_drop", 12, 32, 296, 10, track=False))
    tb.add(progress("Progress_HP_lasting", "bar_lasting", 12, 32, 296, 10, track=False))
    tb.save(os.path.join(ui_dir, "TargetBar_OpenKO.uif"))

    # ------------------------------------------------ HotKey (alt orta)
    SLOT, GAP = 40, 4
    hk_w = 8 * (SLOT + GAP) + 4 + 28
    hk = UIBase(id="HotKey_OpenKO", region=(0, 0, hk_w, 76))
    panel(hk, 0, 20, hk_w, 56)
    for i in range(8):
        x = 8 + i * (SLOT + GAP)
        y = 28
        hk.add(img(f"img_slot{i}", f"slot_{i}", x, y))
        hk.add(UIArea(id=str(i), region=(x, y, x + SLOT, y + SLOT), area_type=UI_AREA_TYPE_SKILL_HOTKEY))
        hk.add(string(str(i), x, y + SLOT - 14, SLOT - 3, 12, size=10, bold=True, align="right", valign="bottom"))
        hk.add(string(str(i + 10), x - 40, 0, SLOT + 80, 16, size=11, color=GOLD, align="center"))
    hk.add(button("btn_up", "btn_up", hk_w - 30, 28))
    hk.add(button("btn_down", "btn_down", hk_w - 30, 50))
    hk.save(os.path.join(ui_dir, "HotKey_OpenKO.uif"))

    preview(A, sb, tb, hk, os.path.join(out_dir, "preview_hud.png"))
    return ui_dir


def preview(A, sb, tb, hk, path):
    """Oyun sahnesi yerine koyu bir zemin uzerinde HUD'in yerlesimi."""
    canvas = Image.new("RGBA", (W, H), (36, 40, 34, 255))
    d = ImageDraw.Draw(canvas)
    for y in range(H):  # basit "arazi" gecisi
        c = (30 + y * 20 // H, 34 + y * 24 // H, 30 + y * 12 // H, 255)
        d.line([(0, y), (W, y)], fill=c)
    f11 = noto(11, "Bold")
    f10 = noto(10)

    def draw(node, ox=0, oy=0, values=None):
        values = values or {}
        if isinstance(node, UIImage) and node.tex:
            u0, v0, u1, v1 = node.uv
            tw, th = A.img.size
            crop = A.img.crop((round(u0 * tw), round(v0 * th), round(u1 * tw), round(v1 * th)))
            if crop.size != (node.width, node.height):
                crop = crop.resize((max(1, node.width), max(1, node.height)), Image.BILINEAR)
            canvas.alpha_composite(crop, (node.region[0] + ox, node.region[1] + oy))
        elif isinstance(node, UIImage) and node.id == "Img_MiniMap":
            d.rectangle((node.region[0] + ox, node.region[1] + oy, node.region[2] + ox, node.region[3] + oy),
                        fill=(20, 22, 27, 255))
            cx, cy = (node.region[0] + node.region[2]) // 2 + ox, (node.region[1] + node.region[3]) // 2 + oy
            d.rectangle((cx - 2, cy - 2, cx + 2, cy + 2), fill=GOLD + (255,))
        elif isinstance(node, UIProgress):
            frac = values.get(node.id)
            if frac is None:
                return
            for c in node.children:
                if c.reserved == IMAGETYPE_BKGND and c.tex:
                    draw(c, ox, oy)
            for c in node.children:
                if c.reserved == IMAGETYPE_FRGND:
                    u0, v0, u1, v1 = c.uv
                    cc = UIImage(id=c.id, region=(c.region[0], c.region[1],
                                                  c.region[0] + int(c.width * frac), c.region[3]),
                                 tex=c.tex, uv=(u0, v0, u0 + (u1 - u0) * frac, v1))
                    draw(cc, ox, oy)
            return
        elif isinstance(node, UIString):
            txt = values.get(node.id)
            if txt:
                col = (node.color >> 16 & 255, node.color >> 8 & 255, node.color & 255, 255)
                fnt = f11 if node.bold else f10
                tw_ = fnt.getlength(txt)
                x = node.region[0] + ox
                if node.style & UISTYLE_STRING_ALIGNCENTER:
                    x = (node.region[0] + node.region[2]) // 2 - tw_ / 2 + ox
                elif node.style & UISTYLE_STRING_ALIGNRIGHT:
                    x = node.region[2] - tw_ + ox
                d.text((x, node.region[1] + oy + 1), txt, font=fnt, fill=col)
        elif isinstance(node, UIButton):
            for c in node.children:
                if isinstance(c, UIImage) and c.reserved == BS_NORMAL:
                    draw(c, ox, oy)
            return
        for c in node.children:
            draw(c, ox, oy, values)

    draw(sb, 0, 0, {"Progress_HP": 0.72, "Progress_MSP": 0.45, "Progress_ExpP": 0.63, "Progress_ExpC": 0.3,
                    "Text_HP": "1240 / 1720", "Text_MSP": "410 / 900", "Text_ExpP": "63.21 %",
                    "Text_Position": "512.3, 388.1", "Text_Version": "Ver. 1.298", "string_fps": "144 fps"})
    draw(tb, (W - tb.width) // 2, 0, {"pro_target": 0.55, "text_target": "Kekoon Captain"})
    draw(hk, (W - hk.width) // 2, H - hk.height - 8, {"0": "12", "3": "5", "10": ""})
    canvas.convert("RGB").save(path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "out"))
    a = ap.parse_args()
    print("yazildi:", build(a.out))
