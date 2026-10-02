# Maden Sistemi — Tasarım Belgesi

Durum: taslak v2 · 2 Ekim 2026 · Open-KO / CZ (zone 201)

Oyun içi "madencilik" teması üzerinden KC ekonomisi. Gerçek kripto madenciliği
yok; oyuncu kazma sallar, cevher çıkarır, cevher ya KC'ye dönüşür ya da
upgrade'de yanar.

---

## 1. Karar özeti

| Konu | Karar |
|---|---|
| Yuva sınırı | **Yok.** Damar modeli: `V(N) = min(V0 × √N, Vmax)`, oradaki herkes paylaşır |
| Cevherin kullanımı | **Çift.** Ya teslim edilip KC olur, ya upgrade/craft girdisi olarak kullanılır |
| Hesap başına günlük KC | **Tavanlı.** Madeni ne kadar tutarsan tut, günlük sınır var |
| KC havuzları | **İki ayrı.** Kazanılan KC çekilebilir; satın alınan KC yalnızca harcanır |
| Upgrade kağıdı | KC ile satılır. Ana KC lavabosu |
| Kazma | Yıpranır. **Altınla** alınır ve tamir edilir, KC ile değil |
| Ölüm cezası | Üstteki teslim edilmemiş ham cevher **yanar**, öldürene geçmez. Bakiye güvende |
| Ölüm sonrası bekleme | Yok, standart dirilme |
| Konum | CZ merkezi — iki üsse de 391 birim, eşit mesafede |

---

## 2. Oyun mekaniği

**Kazma.** Oyuncu maden alanında kazma kullanır. Her vuruş dayanıklılıktan
düşer. Kazma kırılırsa madencilik durur; üsse dönüp altınla tamir ettirir.

**Ham cevher.** Kazma doğrudan KC vermez, çantaya **ham cevher** yazar. Cevher
bağlıdır (bound) — takas edilemez, depoya konamaz, ölünce yanar.

**İki çıkış yolu.** Oyuncu cevherle ne yapacağına kendisi karar verir:

1. **Teslim** → üssündeki maden NPC'sine verir, KC'ye dönüşür, bakiyeye yazılır
2. **Kullan** → yüksek seviye upgrade ve craft'ta girdi olarak harcar

Bu seçim ekonominin kendi kendini dengeleme mekanizmasıdır. KC kuru kalırsa
oyuncular cevheri upgrade'e kaydırır, cevher değerlenir, hazineden para
çıkmaz. Cevher bol olursa teslim artar. Denge oyuncuların kararıyla kurulur.

**Ölüm.** Maden alanında ölürsen üstündeki teslim edilmemiş cevher yok olur.
Bakiyendeki KC'ye dokunulmaz. Öldüren cevheri almaz — ödülü madenin kendisi.

Ne kadar çok cevher taşırsan o kadar çok kaybedersin, ama teslim için üsse
yürümek zorundasın. "Ne zaman döneyim" kararı oyunun kendisi olur.

---

## 3. Üretim formülü

```
V(N) = min( V0 × √N , Vmax )        kişi başı saatlik = V(N) / N
```

`N` = o anda maden alanında aktif kazan oyuncu sayısı.

### Neden saf paylaşım değil

Saf paylaşımda (V sabit) asıl risk yüksek nüfus değil, **düşük nüfus**:
gece 04:00'te tek başına giren oyuncu bütün damarı toplar.

| N | saf paylaşım (V=208) | karekök modeli (V0=40, Vmax=250) |
|---:|---:|---:|
| 1 | 208 KC/sa — **$2.08** | 40 KC/sa — $0.40 |
| 3 | 69 KC/sa | 23 KC/sa |
| 5 | 42 KC/sa | 18 KC/sa |
| 10 | 21 KC/sa | 13 KC/sa |
| 20 | 10 KC/sa | 9 KC/sa |
| 40 | 5 KC/sa | 6 KC/sa |
| 80 | 2.6 KC/sa | 3.1 KC/sa |
| 150 | 1.4 KC/sa | 1.7 KC/sa |

Karekök modeli tek oyuncuyu beşte bire indirir, kalabalıkta saf paylaşımdan
daha cömert davranır. İkisinin de tavanı vardır.

### Hesap başına günlük tavan

Damar tavanı hazineyi korur ama **tekeli** engellemez. Para harcayıp +8 takım
basan klan madene çöker, damarın çoğunu alır, geri kalan oyuncu hiçbir şey
kazanamaz — "burada para kazanılıyor" vaadi onlar için yalan olur ve giderler.

Çözüm: hesap başına günlük KC tavanı. Madeni 24 saat tutsan da günlük sınıra
çarparsın.

```
gunluk_tavan ≈ (Vmax × 24) / hedeflenen_aktif_madenci
```

`Vmax = 250` ve hedef 40 aktif madenci ise tavan ≈ **150 KC/gün**.

Üç sorunu birden çözer:

