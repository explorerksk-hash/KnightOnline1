# uitool — Open-KO UI (.uif / .dxt) araçları

Windows'taki UIE aracına gerek kalmadan, Python ile oyun arayüzü dosyası üretir.

- `n3ui.py` — .uif okuyucu/yazıcı (format sürümü 1264+) ve sıkıştırmasız .dxt yazıcı.
  `python n3ui.py dosya.uif` ağacı yazdırır; `python n3ui.py doku.dxt` başlığı gösterir.
- `build_login_a.py` — "Login A" tasarımını üretir:
  `UI/Login_OpenKO.uif`, `UI/openko_login_bg.dxt`, `UI/openko_login_atlas.dxt` + önizleme PNG'leri.

## Kurulum / çalıştırma (PC)

```bat
pip install pillow numpy
cd P:\Projeler\openko\tools\uitool
python build_login_a.py --out P:\Projeler\openko\assets\Client
```

İstemci (`GameProcLogIn_1298.cpp`) `assets\Client\UI\Login_OpenKO.uif` varsa onu,
yoksa ui.tbl'deki klasik intro'yu yükler. Dosyayı silmek eski ekrana döndürür.

Yazı tipleri `fonts/` altında (Cinzel, Noto Sans — SIL OFL).

## HUD

`build_hud_a.py` — durum çubuğu + mini harita (`StateBar_OpenKO.uif`), hedef çubuğu
(`TargetBar_OpenKO.uif`) ve hotkey barı (`HotKey_OpenKO.uif`) + `openko_hud_atlas.dxt`.
İstemci `CGameBase::OpenKOUIFile()` ile `UI\<Ad>_OpenKO.uif` varsa onu yükler.
Sohbet/komut barı şimdilik orijinal dosyalarda (bkz. yol haritası).

Not: motor çocukları ters sırada çizer; `n3ui` bunu gizler — `add()` sırası = alttan üste.
