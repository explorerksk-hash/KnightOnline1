// g++ -std=c++20 -I../src/Server/Ebenezer CheatGuardTest.cpp && ./a.out
#include "CheatGuard.h"

#include <cassert>
#include <cstdio>

using namespace openko;
using namespace std::chrono_literals;

static GuardClock::time_point T0 = GuardClock::now();

static int simulate(CMoveGuard& g, float metersPerSec, int speedPct, int seconds, float packetHz = 5.0f)
{
	int worst      = 0;
	const float dt = 1.0f / packetHz;
	auto t         = T0;
	g.Check(0.0f, speedPct, t); // init
	for (int i = 0; i < static_cast<int>(seconds * packetHz); i++)
	{
		t += std::chrono::milliseconds(static_cast<int>(dt * 1000));
		GuardVerdict v = g.Check(metersPerSec * dt, speedPct, t);
		worst          = std::max(worst, static_cast<int>(v));
	}
	return worst;
}

int main()
{
	// 1) Normal kosma (4.5 m/s), buff yok -> hic strike yok
	{
		CMoveGuard g;
		assert(simulate(g, 4.5f, 100, 120) == 0);
		assert(g.Strikes() == 0);
	}
	// 2) %150 hiz buff'i ile 6.75 m/s -> hic strike yok
	{
		CMoveGuard g;
		assert(simulate(g, 6.75f, 150, 120) == 0);
	}
	// 3) Gecikme titremesi: paketler toplu gelse de toplam mesafe dogru -> strike yok
	{
		CMoveGuard g;
		auto t = T0;
		g.Check(0, 100, t);
		for (int i = 0; i < 50; i++)
		{
			t += 1000ms;
			assert(g.Check(4.5f * 0.6f, 100, t) == GuardVerdict::Ok); // 0.6 s'lik mesafe
			t += 200ms;
			assert(g.Check(4.5f * 0.6f, 100, t) == GuardVerdict::Ok);
		}
	}
	// 4) Speedhack x2 (9 m/s, buff yok) -> birkac saniyede Violation
	{
		CMoveGuard g;
		assert(simulate(g, 9.0f, 100, 60) == static_cast<int>(GuardVerdict::Violation));
		std::printf("x2 speedhack: strikes=%d\n", g.TotalStrikes());
		assert(g.TotalStrikes() >= 5);
	}
	// 5) Hafif speedhack x1.5 (6.75 m/s, buff yok) -> yine yakalanir (tolerans 1.3)
	{
		CMoveGuard g;
		assert(simulate(g, 6.75f, 100, 120) == static_cast<int>(GuardVerdict::Violation));
	}
	// 6) Teleport hack: tek pakette 400 m -> aninda strike
	{
		CMoveGuard g;
		g.Check(0, 100, T0);
		assert(g.Check(400.0f, 100, T0 + 200ms) == GuardVerdict::Suspicious);
	}
	// 7) Sunucu warp'i: Reset sonrasi ilk paket Ok
	{
		CMoveGuard g;
		g.Check(0, 100, T0);
		g.Reset();
		assert(g.Check(400.0f, 100, T0 + 200ms) == GuardVerdict::Ok);
	}
	// 8) Strike'lar zamanla azalir
	{
		CMoveGuard g;
		g.Check(0, 100, T0);
		g.Check(400.0f, 100, T0 + 1s);
		g.Check(400.0f, 100, T0 + 2s);
		assert(g.Strikes() == 2);
		g.Check(0.1f, 100, T0 + 200s);
		assert(g.Strikes() == 0);
	}
	// 9) Paket seli
	{
		CPacketGuard p;
		auto t       = T0;
		int worst    = 0;
		for (int s = 0; s < 4; s++)
		{
			for (int i = 0; i < 300; i++)
			{
				t += 3ms;
				worst = std::max(worst, static_cast<int>(p.OnPacket(t)));
			}
			t += 100ms;
		}
		assert(worst == static_cast<int>(GuardVerdict::Violation));
		CPacketGuard q;
		t = T0;
		for (int i = 0; i < 600; i++)
		{
			t += 50ms; // 20/s
			assert(q.OnPacket(t) == GuardVerdict::Ok);
		}
	}
	std::printf("CheatGuard: tum testler gecti\n");
	return 0;
}
