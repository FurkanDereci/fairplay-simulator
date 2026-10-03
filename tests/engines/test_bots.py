"""S6 — benchmark botları: determinizm, durumsuzluk, strateji davranışı."""

from __future__ import annotations

from decimal import Decimal as D

from fairplay_echo.core.money import Money
from fairplay_echo.engines.bots import BotStrategy, benchmark_latest, benchmark_series
from fairplay_echo.engines.match import MatchRecord


def _record(match_id: str, home: int, away: int, odds: dict[str, Money]) -> MatchRecord:
    return MatchRecord(
        match_id=match_id,
        home_team="Ev",
        away_team="Deplasman",
        home_score=home,
        away_score=away,
        odds_1x2=odds,
        seed=1,
    )


AWAY_FAVOURITE: dict[str, Money] = {"HOME": D("3.00"), "DRAW": D("3.00"), "AWAY": D("1.50")}


def test_series_starts_at_base_nav() -> None:
    assert benchmark_series([]) == {strategy: [D("100")] for strategy in BotStrategy}


def test_series_has_one_point_per_match() -> None:
    records = [_record(f"m{i}", 1, 0, AWAY_FAVOURITE) for i in range(4)]
    series = benchmark_series(records)
    for points in series.values():
        assert len(points) == len(records) + 1


def test_no_hidden_state_same_input_same_output() -> None:
    """Ayrı durum tutulmaz: aynı kayıtlar her seferinde aynı eğriyi üretir (restart güvenli)."""
    records = [_record(f"m{i}", 1, 1, AWAY_FAVOURITE) for i in range(5)]
    assert benchmark_series(records) == benchmark_series(records)


def test_strategies_diverge_on_a_biased_history() -> None:
    """Deplasman favorisi hep kazanıyorsa favori-takip yükselir, ev-takip düşer."""
    records = [_record(f"m{i}", 0, 1, AWAY_FAVOURITE) for i in range(5)]
    latest = benchmark_latest(records)

    assert latest[BotStrategy.FAVORITE_HEAVY] > D("100")
    assert latest[BotStrategy.HOME_ADVANTAGE] < D("100")
    assert latest[BotStrategy.FAVORITE_HEAVY] > latest[BotStrategy.HOME_ADVANTAGE]


def test_bot_stops_betting_when_broke() -> None:
    """Kasa tükenince bot bahis açmaz; NAV eğrisi bozulmaz, sıfıra düşmez."""
    records = [_record(f"m{i}", 0, 1, AWAY_FAVOURITE) for i in range(30)]
    series = benchmark_series(records)
    for points in series.values():
        assert all(point >= 0 for point in points)
    assert series[BotStrategy.HOME_ADVANTAGE][-1] == D("0")


def test_seed_changes_random_walk() -> None:
    records = [_record(f"m{i}", 1, 0, AWAY_FAVOURITE) for i in range(8)]
    assert benchmark_series(records, seed=1) != benchmark_series(records, seed=2)