- **Tekel:** klan madeni tutsa bile üyeleri tavana çarpar, sırayla girmek
  zorunda kalır, maden gün boyu el değiştirir
- **Çoklu client:** her hesap ayrı tavana takılır, pencere açmanın getirisi
  doğrusal değil
- **Bot:** getirisi tavanla sınırlı, yazmaya değmez

### PvP motivasyonu

Öldürdüğün her oyuncu **o anda** kazancını artırır. Yuva dolmasını beklemeye
gerek yok; her kill anında kârlı. Klanlar alanı temizlemek için organize olur.

---

## 4. İki KC havuzu

| Havuz | Kaynak | Harcanır | Çekilir |
|---|---|:---:|:---:|
| `KC_kazanilan` | maden teslimi, ödül, event | ✓ | ✓ |
| `KC_satin_alinan` | kasadan satın alma | ✓ | ✗ |

Harcama **önce satın alınandan** düşer; kazanılan havuz el değmeden durur, böylece
çekim vaadi oyuncunun gözünde gerçek kalır.

Üç faydası:

- **Arbitraj kapanır.** Satın alınan KC çekilemediği için "ucuza al, çekimden
  boz" yolu yok. Satış fiyatı ile çekim kuru arasındaki makası kollamak
  zorunda kalmazsın
- **Yükümlülük hesaplanabilir.** Hazinenin borcu yalnızca madenden basılan KC
  kadar — zaten tavanlı
- **Hukuki duruş.** KC alıp satan bir piyasa işletmiyorsun; oyun parası
  satıyorsun ve ayrıca ödül ödüyorsun

---

## 5. Hazine dengesi

Peg örneği: **1 USDT = 100 KC**. Tavan `Vmax = 250 KC/sa` ise günde en fazla
**6.000 KC = $60** basılır. Aylık en kötü senaryo **$1.800** — nüfus ne olursa
olsun aşılmaz.

Basılanın tamamı çekilmez; upgrade kağıdına giden KC yanar ve hazineden hiç
çıkmaz:

| Çekim oranı | Günlük ödeme | Aylık ödeme |
|---:|---:|---:|
| %20 | $12 | $360 |
| %40 | $24 | $720 |
| %60 | $36 | $1.080 |
| %80 | $48 | $1.440 |
| %100 | $60 | $1.800 |

Bu rakamı **maliyet değil pazarlama gideri** say: sunucuyu konuşulur yapmanın
bedeli.

**İzlenecek tek sayı:** haftalık satılan KC ÷ çekilen KC. Kalıcı olarak 1'in
altına inerse `Vmax` kısılır.

### Upgrade kağıdı — ana lavabo

KC'nin başlıca harcama yeri upgrade kağıdı. İki yönden işe yarar: gerçek
parayla KC alan oyuncu kağıdı alır (hazineye para girer), madenci kazandığı
KC'yi çekmek yerine kağıda yatırır (çekim baskısı düşer). Kağıt kullanılınca
yanar, KC onunla birlikte yok olur.

**Kağıt fiyatı artık oyunun en kritik sayısı.** Ucuz olursa herkes bir haftada
+8 olur, takım anlamını yitirir, KC talebi biter. Pahalı olursa kimse almaz.
Açılışta yüksek tut, satış verisine bakıp indir — yukarı çekmek oyuncuyu
kızdırır, aşağı çekmek sevindirir.

### Pay-to-earn tuzağı

Kazma KC ile satılmaz. 100 KC'lik kazma ömrü boyunca 150 KC kazandırırsa
herkes alır ve hazine aldığından fazlasını öder. **Kazma ve tamir sadece
altınla.** PUS'ta kazanç hızını artıran hiçbir şey satılmaz.

---

## 6. Sunucu tarafı

Mimari `openko-crypto` ayrımını korur: **oyun sunucusunda özel anahtar, RPC
veya blockchain kütüphanesi yok.** Ebenezer yalnızca bakiye değişimini ve
çekim talebini bridge'e iletir.

### Tablolar

```sql
MINE_ZONE(zoneId, centerX, centerZ, radius, V0, Vmax, oreToKc, dailyCapKc, active)
MINE_SESSION(charId, zoneId, startedAt, lastTick, oreCarried)
MINE_DAILY(charId, day, kcEarned)              -- hesap başına günlük tavan
USER_KC(charId, earned, purchased, updated)     -- iki havuz
KC_LEDGER(id, request_id UNIQUE, charId, delta, pool, reason, ref_tx, created)
```

`pool` = `earned` | `purchased`. Bakiye ledger toplamıdır; `USER_KC` yalnızca
cache. Uyuşmazlıkta ledger kazanır, gece işiyle kontrol edilir.

### Akış

1. **Maden tick'i** (ör. 10 sn): alan içindeki aktif kazan oyuncuları say →
   `V(N)` hesapla → kişi başı payı `oreCarried`'a ekle. Sayım ve dağıtım
   tamamen sunucuda; client'ın söylediği hiçbir şeye güvenilmez.
