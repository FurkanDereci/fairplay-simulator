"""Sınır kararları — "mutation denetimi" yerine elle tutulan çita.

Neden: kapsam yüzdesi `%96` olsa bile `<=` → `<` gibi bir değişiklik **hiçbir testi kırmayabilir**
(alan 1'in tam sorusu). Araç denemesi: `mutmut 3.8` bu ortamda çalışmadı (kopyalama adımı
`/run/udev` symlink döngüsüne giriyor) ve zaten maliyeti ~28 sn × mutant. O yüzden çita **araca**
değil, kritik kararların **sınırına** bağlandı: aşağıdaki her test, tek bir karşılaştırma/sabit
değiştiğinde kırmızıya düşer. Eşleme: `docs/50-test-strategy.md` §9.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal as D

from fairplay_echo.core import cooldown as cooldown_mod
from fairplay_echo.core import energy as energy_mod
from fairplay_echo.core import metrics as metrics_mod
from fairplay_echo.core import money as money_mod
from fairplay_echo.core import odds as odds_mod

T0 = datetime(2026, 1, 1, 12, 0, 0)


def test_money_rounds_half_up_never_half_even() -> None:
    """`ROUND_HALF_UP` → `ROUND_HALF_EVEN` mutantını öldürür (0.125 → 0.13, 0.12 değil)."""
    assert money_mod.q(D("0.125"), D("0.01")) == D("0.13")
    assert money_mod.q(D("1.005"), money_mod.MONEY_Q) == D("1.01")
    assert money_mod.q(D("2.5"), D("1")) == D("3")


def test_money_refuses_float() -> None:
    """`float` sınırı korunmalı: ikili yuvarlama artığı içeri sızamaz."""
    for value in (1, "1.5", D("1.5")):
        assert money_mod.dec(value) == D("1.5") or value == 1
    try:
        money_mod.dec(1.5)  # type: ignore[arg-type]
    except TypeError:
        return
    raise AssertionError("float kabul edildi; ikili artık paraya sızabilir.")


def test_normalize_market_drops_non_positive_odds() -> None:
    """`v > ZERO` → `v >= ZERO` mutantını öldürür (0 oranı 1/0 ile çökertir)."""
    market = odds_mod.normalize_market("1x2", {"H": D("2.0"), "D": D("0"), "A": D("4.0")})
    assert set(market.outcomes) == {"H", "A"}
    assert set(market.fair_prob) == {"H", "A"}


def test_overround_never_goes_negative() -> None:
    """`max(ZERO, total − 1)` mutantını öldürür: implied toplam 1'in altındaysa overround 0'dır."""
    market = odds_mod.normalize_market("1x2", {"H": D("3.0"), "D": D("3.0")})
    assert market.overround == D("0")
    assert market.margin_pct == D("0.00")


def test_normalize_market_survives_an_all_invalid_market() -> None:
    """`total > ZERO` guard'ı mutantını öldürür: 0'a bölme olmamalı."""
    market = odds_mod.normalize_market("1x2", {"H": D("0"), "D": D("0")})
    assert market.outcomes == {}
    assert market.fair_odds == {}
    assert market.overround == D("0")


def test_kelly_returns_exactly_zero_when_there_is_no_edge() -> None:
    """`fraction > ZERO` → `>= ZERO`/kaldır mutantını öldürür: negatif kenar 0 döner.

    Orijinal projedeki `slip-kelly-val` burada 0.05'e düşüyordu (uydurma bahis oranı).
    """
    assert odds_mod.kelly_fraction(D("0.3"), D("2")) == D("0")
    assert odds_mod.kelly_fraction(D("0.5"), D("2")) == D("0")


def test_kelly_guards_odds_at_or_below_one() -> None:
    """`odds <= ONE` → `<` mutantını öldürür: o = 1 sıfıra bölme değil, 0'dır."""
    assert odds_mod.kelly_fraction(D("1"), D("1")) == D("0")
    assert odds_mod.kelly_fraction(D("0.9"), D("0.5")) == D("0")


def test_clv_guards_a_zero_closing_odds() -> None:
    """`closing_odds <= ZERO` guard mutantını öldürür."""
    assert odds_mod.clv_pct(D("2.0"), D("0")) == D("0")


def test_wager_is_allowed_at_exactly_the_cost() -> None:
    """`energy >= cost` → `>` mutantını öldürür."""
    assert energy_mod.can_wager(10) is True
    assert energy_mod.can_wager(9) is False


def test_spend_never_goes_below_zero() -> None:
    """`max(0, …)` mutantını öldürür."""
    assert energy_mod.spend(5) == 0
    assert energy_mod.spend(10) == 0


def test_cooldown_tier_zero_is_free_and_tier_one_is_not() -> None:
    """`tier < 1` → `tier <= 1` mutantını öldürür."""
    assert cooldown_mod.cooldown_hours(0) == 0
    assert cooldown_mod.cooldown_hours(1) == 1


def test_unlock_happens_at_the_exact_expiry_instant() -> None:
    """`is_locked` (`<`) ve `unlock_if_expired` (`>=`) mutantlarını öldürür."""
    state = cooldown_mod.CooldownState(tier=1, locked_until=T0)

    assert state.is_locked(T0) is False, "tam bitiş anında kilit yok"
    assert state.unlock_if_expired(T0) is True
    assert state.locked_until is None

    fresh = cooldown_mod.CooldownState(tier=1, locked_until=T0 + timedelta(seconds=1))
    assert fresh.is_locked(T0) is True
    assert fresh.unlock_if_expired(T0) is False


def test_solvent_day_streak_drops_the_tier_at_exactly_three() -> None:
    """`streak >= 3` → `>` mutantını öldürür (3. gün tier'ı düşürür)."""
    assert cooldown_mod.record_solvent_day(0, 2) == (1, 2)
    assert cooldown_mod.record_solvent_day(2, 2) == (0, 1)


def test_sharpe_t_statistic_guards_a_zero_period_count() -> None:
    """`periods <= 0` guard mutantını öldürür."""
    assert metrics_mod.sharpe_t_statistic(1.0, 0) == 0.0
    assert metrics_mod.sharpe_t_statistic(1.0, -3) == 0.0
