#ifndef EBENEZER_MINE_H
#define EBENEZER_MINE_H

#pragma once

#include <cstdint>

class CUser;

namespace Ebenezer::Mine
{

// ---------------------------------------------------------------------------
// Maden ayarlari. Faz 1'de sabit; faz 2'de gameserver.ini / MINE_ZONE tablosu.
// Tasarim: docs/design/maden.md
// ---------------------------------------------------------------------------

// Colony Zone. Merkez oyun icinde isaretlendi (Merhaba, 2 Ekim 2026).
inline constexpr int16_t ZONE_ID = 201;
inline constexpr float CENTER_X  = 1014.9f;
inline constexpr float CENTER_Z  = 992.7f;
inline constexpr float RADIUS    = 125.0f;

// Damar: V(N) = min(V0 * karekok(N), VMAX), saatlik toplam cevher.
inline constexpr double V0   = 40.0;
inline constexpr double VMAX = 250.0;

// Tick araligi (EbenezerApp zamanlayicisi ile ayni olmali).
inline constexpr int TICK_SECONDS = 10;

// Tek seferde tasinabilecek en fazla cevher. 0 = sinirsiz.
inline constexpr int CARRY_LIMIT = 500;

// Kazma esyasi henuz yok; 0 iken dayaniklilik tuketimi atlanir (faz 2).
inline constexpr int PICKAXE_ITEM_ID = 0;

bool IsInside(int16_t zoneId, float x, float z);

// WIZ_MINE alt komutlari
enum e_MineOpcode : uint8_t
{
	MINE_START   = 1, // kazmaya basla
	MINE_STOP    = 2, // birak
	MINE_STATE   = 3, // durum sorgusu (sunucu da kendiliginden gonderir)
	MINE_DELIVER = 4, // cevheri teslim et
};

// CUser::Parsing icinden cagrilir.
void HandlePacket(CUser* pUser, char* pBuf, int len);

// Oyuncu oldugunde: tasinan cevher yanar. Olum yollarindan cagrilir.
void OnUserDeath(CUser* pUser);

// Oyuncu bolge degistirince / cikinca madenciligi birakir.
void OnUserLeave(CUser* pUser);

} // namespace Ebenezer::Mine

#endif // EBENEZER_MINE_H
