# Open-KO Bug Kaydı

| ID | Bileşen | Belirti | Önem | Repro | Durum | Commit |
|----|---------|---------|------|-------|-------|--------|
| 7 | Ebenezer | Ebenezer, AIServer'dan önce açılırsa bağlantı bir daha hiç denenmiyordu → oyunda hiç mob/NPC doğmuyor. `GameTimeTick` yalnızca `m_bFirstServerFlag` (bir kez bağlanmış olma) durumunda yeniden bağlanıyordu. | **P0** | AIServer'ı Ebenezer'den sonra başlat | **Düzeltildi** — her tick yeniden denenir, sunucu açılış sırası artık önemsiz | `fix(ebenezer): keep retrying AIServer` |
| 1 | Aujard | `AujardApp::ConCurrentUserCount()` (AujardApp.cpp ~670) ilk 5 dk tick'inde `strlen(pUser->m_id)` okurken 0xC0000005 access violation. `pUser` Ebenezer'in `KNIGHT_DB` paylaşımlı belleğine işaret ediyor (3000 x 8000 bayt = 24.000.000). İlk çalıştırmada (6 Eyl 2026 09:38) görüldü; queue'lar hazır olmadığı için "waiting" yolu izlenmişti. İkinci çalıştırmada (10:17, queue'lar ilk denemede açıldı) 3 tick boyunca tekrar etmedi. | P0 | Sunucuları "Only servers" ile başlat, 5 dk bekle (timer geçici 30 sn) | Açık — koruma + teşhis eklendi, kök neden doğrulanmadı | (çalışma kopyası) |
| 2 | Ebenezer | `EXEC::Parse: unhandled opcode` — CHANGE_POSITION, MOVE_MIDDLE_STATUE, CHANGE_NAME, SEND_WEBPAGE_ADDRESS, STATE_CHANGE, CHECK_PCBANG_*, SHOW_PCBANG_ITEM, CHECK_PPCARD_SERIAL, GIVE_PPCARD_ITEM, ZONE_CHANGE_PARTY; `EVENT::LoadEvent: unhandled opcode 'TYPE'` (11.evt, 12.evt) | P1 | Sunucu başlangıcı, assets/Server/QUESTS yüklenirken | **Düzeltildi** (4f093ac) — 12 EXEC + 2 LOGIC opcode'u parse ediliyor; ZONE_CHANGE_PARTY / ROB_ALLITEM_PARTY gerçek davranışla, PC-bang / PP-card ailesi bilinçli no-op; `TYPE` başlık satırı atlanıyor | EXEC.cpp, LOGIC_ELSE.cpp, EVENT.cpp, User.cpp/.h |
| 3 | Ebenezer | `LoadNoticeData: failed to open Notice.txt` | P2 | Başlangıç | **Düzeltildi** — dosya zorunlu değil; eksikse artık warn yerine info seviyesinde ve **tam yol** yazılıyor. Varsayılan `Notice.txt` assets/Server altına eklendi (çalışma dizinine, gameserver.ini'nin yanına kopyalanır) | EbenezerApp.cpp, assets/Server/Notice.txt |
| 4 | AIServer | `Npc::IsNoPathFind invalid pathCount` / `StepMove aniFrameCount out of bounds` (Victory Gate 10510/20510, pathCount=100, frameCount=0) | P2 | Başlangıç | **Düzeltildi** — adım boyu 0/çok küçükken sonsuz döngü; artık adım boyu yola göre büyütülüyor, yol yoksa StepMove sessizce çıkıyor | `fix(aiserver): npc path` |
| 5 | AIServer | `GameSocket::Parsing: Unhandled opcode 32` (Ebenezer → AI, 4 kez başlangıçta) | P2 | Ebenezer bağlanınca | **Düzeltildi** — 0x32 = 50 = `AG_SERVER_INFO`; Ebenezer `SendAllUserInfo()` ile toplu oyuncu listesini gönderirken başa/sona koyduğu işaretçiler AIServer tarafında karşılıksızdı. `CGameSocket::RecvServerInfo()` eklendi | GameSocket.cpp/.h |
| 6 | Client | KnightOnLine.exe başlatıldığında küçük bir pencere açılıyor, ~13 MB bellek; Log.txt oluşmadı → N3Eng init'ten önce duruyor (mesaj kutusu?). Claude pencereyi göremiyor. | P0 | "Only client" profili ile başlat | Açık — kullanıcı ekranı bildirecek | — |
| 8 | AIServer | Bazı haritalarda hiç NPC/mob yok (El Morad ve savaş bölgeleri) | P0 | Her açılışta | **Düzeltildi** — `server.ini` `[SERVER] ZONE=1` (KARUS) idi; `LoadNpcPosTable` yalnızca kendi sunucu numarasına ait bölgelerin NPC'lerini üretiyordu. `ZONE=0` (UNIFY) yapıldı; ayrıca `AddObjectEventNpc` içinde UNIFY istisnası eksikti (kapı/heykel gibi harita olay NPC'leri de üretilmiyordu) | AIServerApp.cpp, bin/Debug-x64/server.ini |

## Yapılan değişiklikler

- `src/Server/shared-server/SharedMemoryBlock.{h,cpp}`: `GetSize()`, `GetName()` eklendi.
- `src/Server/Aujard/AujardApp.cpp`:
  - `InitSharedMemory`: mapping boyutu `MAX_USER * ALLOCATED_USER_DATA_BLOCK`'tan küçükse Release + retry.
  - `ConCurrentUserCount`: base/size debug logu (DIAG #1).
  - `_concurrentCheckThread` geçici 30s → **5 dk'ya geri alındı**.
- `src/Server/Ebenezer/EbenezerApp.cpp`: AIServer'a yeniden bağlanma (bug #7).
- `src/Server/AIServer/Npc.cpp`: `IsNoPathFind` adım boyu düzeltmesi + `StepMove` boş yol koruması (bug #4).
- `src/Server/Ebenezer/CheatGuard.h` + `User.{h,cpp}`: anti-cheat faz 1 (hareket/paket bekçileri, `OPENKO_ANTICHEAT_KICK` ile kapalı).

## Bilinen dış kayıtlar
- Upstream #80: client `CN3UIWndBase::m_sRecoveryJobInfo.pItemSource` null deref (kapalı, çözümsüz).
