# OpenKO Anti-Cheat — Sunucu Tarafı (Faz 1)

Kaynak: `src/Server/Ebenezer/CheatGuard.h` (yalnızca STL, birim testli: `tests/CheatGuardTest.cpp`).

## Ne yapıyor

| Bekçi | Nerede | Ne ölçer | Karar |
|---|---|---|---|
| `CMoveGuard` | `CUser::MoveProcess` | **10 sn kayan pencerede ortalama hız** vs. izin verilen hız (4.5 m/s × `m_bSpeedAmount` × 1.45 tolerans). 60 m üstü tek sıçrama ortalamaya katılmaz, ayrı sayılır (pencerede 4 sıçrama → strike). Pencerenin **en uzun tek örneği** toplamdan düşülür: KO'nun hareket paketi varılacak noktayı taşıdığı için pencerenin sonunda her zaman henüz katedilmemiş bir segment bulunur. | 4 strike → `Violation` |
| `CPacketGuard` | `CUser::Parsing` | Saniyede paket sayısı (>120) | 3 ardışık saniye → `Violation` |

- Strike'lar 45 sn'de bir azalır.
- **Neden kayan pencere?** İlk sürüm "mesafe bütçesi" kullanıyordu; paketler toplu geldiğinde
  normal oyuncu da açık biriktirip yanlış alarm veriyordu (6 Eyl 2026 testinde tek oturumda
  16 yanlış pozitif). Ortalama hız bu dalgalanmaları yutar; testlere ağır gecikme titremesi
  ve toplu paket senaryoları eklendi.
- Sunucunun kendi taşıdığı oyuncu (`ZoneChange`, `Warp`, `Regene`, `SendMyInfo`) bekçiyi sıfırlar;
  ayrıca mesafe hem `cur` hem `will` konumuna göre alınıp küçüğü kullanılır → yanlış alarm yok.
- **Karar anahtarı:** `Define.h` → `OPENKO_ANTICHEAT_KICK`. Varsayılan `false` = sadece log
  (`User::MoveProcess: movement anomaly ...`, `User::Parsing: packet flood ...`).
  `true` yapınca hareket ihlalinde `SpeedHackUser()` (hesap BLOCK + bağlantı kesme), paket selinde bağlantı kesme.

## Devreye alma

1. Derle, sunucuyu aç, 1–2 gün Ebenezer loglarında `movement anomaly` satırlarını izle.
2. Normal oyunda satır görmüyorsan `OPENKO_ANTICHEAT_KICK = true` yap.
3. Hız buff'ı olan skill'ler `m_bSpeedAmount` üzerinden hesaba katılır; yeni bir hız kaynağı
   (binek vb.) eklersen aynı alanı güncelle.

## Sonraki fazlar (openko-anticheat skill'i)

- Faz 2: Skill/attack cooldown ve menzil doğrulaması (server-side), hasar formülünü istemciden almama.
- Faz 3: Launcher → istemci dosya hash'i (`openko-launcher` manifest) login paketinde; uyuşmazsa reddet.
- Faz 4: Otomatik ban listesi + GM paneli raporu (`openko-db`).
