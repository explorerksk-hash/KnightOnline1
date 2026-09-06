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
