#pragma once

// OpenKO anti-cheat (sunucu tarafi) - openko-anticheat
//
// Iki bagimsiz, bagimliliksiz (yalnizca STL) bekci:
//   CMoveGuard   : hareket paketlerini KAYAN PENCEREDE ortalama hiz ile dogrular.
//   CPacketGuard : saniye basina paket sayisini sinirlar (flood / bot spam).
//
// Neden ortalama hiz? Ilk surumde "mesafe butcesi" kullaniliyordu; paketler toplu
// geldiginde (ag gecikmesi, sunucu tick'i) normal oyuncu da acik biriktirip
// yanlis alarm uretiyordu (6 Eyl 2026 testinde 16 yanlis pozitif). Kayan pencere
// bu dalgalanmalari kendiliginden yutar: yalnizca SUREKLI asiri hiz yakalanir.
//
// Isinlanmalar (portal, warp, dirilme) ayri sayilir: tek pakette maxJumpMeters
// uzerindeki sicramalar mesafe ortalamasina KATILMAZ, kendi (cok daha gevsek)
// esikleriyle degerlendirilir. Sunucunun kendi tasidigi durumlarda cagiran taraf
// Reset() cagirir ve o sicrama hic sayilmaz.
//
// Karar verme (kick/ban) cagirana birakilir; bu dosya yalnizca olcum yapar.
// Bkz. tests/CheatGuardTest.cpp

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <deque>

namespace openko
{

using GuardClock = std::chrono::steady_clock;

enum class GuardVerdict : uint8_t
{
	Ok = 0,     // normal
	Suspicious, // esik asildi, strike eklendi
	Violation   // strike limiti doldu -> yaptirim onerilir
};

// ---------------------------------------------------------------------------
// Hareket bekcisi (kayan pencere)
// ---------------------------------------------------------------------------
class CMoveGuard
{
public:
	struct Config
	{
		float baseRunSpeed    = 4.5f;  // m/s, buff'siz kosma hizi (istemci: 1.5 * 3.0)
		float tolerance       = 1.45f; // yokus/ag/yuvarlama payi
		float windowSeconds   = 8.0f;  // ortalamanin alindigi pencere
		float minWindowFill   = 3.0f;  // pencere bu kadar dolmadan karar verilmez
		int strikeLimit       = 4;     // bu kadar strike -> Violation
		float strikeDecaySec  = 45.0f; // her N saniyede 1 strike silinir
		float maxJumpMeters   = 60.0f; // tek pakette bundan uzak -> isinlanma sayilir
		int jumpLimit         = 4;     // pencerede bu kadar acikamayan isinlanma -> strike
	};

	CMoveGuard() = default;

	explicit CMoveGuard(const Config& cfg)
		: _cfg(cfg)
	{
	}

	// dist        : bu paketle katedilen mesafe (metre)
	// speedPercent: m_bSpeedAmount (100 = normal); 100 altindakiler 100 sayilir
	GuardVerdict Check(float dist, int speedPercent, GuardClock::time_point now)
	{
		if (!(dist >= 0.0f)) // NaN dahil
			dist = 0.0f;

		DecayStrikes(now);
		Trim(now);

		const bool isJump = dist > _cfg.maxJumpMeters;
		if (isJump)
			_jumps.push_back(now);
		else
			_samples.push_back({now, dist, MaxSpeed(speedPercent)});

		if (!_started)
		{
			_started    = true;
			_windowFrom = now;
		}

		const float filled = std::chrono::duration<float>(now - _windowFrom).count();

		bool strike = false;
		if (static_cast<int>(_jumps.size()) >= _cfg.jumpLimit)
		{
			strike = true;
			_jumps.clear();
		}
		else if (filled >= _cfg.minWindowFill && _samples.size() >= 4)
		{
			float sumDist = 0.0f, sumAllowed = 0.0f;
			for (const Sample& s : _samples)
			{
				sumDist += s.dist;
				sumAllowed = std::max(sumAllowed, s.maxSpeed);
			}

			const float span = std::chrono::duration<float>(now - _samples.front().at).count();
			if (span > 0.5f)
			{
				const float avg = sumDist / span;
				if (avg > sumAllowed)
				{
					strike = true;
					_samples.clear();
					_windowFrom = now;
				}
			}
		}

		if (!strike)
			return GuardVerdict::Ok;

		++_strikes;
		++_totalStrikes;
		return (_strikes >= _cfg.strikeLimit) ? GuardVerdict::Violation : GuardVerdict::Suspicious;
	}

	// Sunucu oyuncuyu bilerek tasidiysa (warp, zone, dirilme, home) cagirin.
	void Reset()
	{
		_samples.clear();
		_jumps.clear();
		_started = false;
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

	const Config& GetConfig() const
	{
		return _cfg;
	}

private:
	struct Sample
	{
		GuardClock::time_point at;
		float dist;
		float maxSpeed;
	};

	float MaxSpeed(int speedPercent) const
	{
		const int pct = std::max(100, speedPercent);
		return _cfg.baseRunSpeed * (static_cast<float>(pct) / 100.0f) * _cfg.tolerance;
	}

	void Trim(GuardClock::time_point now)
	{
		const auto cutoff = now - std::chrono::duration_cast<GuardClock::duration>(
										  std::chrono::duration<float>(_cfg.windowSeconds));

		while (!_samples.empty() && _samples.front().at < cutoff)
			_samples.pop_front();

		while (!_jumps.empty() && _jumps.front() < cutoff)
			_jumps.pop_front();

		if (_started && _windowFrom < cutoff)
			_windowFrom = cutoff;
	}

	void DecayStrikes(GuardClock::time_point now)
	{
		if (_strikes <= 0)
		{
			_lastDecay = now;
			return;
		}

		if (_lastDecay == GuardClock::time_point {})
			_lastDecay = now;

		const float since = std::chrono::duration<float>(now - _lastDecay).count();
		if (since >= _cfg.strikeDecaySec)
		{
			_strikes   = std::max(0, _strikes - static_cast<int>(since / _cfg.strikeDecaySec));
			_lastDecay = now;
		}
	}

	Config _cfg {};
	std::deque<Sample> _samples;
	std::deque<GuardClock::time_point> _jumps;
	bool _started  = false;
	int _strikes   = 0;
	int _totalStrikes = 0;
	GuardClock::time_point _windowFrom {};
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
		int maxPerSecond = 120; // normal oyun ~10-30/s
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
			if (_count <= _cfg.maxPerSecond)
				_strikes = 0;
			_windowStart = now;
			_count       = 0;
		}

		++_count;
		if (_count == _cfg.maxPerSecond + 1)
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
