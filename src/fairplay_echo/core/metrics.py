"""Risk ve performans metrikleri — spec §2.

İstatistik olduğu için `float` döner; para tarafı `Decimal` kalır. Yetersiz örnekte 0 döner,
asla çökmez. Örnek/varyans kuralları spec'te açıkça yazılıdır ve burada birebir uygulanır.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from itertools import pairwise

from .money import ZERO, Money

_EPS = 1e-6

# Sharpe'ın kendi bağıntısı: `t = SR·√T`. Anlamlılık için `t ≥ 2` (bkz. `docs/20` §2.8).
MIN_T_STATISTIC = 2.0


def sharpe_t_statistic(sharpe_ratio: float, periods: int) -> float:
    """Ortalamanın t istatistiği: `SR × √T` (T = getiri dönemi sayısı).

    Yetersiz örneklemde Sharpe bir *sayı* olarak görünür ama **anlamlı değildir**;
    bu fonksiyon o ayrımı ölçülebilir kılar.
    """
    if periods <= 0:
        return 0.0
    return round(sharpe_ratio * math.sqrt(periods), 2)


def is_statistically_reliable(
    t_statistic: float, *, minimum: float = MIN_T_STATISTIC
) -> bool:
    """`t ≥ 2` mi? Değilse metrik yorumlanmamalı."""
    return t_statistic >= minimum


@dataclass(frozen=True)
class SettledWager:
    """İşlem istatistikleri için minimal girdi. Kazanç/kayıp `net` işaretinden türer."""

    stake: Money
    payout: Money

    @property
    def net(self) -> Money:
        return self.payout - self.stake


@dataclass(frozen=True)
class TradeStats:
    total_trades: int
    win_rate_pct: float
    profit_factor: float
    gross_profit: float
    gross_loss: float
    avg_win: float
    avg_loss: float
    expectancy: float


def returns_series(nav: Sequence[Money]) -> list[float]:
    """Dönemsel kesirli getiriler; önceki değer ≤ 0 ise 0."""
    out: list[float] = []
    for prev, curr in pairwise(nav):
        out.append((float(curr) - float(prev)) / float(prev) if prev > 0 else 0.0)
    return out


def _mean(xs: Sequence[float]) -> float:
    return sum(xs) / len(xs)


def max_drawdown_pct(nav: Sequence[Money]) -> float:
    """Zirveden dibe en büyük düşüş (%)."""
    if not nav:
        return 0.0
    peak = float(nav[0])
    worst = 0.0
    for value in nav:
        current = float(value)
        peak = max(peak, current)
        if peak > 0:
            worst = max(worst, (peak - current) / peak)
    return round(worst * 100.0, 2)


def sharpe(returns: Sequence[float], risk_free_rate: float = 0.0) -> float:
    """Sharpe oranı; örneklem standart sapması (n−1)."""
    if len(returns) < 2:
        return 0.0
    mu = _mean(returns)
    excess = mu - risk_free_rate
    variance = sum((r - mu) ** 2 for r in returns) / (len(returns) - 1)
    sd = math.sqrt(variance) if variance > 0 else 0.0
    if sd <= _EPS:
        return round(excess * 10.0, 2) if excess > 0 else 0.0
    return round(excess / sd, 2)


def sortino(returns: Sequence[float], target_return: float = 0.0) -> float:
    """Sortino oranı; aşağı yönlü sapma, n'e bölünür."""
    if len(returns) < 2:
        return 0.0
    mu = _mean(returns)
    excess = mu - target_return
    downside = sum(min(0.0, r - target_return) ** 2 for r in returns) / len(returns)
    dd = math.sqrt(downside) if downside > 0 else 0.0
    if dd <= _EPS:
        return round(excess * 10.0, 2) if excess > 0 else 0.0
    return round(excess / dd, 2)


def beta_alpha(
    player_returns: Sequence[float],
    benchmark_returns: Sequence[float],
    risk_free_rate: float = 0.0,
) -> tuple[float, float]:
    """Portföy Beta ve Jensen Alpha (benchmark'a karşı)."""
    n = min(len(player_returns), len(benchmark_returns))
    if n < 3:
        return (1.0, 0.0)
    rp = player_returns[-n:]
    rb = benchmark_returns[-n:]
    mean_p = _mean(rp)
    mean_b = _mean(rb)
    var_b = sum((b - mean_b) ** 2 for b in rb) / (n - 1)
    if var_b <= _EPS:
        return (1.0, round((mean_p - mean_b) * 100.0, 2))
    cov = sum((rp[i] - mean_p) * (rb[i] - mean_b) for i in range(n)) / (n - 1)
    beta = cov / var_b
    alpha = (mean_p - risk_free_rate) - beta * (mean_b - risk_free_rate)
    return (round(beta, 2), round(alpha * 100.0, 2))


def trade_stats(wagers: Sequence[SettledWager]) -> TradeStats:
    """Kazanç/kayıp **net** işaretinden türetilir; `net = 0` (VOID/PUSH) hariç tutulur."""
    settled = [w for w in wagers if w.net != ZERO]
    total = len(settled)
    if total == 0:
        return TradeStats(0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    wins = [w for w in settled if w.net > ZERO]
    losses = [w for w in settled if w.net < ZERO]

    gross_profit = sum(float(w.net) for w in wins)
    gross_loss = -sum(float(w.net) for w in losses)
    win_rate = len(wins) / total * 100.0

    if gross_loss > 0:
        profit_factor = gross_profit / gross_loss
    else:
        profit_factor = 99.0 if gross_profit > 0 else 0.0

    avg_win = gross_profit / len(wins) if wins else 0.0
    avg_loss = gross_loss / len(losses) if losses else 0.0
    expectancy = sum(float(w.net) for w in settled) / total

    return TradeStats(
        total_trades=total,
        win_rate_pct=round(win_rate, 2),
        profit_factor=round(profit_factor, 2),
        gross_profit=round(gross_profit, 2),
        gross_loss=round(gross_loss, 2),
        avg_win=round(avg_win, 2),
        avg_loss=round(avg_loss, 2),
        expectancy=round(expectancy, 2),
    )


def risk_adjusted_score(twr_pct: float, max_drawdown_pct: float, sharpe_ratio: float) -> float:
    """Bütünleşik fon yöneticisi puanı — spec §2.7."""
    drawdown_factor = max(0.0, 1.0 - max_drawdown_pct / 100.0)
    sharpe_factor = min(2.5, max(0.2, (sharpe_ratio + 1.0) / 2.0))
    return round(twr_pct * drawdown_factor * sharpe_factor, 2)
