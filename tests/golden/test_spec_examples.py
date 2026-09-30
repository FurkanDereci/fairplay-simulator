"""Spec işlenmiş örnekleri — `docs/20-accounting-spec.md` §1–§4.

Her test bir `[G-x]` kimliği taşır; `tests/test_docs_sync.py` bu kimliklerin spec ile birebir
örtüşmesini zorlar. Spec'teki sayı değişirse bu test kırılır.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal as D

from fairplay_echo.core import cooldown as cooldown_mod
from fairplay_echo.core import energy as energy_mod
from fairplay_echo.core import metrics, nav, odds
from fairplay_echo.core.ledger import Ledger
from fairplay_echo.core.metrics import SettledWager
from fairplay_echo.core.money import Money, q, q_nav, q_units

EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _replay(ledger: Ledger) -> nav.Fund:
    return nav.Fund.replay(ledger.entries)


def test_g1_refill_invariance() -> None:
    """[G-1] Refill NAV'ı değiştirmez; yalnız birim sayısı artar."""
    led = Ledger()
    led.deposit(D("1000"))
    led.place_wager("w1", D("100"))
    assert q_nav(_replay(led).nav) == D("100.0000")

    led.settle_wager("w1", D("100"), D("250"))
    fund = _replay(led)
    assert q_nav(fund.nav) == D("115.0000")
    assert fund.twr == D("15.00")

    led.refill(D("1000"))
    fund = _replay(led)
    assert q_units(fund.units) == D("18.6956522")
    assert q_nav(fund.nav) == D("115.0000")


def test_g2_bankruptcy_and_series_compounding() -> None:
    """[G-2] İflas kalıcı lekedir; TWR seriler arası bileşiktir (−100%)."""
    led = Ledger()
    led.deposit(D("1000"))
    led.place_wager("a", D("1000"))
    led.settle_wager("a", D("1000"), D("0"))
    led.refill(D("1000"))
    led.place_wager("b", D("500"))
    led.settle_wager("b", D("500"), D("1000"))

    fund = _replay(led)
    assert fund.series_id == 2
    assert q_nav(fund.nav) == D("150.0000")
    assert fund.twr == D("-100.00")


def test_g3_max_drawdown() -> None:
    """[G-3] MDD = %33.33."""
    series: list[Money] = [D("100"), D("120"), D("90"), D("110"), D("80")]
    assert metrics.max_drawdown_pct(series) == 33.33


def test_g4_sharpe() -> None:
    """[G-4] Sharpe = 0.29."""
    assert metrics.sharpe([0.10, -0.10, 0.10]) == 0.29


def test_g5_sortino() -> None:
    """[G-5] Sortino = 0.58."""
    assert metrics.sortino([0.10, -0.10, 0.10]) == 0.58


def test_g6_trade_stats() -> None:
    """[G-6] ProfitFactor = 1.50 · Expectancy = +25.00."""
    wagers = [
        SettledWager(stake=D("100"), payout=D("250")),
        SettledWager(stake=D("100"), payout=D("0")),
    ]
    stats = metrics.trade_stats(wagers)
    assert stats.win_rate_pct == 50.0
    assert stats.profit_factor == 1.5
    assert stats.expectancy == 25.0


def test_g7_risk_adjusted_score() -> None:
    """[G-7] RAS = 12.00."""
    score = metrics.risk_adjusted_score(twr_pct=15.0, max_drawdown_pct=20.0, sharpe_ratio=1.0)
    assert score == 12.0


def test_g8_vig_and_fair_odds() -> None:
    """[G-8] Vig arındırma ve fair odds."""
    market = odds.normalize_market(
        "1X2", {"HOME": D("1.95"), "DRAW": D("3.50"), "AWAY": D("4.10")}
    )
    assert market.implied == {
        "HOME": D("0.5128205"),
        "DRAW": D("0.2857143"),
        "AWAY": D("0.2439024"),
    }
    assert market.overround == D("0.0424372")
    assert market.margin_pct == D("4.07")
    assert market.fair_prob == {
        "HOME": D("0.4919438"),
        "DRAW": D("0.2740830"),
        "AWAY": D("0.2339733"),
    }
    assert market.fair_odds == {"HOME": D("2.03"), "DRAW": D("3.65"), "AWAY": D("4.27")}


def test_g9_kelly_negative_ev() -> None:
    """[G-9] Fair olasılıkla bahis negatif EV → f* = 0."""
    market = odds.normalize_market("1X2", {"HOME": D("1.95"), "DRAW": D("3.50"), "AWAY": D("4.10")})
    assert odds.kelly_fraction(market.fair_prob["HOME"], D("1.95")) == D("0")


def test_g10_kelly_positive_ev() -> None:
    """[G-10] p=0.55, O=2.10 → f* = %14.09, EV = +%15.50."""
    assert odds.expected_value(D("0.55"), D("2.10")) == D("0.1550")
    fraction = odds.kelly_fraction(D("0.55"), D("2.10"))
    assert q(fraction, D("0.0001")) == D("0.1409")


def test_g11_clv() -> None:
    """[G-11] CLV = +%7.69."""
    assert odds.clv_pct(D("2.10"), D("1.95")) == D("7.69")


def test_g12_energy() -> None:
    """[G-12] Enerji: 10 bahis → 0; 30 dk → +5; 2 saat → +20."""
    energy = energy_mod.MAX_ENERGY
    for _ in range(10):
        energy = energy_mod.spend(energy)
    assert energy == 0
    assert not energy_mod.can_wager(energy)

    half_hour, _ = energy_mod.regen(0, EPOCH, EPOCH + timedelta(minutes=30))
    assert half_hour == 5
    two_hours, _ = energy_mod.regen(0, EPOCH, EPOCH + timedelta(hours=2))
    assert two_hours == 20


def test_g15_energy_cap_rules() -> None:
    """[G-15] Tavanda geçen süre yanar; artık dakikalar saklanır."""
    at_cap, cap_stamp = energy_mod.regen(100, EPOCH, EPOCH + timedelta(hours=3))
    assert (at_cap, cap_stamp) == (100, EPOCH + timedelta(hours=3))

    remainder, stamp = energy_mod.regen(50, EPOCH, EPOCH + timedelta(minutes=100))
    assert (remainder, stamp) == (66, EPOCH + timedelta(minutes=96))


def test_g14_significance_gate() -> None:
    """[G-14] t = SR·√T; t < 2 → anlamsız."""
    assert metrics.sharpe_t_statistic(1.0, 4) == 2.0
    assert metrics.is_statistically_reliable(2.0) is True

    assert metrics.sharpe_t_statistic(1.0, 1) == 1.0
    assert metrics.is_statistically_reliable(1.0) is False

    sharpe_ratio = metrics.sharpe([0.10, -0.10, 0.10])  # [G-4] → 0.29
    assert metrics.sharpe_t_statistic(sharpe_ratio, 3) == 0.5
    assert metrics.is_statistically_reliable(0.5) is False


def test_g13_cooldown() -> None:
    """[G-13] T(n): 1 · 4 · 16 · 64 · 168 (tavan)."""
    assert [cooldown_mod.cooldown_hours(n) for n in (1, 2, 3, 4, 5)] == [
        D("1"),
        D("4"),
        D("16"),
        D("64"),
        D("168"),
    ]
