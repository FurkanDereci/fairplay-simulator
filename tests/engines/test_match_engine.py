"""S5 — maç motoru: determinizm, tutarlılık, λ türetme."""

from __future__ import annotations

from decimal import Decimal as D

import pytest

from fairplay_simulator.core.money import Money
from fairplay_simulator.engines.match import (
    BTTS_NO,
    BTTS_YES,
    MARKET_1X2,
    OVER,
    UNDER,
    MatchResult,
    derive_lambdas,
    run_monte_carlo,
    simulate_match,
)

ODDS_1X2: dict[str, Money] = {"HOME": D("1.95"), "DRAW": D("3.50"), "AWAY": D("4.10")}


def _simulate(seed: int) -> MatchResult:
    return simulate_match("m1", "Ev", "Deplasman", ODDS_1X2, seed=seed)


def test_same_seed_same_result() -> None:
    """Aynı seed → aynı skor (ADR-0003)."""
    assert _simulate(42) == _simulate(42)
    assert _simulate(7).home_score == _simulate(7).home_score


def test_seed_actually_varies() -> None:
    """Farklı seed'ler tek bir skora kilitlenmez."""
    results = {(r.home_score, r.away_score) for r in (_simulate(s) for s in range(24))}
    assert len(results) > 1


def test_lambda_favourite_gets_more() -> None:
    """Favori (daha düşük oran) daha yüksek λ alır, toplam lig ortalamasına yakın."""
    lambda_home, lambda_away = derive_lambdas(ODDS_1X2)
    assert lambda_home > lambda_away
    assert lambda_home + lambda_away == pytest.approx(2.6, abs=0.01)


def test_match_events_match_the_scoreline() -> None:
    """Olay sayısı gol sayısına eşit; dakikalar 1–90 arası ve sıralı."""
    for seed in range(12):
        result = _simulate(seed)
        assert len(result.events) == result.home_score + result.away_score
        minutes = [event.minute for event in result.events]
        assert minutes == sorted(minutes)
        assert all(1 <= minute <= 90 for minute in minutes)
        assert all(event.event_type == "GOAL" for event in result.events)


def test_match_events_are_deterministic_and_track_the_running_score() -> None:
    first = _simulate(42)
    assert first.events == _simulate(42).events

    home = away = 0
    for event in first.events:
        home += event.team == first.home_team
        away += event.team == first.away_team
        assert f"({home}-{away})" in event.description
    assert (home, away) == (first.home_score, first.away_score)


def test_outcomes_follow_the_score() -> None:
    """Sonuç etiketleri skordan tutarlı türetilir."""
    home_win = MatchResult("m", "A", "B", 2, 1)
    assert home_win.outcome_1x2 == "HOME"
    assert home_win.outcome_ou_25 == OVER
    assert home_win.outcome_btts == BTTS_YES

    goalless_draw = MatchResult("m", "A", "B", 0, 0)
    assert goalless_draw.outcome_1x2 == "DRAW"
    assert goalless_draw.outcome_ou_25 == UNDER
    assert goalless_draw.outcome_btts == BTTS_NO

    away_win = MatchResult("m", "A", "B", 0, 2)
    assert away_win.outcome_1x2 == "AWAY"


def test_outcome_for_unknown_market_raises() -> None:
    with pytest.raises(ValueError, match="Bilinmeyen market"):
        MatchResult("m", "A", "B", 1, 0).outcome_for("HANDIKAP")


def test_outcome_for_matches_market() -> None:
    result = MatchResult("m", "A", "B", 1, 0)
    assert result.outcome_for(MARKET_1X2) == result.outcome_1x2


def test_monte_carlo_is_deterministic_and_normalised() -> None:
    first = run_monte_carlo(1.6, 1.0, 2_000, seed=99)
    second = run_monte_carlo(1.6, 1.0, 2_000, seed=99)
    assert first == second

    total = first.home_win_pct + first.draw_pct + first.away_win_pct
    assert total == pytest.approx(100.0, abs=0.05)
    assert first.iterations == 2_000
    assert 0.0 <= first.btts_pct <= 100.0


def test_monte_carlo_rejects_empty_run() -> None:
    with pytest.raises(ValueError, match="iterations"):
        run_monte_carlo(1.0, 1.0, 0, seed=1)
