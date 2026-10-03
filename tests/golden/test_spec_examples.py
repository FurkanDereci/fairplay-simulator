"""Spec işlenmiş örnekleri — `docs/20-accounting-spec.md` §1–§4.

Her test bir `[G-x]` kimliği taşır; `tests/test_docs_sync.py` bu kimliklerin spec ile birebir
örtüşmesini zorlar. Spec'teki sayı değişirse bu test kırılır.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal as D

import pytest

from fairplay_simulator.core import cooldown as cooldown_mod
from fairplay_simulator.core import energy as energy_mod
from fairplay_simulator.core import metrics, nav, odds
from fairplay_simulator.core.errors import InvalidOdds
from fairplay_simulator.core.learning import (
    BADGE_CLV_MASTER,
    BADGE_MARKET_BREADTH,
    BADGE_STAKE_DISCIPLINE,
    BetInput,
    build_learning_report,
    earned_badges,
    earns_discipline_discount,
)
from fairplay_simulator.core.ledger import Ledger
from fairplay_simulator.core.metrics import SettledWager
from fairplay_simulator.core.money import Money, q, q_nav, q_units

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


def test_g17_risk_of_ruin() -> None:
    """[G-17] R_ruin = ((1−Edge)/(1+Edge))^Units; kenar yoksa iflas kaçınılmaz."""
    assert odds.risk_of_ruin(D("0.01"), D("100")) == D("13.53")
    assert odds.risk_of_ruin(D("0.00"), D("100")) == D("100.00")


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


def test_g16_learning_metrics() -> None:
    """[G-16] Öğrenme ölçütleri: CLV eğilimi, bahis oranı, favori payı."""
    ledger = Ledger()
    ledger.deposit(D("1000"))
    closings = ["2.10", "2.05", "2.00", "1.95", "1.90", "1.85"]
    for index in range(1, 7):
        wager_id = f"b{index}"
        ledger.place_wager(wager_id, D("100"))
        ledger.settle_wager(wager_id, D("100"), D("100"))  # push: net 0, portföy sabit

    bets = {
        f"b{index}": BetInput(f"b{index}", "1x2", D("2.00"), D(closing))
        for index, closing in enumerate(closings, start=1)
    }
    report = build_learning_report(ledger.entries, bets)

    assert report.bets == 6
    assert report.reliable is True
    assert report.clv_first_half_pct == D("-2.40")
    assert report.clv_second_half_pct == D("5.31")
    assert report.clv_mean_pct == D("1.46")
    assert report.clv_trend == "iyileşiyor"
    assert report.mean_stake_ratio_pct == D("10.00")
    assert report.stake_verdict == "ölçülü"
    assert report.favourite_share_pct == D("0.00")
    assert report.favourite_verdict == "dengeli"
    assert report.headline == "CLV eğilimi yukarı"


def test_g16_thin_sample_reads_no_trend() -> None:
    """[G-16] `N < 6` iken eğilim okunmaz — alan 3'ün örneklem kuralının ikizi."""
    ledger = Ledger()
    ledger.deposit(D("1000"))
    for index in range(3):
        ledger.place_wager(f"t{index}", D("100"))
    bets = {
        f"t{index}": BetInput(f"t{index}", "1x2", D("2.00"), D("2.10")) for index in range(3)
    }

    report = build_learning_report(ledger.entries, bets)
    assert report.reliable is False
    assert report.clv_trend == "örneklem yetersiz"
    assert report.clv_first_half_pct is None
    assert "Örneklem yetersiz (3/6)" in report.headline


