#pragma once

// OpenKO anti-cheat (sunucu tarafi) - openko-anticheat
//
// Iki bagimsiz, bagimliliksiz (yalnizca STL) bekci:
//   CMoveGuard   : hareket paketlerini hiz/mesafe butcesiyle dogrular (speedhack, teleport).
//   CPacketGuard : saniye basina paket sayisini sinirlar (flood / bot spam).
//
// Ikisi de "strike" biriktirir; strike'lar zamanla azalir. Karar verme (kick/ban) cagirana
// birakilir; bu dosya yalnizca olcum yapar. Bkz. tests/CheatGuardTest.cpp.

#include <algorithm>
#include <chrono>
#include <cstdint>

namespace openko
{

using GuardClock = std::chrono::steady_clock;

enum class GuardVerdict : uint8_t
{
	Ok = 0,     // butce icinde
	Suspicious, // butce asildi, strike eklendi
	Violation   // strike limiti doldu -> yaptirim onerilir
};

// ---------------------------------------------------------------------------
// Hareket bekcisi
//
// Istemci kosarken 4.5 m/s (MOVE_SPEED_WHEN_WALK 1.5 * MOVE_DELTA_WHEN_RUNNING 3) hareket eder;
// hiz buff'lari m_bSpeedAmount (%) ile carpilir. Her paket arasi gecen sure kadar "mesafe
// butcesi" birikir (en fazla burstSeconds saniyelik), gelen paketin katettigi mesafe butceden
// dusulur. Butce deficitLimit metreden fazla eksiye dusunce strike verilir ve butce sifirlanir.
// Sunucu oyuncuyu isinlattiginda (warp/zone/skill) hedef koordinat sunucu tarafinda guncellenir;
// cagiran taraf mesafeyi hem "will" hem "cur" konuma gore hesaplayip kucugunu verdigi icin
// isinlanmalar strike uretmez.
// ---------------------------------------------------------------------------
class CMoveGuard
{
public:
	struct Config
	{
		float baseRunSpeed   = 4.5f;  // m/s, buff'siz kosma hizi
		float tolerance      = 1.30f; // ag gecikmesi / yuvarlama payi
		float burstSeconds   = 2.0f;  // biriktirilebilecek en fazla butce (saniye cinsinden)
		float deficitLimit   = 10.0f; // bu kadar metre acik -> strike
		int strikeLimit      = 5;     // bu kadar strike -> Violation
		float strikeDecaySec = 60.0f; // her N saniyede 1 strike silinir
		float maxJumpMeters  = 150.0f; // tek pakette bundan uzak -> dogrudan strike (teleport hack)
	};

	CMoveGuard() = default;

	explicit CMoveGuard(const Config& cfg)
		: _cfg(cfg)
	{
	}

	// dist        : bu paketle katedilen mesafe (metre)
	// speedPercent: m_bSpeedAmount (100 = normal). 100'un altindaki degerler 100 kabul edilir
	//               (yavaslatma buff'lari icin istemci zaten daha yavas gonderir).
	GuardVerdict Check(float dist, int speedPercent, GuardClock::time_point now)
	{
		if (!_initialized)
		{
			_initialized = true;
			_lastPacket  = now;
			_lastDecay   = now;
			_budget      = MaxSpeed(speedPercent) * _cfg.burstSeconds;
			return GuardVerdict::Ok;
		}

		DecayStrikes(now);

		const float dt = std::chrono::duration<float>(now - _lastPacket).count();
		_lastPacket    = now;

		const float vmax = MaxSpeed(speedPercent);
		_budget          = std::min(_budget + std::max(0.0f, dt) * vmax, vmax * _cfg.burstSeconds);
		_budget -= dist;

		bool strike = false;
		if (dist > _cfg.maxJumpMeters)
			strike = true;
		else if (_budget < -_cfg.deficitLimit)
			strike = true;

		if (!strike)
			return GuardVerdict::Ok;

		_budget = 0.0f;
		++_strikes;
		++_totalStrikes;
		return (_strikes >= _cfg.strikeLimit) ? GuardVerdict::Violation : GuardVerdict::Suspicious;
	}

	// Sunucu oyuncuyu bilerek tasidiysa (warp, zone degisimi, olum/dirilme) cagirin.
	void Reset()
	{
		_initialized = false;
		_budget      = 0.0f;
	}

	void ClearStrikes()
	{
		_strikes = 0;
	}

	int Strikes() const
	{
		return _strikes;
	}

	int TotalStrikes() const
	{
		return _totalStrikes;
	}

	float Budget() const
	{
		return _budget;
	}

	const Config& GetConfig() const
	{
		return _cfg;
	}

private:
	float MaxSpeed(int speedPercent) const
	{
		const int pct = std::max(100, speedPercent);
		return _cfg.baseRunSpeed * (static_cast<float>(pct) / 100.0f) * _cfg.tolerance;
	}

	void DecayStrikes(GuardClock::time_point now)
	{
		if (_strikes <= 0)
		{
			_lastDecay = now;
			return;
		}

		const float since = std::chrono::duration<float>(now - _lastDecay).count();
		if (since >= _cfg.strikeDecaySec)
		{
			const int drop = static_cast<int>(since / _cfg.strikeDecaySec);
			_strikes       = std::max(0, _strikes - drop);
			_lastDecay     = now;
		}
	}

	Config _cfg {};
	bool _initialized = false;
	float _budget     = 0.0f;
	int _strikes      = 0;
	int _totalStrikes = 0;
	GuardClock::time_point _lastPacket {};
	GuardClock::time_point _lastDecay {};
};

// ---------------------------------------------------------------------------
// Paket sel bekcisi: kayan 1 saniyelik pencerede paket sayar.
// ---------------------------------------------------------------------------
class CPacketGuard
{
public:
	struct Config
	{
		int maxPerSecond = 120; // normal oyun ~10-30/s; 120 uzerinde bot/flood kabul
		int strikeLimit  = 3;   // ard arda bu kadar saniye asilirsa Violation
	};

	CPacketGuard() = default;

	explicit CPacketGuard(const Config& cfg)
		: _cfg(cfg)
	{
	}

	GuardVerdict OnPacket(GuardClock::time_point now)
	{
		if (_windowStart == GuardClock::time_point {})
			_windowStart = now;

		const float since = std::chrono::duration<float>(now - _windowStart).count();
		if (since >= 1.0f)
		{
			// pencere kapandi: asilmadiysa strike'lari sifirla
			if (_count <= _cfg.maxPerSecond)
				_strikes = 0;
			_windowStart = now;
			_count       = 0;
		}

		++_count;
		if (_count == _cfg.maxPerSecond + 1) // bu pencerede ilk asim
		{
			++_strikes;
			return (_strikes >= _cfg.strikeLimit) ? GuardVerdict::Violation : GuardVerdict::Suspicious;
		}

		return GuardVerdict::Ok;
	}

	int Strikes() const
	{
		return _strikes;
	}

private:
	Config _cfg {};
	GuardClock::time_point _windowStart {};
	int _count   = 0;
	int _strikes = 0;
};

} // namespace openko
