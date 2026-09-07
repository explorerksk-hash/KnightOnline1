// g++ -std=c++20 -I../src/Server/Ebenezer CheatGuardTest.cpp && ./a.out
#include "CheatGuard.h"

#include <cassert>
#include <cstdio>
#include <random>

using namespace openko;
using namespace std::chrono_literals;

static GuardClock::time_point T0 = GuardClock::now();

static int run(CMoveGuard& g, float metersPerSec, int speedPct, int seconds,
	float packetHz = 5.0f, float jitter = 0.0f, unsigned seed = 1)
{
	std::mt19937 rng(seed);
	std::uniform_real_distribution<float> jit(-jitter, jitter);
	int w         = 0;
	auto t        = T0;
	const float dt = 1.0f / packetHz;
	for (int i = 0; i < static_cast<int>(seconds * packetHz); i++)
	{
		const float step = std::max(0.0f, dt + jit(rng));
		t += std::chrono::milliseconds(static_cast<int>(step * 1000));
		w = std::max(w, static_cast<int>(g.Check(metersPerSec * step, speedPct, t)));
	}
	return w;
}

int main()
{
	// 1) Normal kosma, duzenli paket -> temiz
	{
		CMoveGuard g;
		assert(run(g, 4.5f, 100, 180) == 0);
	}
	// 2) %150 hiz buff'i -> temiz
	{
		CMoveGuard g;
		assert(run(g, 6.75f, 150, 180) == 0);
	}
	// 3) Agir gecikme titremesi (paket araligi 0.05-0.75 s arasi oynuyor) -> temiz
	//    Ilk surumdeki yanlis pozitiflerin sebebi buydu.
	{
		CMoveGuard g;
		assert(run(g, 4.5f, 100, 300, 4.0f, 0.30f, 7) == 0);
	}
	// 4) Paketler toplu geliyor: 1 s sessizlik + arka arkaya 5 paket -> temiz
	{
		CMoveGuard g;
		auto t = T0;
		int w  = 0;
		for (int burst = 0; burst < 40; burst++)
		{
			t += 1000ms;
			w = std::max(w, static_cast<int>(g.Check(4.5f * 1.0f, 100, t))); // 1 s'lik mesafe
			for (int k = 0; k < 4; k++)
			{
				t += 40ms;
				w = std::max(w, static_cast<int>(g.Check(4.5f * 0.04f, 100, t)));
			}
		}
		assert(w == 0);
	}
	// 5) Tek isinlanma (portal, 120 m) tolere edilir
	{
		CMoveGuard g;
		run(g, 4.5f, 100, 20);
		auto t = T0 + 30s;
		assert(g.Check(120.0f, 100, t) == GuardVerdict::Ok);
		assert(g.Strikes() == 0);
	}
	// 6) Speedhack x2 -> Violation
	{
		CMoveGuard g;
		assert(run(g, 9.0f, 100, 120) == static_cast<int>(GuardVerdict::Violation));
		std::printf("x2 speedhack: strikes=%d\n", g.TotalStrikes());
	}
	// 7) Hafif speedhack x1.6 (buff yok) -> yakalanir
	{
		CMoveGuard g;
		assert(run(g, 7.2f, 100, 180) == static_cast<int>(GuardVerdict::Violation));
	}
	// 8) Isinlanma hilesi: 10 sn icinde arka arkaya sicramalar -> yakalanir
	{
		CMoveGuard g;
		auto t = T0;
		int w  = 0;
		for (int i = 0; i < 6; i++)
		{
			t += 900ms;
			w = std::max(w, static_cast<int>(g.Check(300.0f, 100, t)));
		}
		assert(w >= static_cast<int>(GuardVerdict::Suspicious));
	}
	// 9) Sunucu warp'i sonrasi Reset -> temiz
	{
		CMoveGuard g;
		run(g, 4.5f, 100, 20);
		g.Reset();
		assert(g.Check(800.0f, 100, T0 + 25s) == GuardVerdict::Ok);
	}
	// 10) Strike'lar zamanla silinir
	{
		CMoveGuard g;
		run(g, 9.0f, 100, 30);
		assert(g.Strikes() > 0);
		g.Check(0.1f, 100, T0 + 600s);
		assert(g.Strikes() == 0);
	}
	// 11) Paket seli
	{
		CPacketGuard p;
		auto t    = T0;
		int w     = 0;
		for (int s = 0; s < 4; s++)
		{
			for (int i = 0; i < 300; i++)
			{
				t += 3ms;
				w = std::max(w, static_cast<int>(p.OnPacket(t)));
			}
			t += 100ms;
		}
		assert(w == static_cast<int>(GuardVerdict::Violation));

		CPacketGuard q;
		t = T0;
		for (int i = 0; i < 600; i++)
		{
			t += 50ms; // 20/s
			assert(q.OnPacket(t) == GuardVerdict::Ok);
		}
	}
	// 12) Uzun kosu segmentleri: istemci VARILACAK noktayi gonderir, oyuncu o
	//     mesafeyi henuz katetmemistir. Fare ile uzaga tiklayan oyuncu tek
	//     pakette 40-56 m bildirir. 7 Eyl 2026 gunlugundeki yanlis alarm buydu.
	{
		CMoveGuard g;
		auto t = T0;
		int w  = 0;
		for (int i = 0; i < 30; i++)
		{
			// 12 s'de bir 55 m'lik segment ilan et: gercek hiz 4.6 m/s
			t += 12000ms;
			w = std::max(w, static_cast<int>(g.Check(55.0f, 100, t)));
			// arada normal kucuk duzeltmeler
			for (int k = 0; k < 4; k++)
			{
				t += 300ms;
				w = std::max(w, static_cast<int>(g.Check(1.4f, 100, t)));
			}
		}
		assert(w == 0);
	}
	// 13) Ayni sekil, ama gercekten hizli: 55 m'lik segmentler 3 s arayla
	//     (~18 m/s) -> yakalanmali.
	{
		CMoveGuard g;
		auto t = T0;
		int w  = 0;
		for (int i = 0; i < 30; i++)
		{
			t += 3000ms;
			w = std::max(w, static_cast<int>(g.Check(55.0f, 100, t)));
			for (int k = 0; k < 4; k++)
			{
				t += 200ms;
				w = std::max(w, static_cast<int>(g.Check(3.0f, 100, t)));
			}
		}
		assert(w > 0);
		std::printf("uzun segment hilesi: strikes=%d\n", g.TotalStrikes());
	}
	std::printf("CheatGuard: tum testler gecti\n");
	return 0;
}
