"""Değişmezler (I1–I6) — property tabanlı.

Her test bir `I<n>` kimliği taşır; `tests/test_docs_sync.py` bunların `docs/10-domain-model.md`
§3 ile örtüşmesini zorlar.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal as D

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from fairplay_echo.core import cooldown as cooldown_mod
from fairplay_echo.core import energy as energy_mod
from fairplay_echo.core.errors import AlreadySettled
from fairplay_echo.core.ledger import EntryType, Ledger, LedgerEntry
from fairplay_echo.core.money import BASE_NAV, ZERO, Money, q_money
from fairplay_echo.core.nav import Fund

EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)
_SETTINGS = settings(max_examples=60, deadline=None, suppress_health_check=[HealthCheck.too_slow])


@st.composite
def generated_funds(draw: st.DataObject) -> tuple[Ledger, Fund]:
    """Geçerli bir komut dizisinden defter + artımlı projeksiyon üretir."""
    ledger = Ledger()
    fund = Fund()
    ledger.deposit(D("1000"))
    fund.apply(ledger.entries[-1])

    next_wager = 0
    for _ in range(draw(st.integers(min_value=0, max_value=12))):
        if draw(st.booleans()):
            ledger.refill(D(draw(st.integers(min_value=1, max_value=2000))))
            fund.apply(ledger.entries[-1])
            continue

        stake = D(draw(st.integers(min_value=1, max_value=1000)))
        if stake > fund.cash:
            continue
        next_wager += 1
        wager_id = f"w{next_wager}"

        ledger.place_wager(wager_id, stake)
        fund.apply(ledger.entries[-1])

        payout = q_money(stake * D("2")) if draw(st.booleans()) else ZERO
        ledger.settle_wager(wager_id, stake, payout)
        fund.apply(ledger.entries[-1])

    return ledger, fund


@given(case=generated_funds())
@_SETTINGS
def test_i1_refill_invariance(case: tuple[Ledger, Fund]) -> None:
    """I1 — Refill öncesi ve sonrası NAV eşit; yalnız birim sayısı değişir."""
    ledger, fund = case
    if fund.closed or fund.units <= ZERO:
        return
    nav_before = fund.nav
    units_before = fund.units

    ledger.refill(D("500"))
    fund.apply(ledger.entries[-1])

    assert fund.nav == nav_before
    assert fund.units > units_before


@given(case=generated_funds())
@_SETTINGS
def test_i2_replay_reproduces_state(case: tuple[Ledger, Fund]) -> None:
    """I2 — Artımlı uygulama ile baştan `replay` birebir aynı durumu üretir."""
    ledger, fund = case
    replayed = Fund.replay(ledger.entries)

    assert replayed.cash == fund.cash
    assert replayed.locked == fund.locked
    assert replayed.units == fund.units
    assert replayed.nav == fund.nav
    assert replayed.series_id == fund.series_id
    assert replayed.series_growth == fund.series_growth
    assert replayed.twr == fund.twr
    assert replayed.open_wagers == fund.open_wagers


@given(case=generated_funds())
@_SETTINGS
def test_i2_nav_times_units_equals_value(case: tuple[Ledger, Fund]) -> None:
    """I2 — `NAV × U = Cash + Exposure` (Suite 2).

    `nav = V/U` bölmesi 28 basamakta tam olmadığı için kimlik **para kuantumunda** karşılaştırılır;
    ölçülen sapma yuvarlama artığıdır, ihlal değil.
    """
    _ledger, fund = case
    if fund.units <= ZERO:
        return
    assert fund.total_value == fund.cash + fund.locked
    assert q_money(fund.nav * fund.units) == q_money(fund.total_value)


@given(case=generated_funds())
@_SETTINGS
def test_i3_settlement_is_idempotent(case: tuple[Ledger, Fund]) -> None:
    """I3 — Sonuçlanmış kupon ikinci kez uygulanamaz; durum değişmez."""
    _ledger, fund = case
    if not fund.settled_wagers:
        return
    wager_id = sorted(fund.settled_wagers)[0]
    before = (fund.cash, fund.locked, fund.units, fund.nav, fund.series_growth)

    duplicate = LedgerEntry(
        seq=10_000,
        entry_type=EntryType.WAGER_SETTLED,
        amount=ZERO,
        stake=ZERO,
        wager_id=wager_id,
    )
    with pytest.raises(AlreadySettled):
        fund.apply(duplicate)

    assert (fund.cash, fund.locked, fund.units, fund.nav, fund.series_growth) == before


@given(case=generated_funds())
@_SETTINGS
def test_i4_bankruptcy_is_permanent(case: tuple[Ledger, Fund]) -> None:
    """I4 — Yeni seri açan bir iflas, büyüme çarpanını sıfırlar; TWR −100% kalır."""
    _ledger, fund = case
    if fund.series_id <= 1:
        return
    assert fund.series_growth == ZERO
    assert fund.twr == D("-100.00")


@given(
    energy=st.integers(min_value=0, max_value=100),
    seconds=st.integers(min_value=0, max_value=20_000),
)
@_SETTINGS
def test_i5_energy_is_monotone_and_bounded(energy: int, seconds: int) -> None:
    """I5 — Geçen süre enerjiyi azaltmaz; tavan 100 aşılmaz."""
    refreshed, _ = energy_mod.regen(energy, EPOCH, EPOCH + timedelta(seconds=seconds))
    assert energy <= refreshed <= energy_mod.MAX_ENERGY


def test_i5_energy_gate_below_cost() -> None:
    """I5 — Eşiğin (10) altında bahis reddedilir, eşikte kabul edilir."""
    assert not energy_mod.can_wager(energy_mod.COST_PER_WAGER - 1)
    assert energy_mod.can_wager(energy_mod.COST_PER_WAGER)


@given(tier=st.integers(min_value=1, max_value=20))
@_SETTINGS
def test_i6_cooldown_grows_and_caps(tier: int) -> None:
    """I6 — T(n)=min(168, 4^(n−1)) ve tavan 168."""
    hours: Money = cooldown_mod.cooldown_hours(tier)
    assert ZERO < hours <= cooldown_mod.MAX_COOLDOWN_HOURS
    assert hours == min(cooldown_mod.MAX_COOLDOWN_HOURS, D("4") ** (tier - 1))


@given(tier=st.integers(min_value=0, max_value=5))
@_SETTINGS
def test_i6_solvent_days_decay_tier(tier: int) -> None:
    """I6 — 3 ardışık solvent gün tier'ı bir düşürür, taban 0."""
    streak = 0
    current = tier
    for _ in range(cooldown_mod.SOLVENT_DAYS_PER_TIER):
        streak, current = cooldown_mod.record_solvent_day(streak, current)
    assert current == max(0, tier - 1)
    assert streak == 0


@given(tier=st.integers(min_value=1, max_value=20), cap=st.sampled_from([D("72"), D("168")]))
@_SETTINGS
def test_i6_discipline_discount_caps_the_cooldown(tier: int, cap: D) -> None:
    """I6 — disiplin indirimi yalnız **tavanı** düşürür: `min(tavan, 4^(n−1))` formülü korunur."""
    hours: Money = cooldown_mod.cooldown_hours(tier, max_hours=cap)
    assert ZERO < hours <= cap
    assert hours == min(cap, D("4") ** (tier - 1))


def test_base_nav_is_one_hundred() -> None:
    """I1 — Başlangıç NAV sabiti 100 dür (spec §1)."""
    assert D("100") == BASE_NAV