def test_g16_headline_writes_percentages_in_turkish() -> None:
    """[G-16] Metindeki yüzde tr-TR yazılır (virgül) ve ek uyumu bozulmaz."""
    ledger = Ledger()
    ledger.deposit(D("1000"))
    for index in range(6):
        ledger.place_wager(f"h{index}", D("166"))  # 166/1000 = %16,60 > %15
    bets = {
        f"h{index}": BetInput(f"h{index}", "1x2", D("1.50"), D("1.60")) for index in range(6)
    }

    report = build_learning_report(ledger.entries, bets)
    assert report.stake_verdict == "aşırı"
    assert report.favourite_verdict == "favori ağırlıklı"
    assert "portföyün %16,60 seviyesinde" in report.headline
    assert "sınır %15,00" in report.headline
    assert "favori oranı %100,00" in report.headline
    assert "%16.60" not in report.headline, "yüzde noktayla yazılmamalı (tr-TR)"


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


def test_g18_discipline_discount() -> None:
    """[G-18] 3+ rozet tavanı 72'ye çeker; tier 4 (64) indirimden etkilenmez."""
    discounted = D("72")
    assert [cooldown_mod.cooldown_hours(n, max_hours=discounted) for n in (3, 4, 5)] == [
        D("16"),
        D("64"),
        D("72"),
    ]
    assert cooldown_mod.cooldown_hours(5) == D("168")  # indirimsiz varsayılan


def test_g18_badges_are_derived_from_measured_metrics() -> None:
    """[G-18] Rozetler **var olan** ölçütlerden türetilir; üçü birlikte indirimi açar."""
    ledger = Ledger()
    ledger.deposit(D("1000"))
    for index in range(6):
        ledger.place_wager(f"b{index}", D("50"))  # 50/1000 = %5 → ölçülü
        ledger.settle_wager(f"b{index}", D("50"), D("50"))  # push: portföy değeri sabit

    markets = ["1x2", "ou", "btts", "1x2", "ou", "btts"]  # 3 farklı pazar
    bets = {
        f"b{index}": BetInput(f"b{index}", market, D("2.00"), D("1.90"))
        for index, market in enumerate(markets)
    }
    badges = earned_badges(build_learning_report(ledger.entries, bets))

    assert BADGE_STAKE_DISCIPLINE in badges
    assert BADGE_CLV_MASTER in badges  # 2.00 → 1.90: CLV pozitif
    assert BADGE_MARKET_BREADTH in badges
    assert earns_discipline_discount(badges) is True


def test_g18_no_badges_from_a_thin_sample() -> None:
    """[G-18] Az örneklemden rozet verilmez (`[G-14]` sınıfının ikizi)."""
    ledger = Ledger()
    ledger.deposit(D("1000"))
    for index in range(3):
        ledger.place_wager(f"t{index}", D("10"))
    bets = {
        f"t{index}": BetInput(f"t{index}", "1x2", D("2.00"), D("1.90")) for index in range(3)
    }
    assert earned_badges(build_learning_report(ledger.entries, bets)) == ()
    assert earns_discipline_discount([]) is False


def test_g19_odds_sanitation_rejects_corrupt_feeds() -> None:
    """[G-19] Bozuk/negatif vig'li oran **reddedilir**; geçerli dizi kabul edilir."""
    # Sağlam: Σ(1/O) > 1 → kabul.
    odds.validate_market_odds("1X2", {"HOME": D("1.95"), "DRAW": D("3.50"), "AWAY": D("4.10")})

    # Negatif vig: Σ(1/O) = 0.857143 ≤ 1 → reddedilir.
    with pytest.raises(InvalidOdds):
        odds.validate_market_odds("1X2", {"HOME": D("3.50"), "DRAW": D("3.50"), "AWAY": D("3.50")})

    # O ≤ 1: matematiksel olarak imkânsız oran → reddedilir.
    with pytest.raises(InvalidOdds):
        odds.validate_market_odds("1X2", {"HOME": D("1.00"), "DRAW": D("2.00"), "AWAY": D("3.00")})

    # Eksik sonuç: 1X2 için DRAW yok → reddedilir.
    with pytest.raises(InvalidOdds):
        odds.validate_market_odds("1X2", {"HOME": D("1.95"), "AWAY": D("4.10")})
