#include "pch.h"
#include "Mine.h"

#include "EbenezerApp.h"
#include "User.h"

#include <shared-server/utilities.h>
#include <spdlog/spdlog.h>

#include <algorithm>
#include <cmath>
#include <string>
#include <vector>

namespace Ebenezer
{

namespace
{

// Oyuncuya tek satir bilgi gonderir. Istemci 12 numarali sohbet tipini
// ekrana basmadan siler (N3_CHAT_CONTINUE_DELETE), bu yuzden PRIVATE_CHAT (2).
void SendLine(CUser* pUser, const std::string& text)
{
	if (pUser == nullptr)
		return;

	char sendBuffer[1024] {};
	int sendIndex = 0;
	static const std::string emptyName;

	SetByte(sendBuffer, WIZ_CHAT, sendIndex);
	SetByte(sendBuffer, PRIVATE_CHAT, sendIndex);
	SetByte(sendBuffer, pUser->m_pUserData->m_bNation, sendIndex);
	SetShort(sendBuffer, pUser->GetSocketID(), sendIndex);
	SetString1(sendBuffer, emptyName, sendIndex);
	SetString2(sendBuffer, text, sendIndex);
	pUser->Send(sendBuffer, sendIndex);
}

} // anonymous namespace

namespace Mine
{

bool IsInside(int16_t zoneId, float x, float z)
{
	if (zoneId != ZONE_ID)
		return false;

	const float dx = x - CENTER_X;
	const float dz = z - CENTER_Z;
	return (dx * dx + dz * dz) <= (RADIUS * RADIUS);
}

void OnUserDeath(CUser* pUser)
{
	if (pUser == nullptr || pUser->m_iOreCarried <= 0)
		return;

	const int lost          = pUser->m_iOreCarried;
	pUser->m_iOreCarried    = 0;
	pUser->m_dOreFraction   = 0.0;
	pUser->m_bMining        = false;

	SendLine(pUser, "[Maden] Oldun. Teslim edilmemis " + std::to_string(lost) + " cevher kayboldu.");
	spdlog::info("Mine::OnUserDeath: ore lost [charId={} ore={}]", pUser->m_pUserData->m_id, lost);
}

void OnUserLeave(CUser* pUser)
{
	if (pUser == nullptr)
		return;

	pUser->m_bMining      = false;
	pUser->m_dOreFraction = 0.0;
}

static void SendState(CUser* pUser, int activeMiners, double perHour)
{
	char sendBuffer[64] {};
	int sendIndex = 0;

	SetByte(sendBuffer, WIZ_MINE, sendIndex);
	SetByte(sendBuffer, MINE_STATE, sendIndex);
	SetByte(sendBuffer, pUser->m_bMining ? 1 : 0, sendIndex);
	SetShort(sendBuffer, std::min(activeMiners, 32767), sendIndex);
	SetShort(sendBuffer, std::min(pUser->m_iOreCarried, 32767), sendIndex);
	SetShort(sendBuffer, static_cast<int>(perHour * 10.0), sendIndex); // 0.1 hassasiyet
	pUser->Send(sendBuffer, sendIndex);
}

void HandlePacket(CUser* pUser, char* pBuf, int /*len*/)
{
	if (pUser == nullptr)
		return;

	int index            = 0;
	const uint8_t subCmd = GetByte(pBuf, index);

	switch (subCmd)
	{
		case MINE_START:
		{
			if (!IsInside(pUser->m_pUserData->m_bZone, pUser->m_pUserData->m_curx,
					pUser->m_pUserData->m_curz))
			{
				SendLine(pUser, "[Maden] Burada maden yok. Colony Zone'un ortasina git.");
				return;
			}

			if (CARRY_LIMIT > 0 && pUser->m_iOreCarried >= CARRY_LIMIT)
			{
				SendLine(pUser, "[Maden] Cantan dolu. Cevheri ussune teslim et.");
				return;
			}

			pUser->m_bMining = true;
			SendLine(pUser, "[Maden] Kazmaya basladin.");
			spdlog::debug("Mine::Start: [charId={} x={:.0f} z={:.0f}]", pUser->m_pUserData->m_id,
				pUser->m_pUserData->m_curx, pUser->m_pUserData->m_curz);
			break;
		}

		case MINE_STOP:
			pUser->m_bMining = false;
			SendLine(pUser, "[Maden] Kazmayi biraktin.");
			break;

		case MINE_STATE:
			SendState(pUser, 0, 0.0);
			break;

		case MINE_DELIVER:
		{
			if (pUser->m_iOreCarried <= 0)
			{
				SendLine(pUser, "[Maden] Teslim edecek cevherin yok.");
				return;
			}

			// Faz 1: KC tablosu yok, teslim yalnizca loglanir ve oyuncuya bildirilir.
			// Faz 3'te burasi Aujard uzerinden KC_LEDGER'a yazacak.
			const int ore        = pUser->m_iOreCarried;
			pUser->m_iOreCarried = 0;

			SendLine(pUser, "[Maden] " + std::to_string(ore) + " cevher teslim edildi.");
			spdlog::info("Mine::Deliver: [charId={} ore={} zone={}]", pUser->m_pUserData->m_id, ore,
				pUser->m_pUserData->m_bZone);
			break;
		}

		default:
			spdlog::warn("Mine::HandlePacket: unknown subcommand [charId={} sub={}]",
				pUser->m_pUserData->m_id, subCmd);
			break;
	}
}

} // namespace Mine

// ---------------------------------------------------------------------------
// Damar tick'i. EbenezerApp zamanlayicisindan Mine::TICK_SECONDS araliklarla
// cagrilir. Sayim ve dagitim tamamen sunucuda; istemciye guvenilmez.
// ---------------------------------------------------------------------------
void EbenezerApp::MineTick()
{
	std::vector<std::shared_ptr<CUser>> miners;

	const int socketCount = GetUserSocketCount();
	for (int i = 0; i < socketCount; i++)
	{
		auto pUser = GetUserPtrUnchecked(i);
		if (pUser == nullptr || pUser->GetState() != CONNECTION_STATE_GAMESTART)
			continue;

		const bool dead = (pUser->m_bResHpType == USER_DEAD || pUser->m_pUserData->m_sHp <= 0);

		// Olum cezasi: kazmayi birakmis olsa bile, uzerinde teslim edilmemis
		// cevherle oldugunde cevher yanar. Tek yerde kontrol edilir ki olum
		// yollarindan birine dokunmayi unutmak acik birakmasin.
		if (dead)
		{
			if (pUser->m_iOreCarried > 0)
				Mine::OnUserDeath(pUser.get());
			else
				pUser->m_bMining = false;
			continue;
		}

		if (!pUser->m_bMining)
			continue;

		// Alandan cikan oyuncu kazmayi birakir (cevheri yanmaz).
		if (!Mine::IsInside(pUser->m_pUserData->m_bZone, pUser->m_pUserData->m_curx,
				pUser->m_pUserData->m_curz))
		{
			pUser->m_bMining = false;
			continue;
		}

		miners.push_back(pUser);
	}

	const int activeMiners = static_cast<int>(miners.size());
	if (activeMiners == 0)
		return;

	// V(N) = min(V0 * karekok(N), VMAX)  -- saatlik toplam cevher
	const double vein       = std::min(Mine::V0 * std::sqrt(static_cast<double>(activeMiners)),
			  Mine::VMAX);
	const double perUserHour = vein / activeMiners;
	const double perUserTick = perUserHour * (Mine::TICK_SECONDS / 3600.0);

	for (auto& pUser : miners)
	{
		pUser->m_dOreFraction += perUserTick;

		const int gained = static_cast<int>(pUser->m_dOreFraction);
		if (gained <= 0)
			continue;

		pUser->m_dOreFraction -= gained;
		pUser->m_iOreCarried += gained;

		if (Mine::CARRY_LIMIT > 0 && pUser->m_iOreCarried >= Mine::CARRY_LIMIT)
		{
			pUser->m_iOreCarried = Mine::CARRY_LIMIT;
			pUser->m_bMining     = false;
		}
	}

	spdlog::debug("EbenezerApp::MineTick: miners={} vein={:.1f}/h perUser={:.2f}/h", activeMiners,
		vein, perUserHour);
}

} // namespace Ebenezer
