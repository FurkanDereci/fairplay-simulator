"""Benchmark botları — üç deterministik strateji.

Kritik tasarım: botlar **ayrı durum tutmaz**. NAV eğrileri, maç kayıtlarından
(`MatchRecord`) her seferinde yeniden **türetilir**. Böylece süreç yeniden başladığında
eğriler sıfırlanmaz (devralınan projede bu, bellekte tutulan global state yüzünden bir hataydı).
"""

from __future__ import annotations

import random
from collections.abc import Mapping, Sequence
from decimal import Decimal
from enum import Enum

from ..core.ledger import Ledger
from ..core.money import BASE_NAV, Money, q_money, to_pct
from ..core.nav import Fund
from .match import MatchRecord

BOT_DEPOSIT: Money = Decimal("1000")
BOT_STAKE: Money = Decimal("100")


class BotStrategy(str, Enum):
    RANDOM_WALK = "RANDOM_WALK"
    FAVORITE_HEAVY = "FAVORITE_HEAVY"
    HOME_ADVANTAGE = "HOME_ADVANTAGE"


def _pick(strategy: BotStrategy, odds: Mapping[str, Money], rng: random.Random) -> str:
    if strategy is BotStrategy.RANDOM_WALK:
        return rng.choice(sorted(odds))
    if strategy is BotStrategy.FAVORITE_HEAVY:
        return min(sorted(odds), key=lambda selection: odds[selection])
    return "HOME"


def benchmark_series(
    records: Sequence[MatchRecord],
    *,
    deposit: Money = BOT_DEPOSIT,
    stake: Money = BOT_STAKE,
    seed: int = 0,
) -> dict[BotStrategy, list[Money]]:
    """Her strateji için NAV serisi (ilk değer `BASE_NAV`, sonra maç başına bir nokta)."""
    rng = random.Random(seed)
    ledgers = {strategy: Ledger() for strategy in BotStrategy}
    funds = {strategy: Fund() for strategy in BotStrategy}
    for strategy, ledger in ledgers.items():
        ledger.deposit(deposit)
        funds[strategy].apply(ledger.entries[-1])

    series: dict[BotStrategy, list[Money]] = {strategy: [BASE_NAV] for strategy in BotStrategy}

    for record in records:
        picks = {strategy: _pick(strategy, record.odds_1x2, rng) for strategy in BotStrategy}
        result = record.result
        for strategy, selection in picks.items():
            ledger = ledgers[strategy]
            fund = funds[strategy]
            if fund.cash < stake:
                continue
            wager_id = f"{strategy.value}:{record.match_id}"
            ledger.place_wager(wager_id, stake)
            fund.apply(ledger.entries[-1])

            won = result.outcome_1x2 == selection
            payout = q_money(stake * record.odds_1x2[selection]) if won else Money("0")
            ledger.settle_wager(wager_id, stake, payout)
            fund.apply(ledger.entries[-1])
        for strategy in BotStrategy:
            series[strategy].append(funds[strategy].nav)

    return series


def benchmark_latest(
    records: Sequence[MatchRecord], *, deposit: Money = BOT_DEPOSIT, seed: int = 0
) -> dict[BotStrategy, Money]:
    """Her stratejinin güncel NAV'ı."""
    series = benchmark_series(records, deposit=deposit, seed=seed)
    return {strategy: points[-1] for strategy, points in series.items()}


def benchmark_return_pct(
    records: Sequence[MatchRecord], *, deposit: Money = BOT_DEPOSIT, seed: int = 0
) -> dict[BotStrategy, Money]:
    """Her stratejinin başlangıca göre yüzde getirisi (TWR)."""
    latest = benchmark_latest(records, deposit=deposit, seed=seed)
    return {strategy: to_pct(nav / BASE_NAV - 1) for strategy, nav in latest.items()}