2. **Teslim:** maden NPC'si → `oreCarried × oreToKc` → `MINE_DAILY` tavan
   kontrolü → **anında** stored proc ile `KC_LEDGER`'a `+delta`
   (`pool='earned'`, reason `mine_deliver`, `request_id` = UUID).
   `WIZ_DATASAVE` döngüsüne bırakılmaz.
3. **Ölüm:** `CUser::HpChange` ölüm dalında, oyuncu maden alanındaysa
   `oreCarried = 0`. Ledger'a satır yazılmaz — cevher hiç KC olmamıştı.
4. **Harcama:** önce `purchased`, bitince `earned` havuzundan düşülür.
5. **Çekim:** yalnızca `earned` havuzundan. Bakiye ve limit kontrolü, ledger'a
   önce pending `-delta`, sonra bridge kuyruğu.

### Yeni opcode'lar

`WIZ_MINE_START` · `WIZ_MINE_STOP` · `WIZ_MINE_STATE` (kişi başı hız, N,
taşınan cevher, günlük tavana kalan — HUD'da canlı) · `WIZ_MINE_DELIVER`

---

## 7. Hile riskleri

- **Çoklu client / bot.** Günlük tavan doğal fren; ayrıca kazma animasyonu ve
  dayanıklılık tüketimi sunucuda doğrulanır, düzenli aralıklı mükemmel tıklama
  paterni loglanır (`openko-anticheat`).
- **Sahte tick.** Pay dağıtımını client tetiklemez, sunucu zamanlayıcısı
  tetikler. `WIZ_MINE_START` sadece bir bildirimdir.
- **Cevher dupe.** Cevher bağlı; takas ve depo kapalı; teslim tek transaction
  ve idempotent.
- **Ölüm çiftçiliği.** Cevher öldürene geçmez — iki hesapla birbirini öldürüp
  servet biriktirme kapısı kapalı. Transfer modeline asla dönülmemeli.
- **Havuz karışması.** `purchased` havuzundan çekim yapılmasına izin veren tek
  bir kod yolu bile bütün arbitraj korumasını iptal eder. Çekim sorgusu
  `pool='earned'` filtresi olmadan yazılmamalı.

---

## 8. Yol haritası

**Faz 1 — kriptosuz maden (şimdi).** Maden alanı, tick, cevher, teslim NPC'si,
kazma yıpranması, ölümde cevher kaybı, upgrade girdisi. KC tablosu yazılır ama
çekim yoktur. Tamamen KO içeriği; bridge'e, cüzdana, KYC'ye dokunulmaz.

Birkaç hafta çalıştırılıp **gerçek sayılar ölçülür**: günlük cevher üretimi,
eşzamanlı madenci sayısı, upgrade'de yanan oran. `V0`, `Vmax` ve günlük tavan
bu veriye göre oturtulur. Para musluğu sayılar bilinmeden açılmaz.

**Faz 2 — oyun içi pazar.** Oyuncular arası, fiyatlar **gold**. Cevherin
upgrade yapana ulaşma yolu; aynı zamanda gold lavabosu (%5 komisyon). Bu
planın en büyük iş kalemi: yeni opcode'lar, UI penceresi, listeleme tablosu,
emanet mantığı. Dupe için bir numaralı hedef — iki tarafın onayı tek
transaction'da ve satır kilidiyle.

**Faz 3 — KC ve çekim.** Kasa (KC satışı), upgrade kağıdı, bridge, deposit,
çekim kuyruğu, KYC ve limitler.

Oyun içinde KC ↔ TL alım satımı **kapsam dışı** — lisans gerektirir.

---

## 9. Açık kararlar

1. `V0`, `Vmax`, günlük tavan kesin değerleri — faz 1 ölçümünden sonra
2. Peg sabit mi (1 USDT = 100 KC), dönemsel ayarlanabilir mi?
3. Maden alanının yarıçapı. CZ merkezinde ~250 birim genişliğinde doğal düzlük
   var (iki üsse de 391 birim). Şu an orada boss spawn halkası duruyor —
   bossler taşınsın mı, maden ve bossler iç içe mi olsun?
4. Teslim NPC'si her iki üste mi, Moradon'da mı?
5. Cevher taşıma kapasitesi sınırlı mı? (Sınırlıysa dönüş zorunlu olur.)
6. Cevher hangi upgrade seviyelerinde girdi olacak? (+8 üstü? nadir craft?)

---

## 10. Uyum notu

KC'nin USDT'ye çevrilebilir olması bu tasarımı Türkiye'de düzenleme kapsamına
yaklaştırır: TCMB'nin kripto ile ödeme yasağı, SPK'nın kripto hizmet
sağlayıcı lisansı, MASAK'ın kimlik doğrulama, limit ve bekleme kuralları. İki
havuz ayrımı duruşu belirgin şekilde iyileştirir ama tek başına yeterli
değildir. Bu belge teknik tasarımdır, hukuki görüş değildir — faz 3'e
geçmeden önce bir hukukçuya danışılmalı.
