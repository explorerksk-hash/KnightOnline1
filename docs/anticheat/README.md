# OpenKO Anti-Cheat — Sunucu Tarafı (Faz 1)

Kaynak: `src/Server/Ebenezer/CheatGuard.h` (yalnızca STL, birim testli: `tests/CheatGuardTest.cpp`).

## Ne yapıyor

| Bekçi | Nerede | Ne ölçer | Karar |
|---|---|---|---|
| `CMoveGuard` | `CUser::MoveProcess` | Paket başına katedilen mesafe vs. hız bütçesi (4.5 m/s × `m_bSpeedAmount` × 1.3 tolerans, 2 sn birikim). 150 m üstü tek sıçrama = anında strike. | 5 strike → `Violation` |
| `CPacketGuard` | `CUser::Parsing` | Saniyede paket sayısı (>120) | 3 ardışık saniye → `Violation` |

- Strike'lar 60 sn'de bir azalır; kısa gecikme dalgalanmaları strike üretmez (testte doğrulandı).
- Sunucunun kendi taşıdığı oyuncu (`ZoneChange`, `Warp`) bekçiyi sıfırlar; diğer yer değiştirmeler
  (regene, home) için mesafe hem `cur` hem `will` konumuna göre alınır → yanlış alarm yok.
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
