"""1920x1080 ekranda orijinal HUD'i verilen olceklerde gosterir."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw
from n3ui import UIBase
import render_uif as R

AR = '/mnt/user-data/uploads/Projeler/openko/assets/Client'
A = AR + '/UI_us'
W, H = 1920, 1080


def frame(scale):
    bg = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    d = ImageDraw.Draw(bg)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(38 + 40 * t), int(46 + 34 * t), int(40 + 22 * t)))

    def put(name, x, y):
        p = os.path.join(A, name)
        if not os.path.exists(p):
            print('yok:', name); return
        root = UIBase.load(p)
        img = R.render(root, AR, scale=scale, bg=(0, 0, 0, 0))
        bg.alpha_composite(img, (int(x), int(y)))

    s = scale
    put('Ka_StateBar_us.uif', 0, 0)
    tb = UIBase.load(os.path.join(A, 'co_TargetBar_us.uif'))
    put('co_TargetBar_us.uif', (W - tb.width * s) / 2, 0)
    cm = UIBase.load(os.path.join(A, 'Ka_Cmd_us.uif'))
    put('Ka_Cmd_us.uif', (W - cm.width * s) / 2, H - cm.height * s)
    ch = UIBase.load(os.path.join(A, 'Ka_Chat_us.uif'))
    put('Ka_Chat_us.uif', 0, H - (ch.height + cm.height) * s)
    put('Ka_MsgOutput_us.uif', ch.width * s, H - (ch.height + cm.height) * s)
    hk = UIBase.load(os.path.join(A, 'Ka_HotKey_us.uif'))
    put('Ka_HotKey_us.uif', W - hk.width * s, (H - hk.height * s) / 2)
    put('Ka_Inventory_us.uif', 465 if s == 1.0 else W - 366 * s - 20, 10)

    lab = ImageDraw.Draw(bg)
    lab.rectangle([W / 2 - 170, H / 2 - 26, W / 2 + 170, H / 2 + 26], fill=(0, 0, 0, 200))
    lab.text((W / 2 - 140, H / 2 - 8), f'UI olcegi = {scale:g}x   ({W}x{H})', fill=(255, 220, 120))
    return bg


os.makedirs('out', exist_ok=True)
for s, out in ((1.0, 'out/hud_1920_scale10.png'), (1.4, 'out/hud_1920_scale14.png')):
    frame(s).convert('RGB').save(out, quality=92)
    print('yazildi', out)
