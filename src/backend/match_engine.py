import math
import random
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple

@dataclass
class MatchEvent:
    minute: int
    event_type: str  # 'GOAL', 'YELLOW_CARD', 'RED_CARD'
    team: str        # 'HOME', 'AWAY'
    description: str

@dataclass
class MatchResult:
    match_id: str
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    total_goals: int
    outcome_1x2: str          # 'HOME', 'DRAW', 'AWAY'
    outcome_ou_25: str        # 'OVER_2.5', 'UNDER_2.5'
    outcome_btts: str         # 'BTTS_YES', 'BTTS_NO'
    lambda_home: float
    lambda_away: float
    events: List[MatchEvent] = field(default_factory=list)

@dataclass
class MonteCarloDistribution:
    iterations: int
    home_win_pct: float
    draw_pct: float
    away_win_pct: float
    over_25_pct: float
    under_25_pct: float
    btts_pct: float
    fair_odds_1x2: Dict[str, float]
    fair_odds_ou_25: Dict[str, float]

class VirtualMatchEngine:
    """High-performance Poisson and Monte Carlo Simulation Engine for Football Fixtures."""

    @staticmethod
    def sample_poisson(lam: float, rng: Optional[random.Random] = None) -> int:
        """Knuth's algorithm for generating Poisson-distributed random integers."""
        if lam <= 0:
            return 0
        r = rng if rng is not None else random
        L = math.exp(-lam)
        k = 0
        p = 1.0
        while p > L:
            k += 1
            p *= r.random()
        return k - 1

    @classmethod
    def derive_lambdas(cls, odds_1x2: Dict[str, float], total_expected_goals: float = 2.70) -> Tuple[float, float]:
        """Derives Home and Away Poisson lambda parameters from 1X2 market odds."""
        o_h = max(1.01, odds_1x2.get("HOME", 2.50))
        o_d = max(1.01, odds_1x2.get("DRAW", 3.20))
        o_a = max(1.01, odds_1x2.get("AWAY", 2.90))

        imp_h = 1.0 / o_h
        imp_d = 1.0 / o_d
        imp_a = 1.0 / o_a
        total_imp = imp_h + imp_d + imp_a

        p_h = imp_h / total_imp
        p_a = imp_a / total_imp

        # Ratio of goal expectations
        ratio = (p_h + 0.1) / (p_a + 0.1)
        lambda_h = round(total_expected_goals * (ratio / (1.0 + ratio)), 3)
        lambda_a = round(total_expected_goals - lambda_h, 3)

        # Minimum clamp to prevent zero-intensity deadlocks
        lambda_h = max(0.25, lambda_h)
        lambda_a = max(0.25, lambda_a)
        return lambda_h, lambda_a

    @classmethod
    def simulate_match(
        cls,
        match_id: str,
        home_team: str,
        away_team: str,
        odds_1x2: Optional[Dict[str, float]] = None,
        lambda_home: Optional[float] = None,
        lambda_away: Optional[float] = None,
        seed: Optional[int] = None
    ) -> MatchResult:
        """Simulates a 90-minute match generating goal counts and timeline events."""
        rng = random.Random(seed) if seed is not None else random.Random()

        if lambda_home is None or lambda_away is None:
            lh, la = cls.derive_lambdas(odds_1x2 or {"HOME": 2.0, "DRAW": 3.4, "AWAY": 3.8})
        else:
            lh, la = lambda_home, lambda_away

        home_score = cls.sample_poisson(lh, rng)
        away_score = cls.sample_poisson(la, rng)
        total_goals = home_score + away_score

        # Determine outcomes
        if home_score > away_score:
            outcome_1x2 = "HOME"
        elif home_score < away_score:
            outcome_1x2 = "AWAY"
        else:
            outcome_1x2 = "DRAW"

        outcome_ou = "OVER_2.5" if total_goals > 2 else "UNDER_2.5"
        outcome_btts = "BTTS_YES" if home_score > 0 and away_score > 0 else "BTTS_NO"

        # Generate timeline events
        events: List[MatchEvent] = []
        for _ in range(home_score):
            minute = rng.randint(1, 90)
            events.append(MatchEvent(minute=minute, event_type="GOAL", team="HOME", description=f"Goal for {home_team}!"))
        for _ in range(away_score):
            minute = rng.randint(1, 90)
            events.append(MatchEvent(minute=minute, event_type="GOAL", team="AWAY", description=f"Goal for {away_team}!"))

        # Sort chronologically
        events.sort(key=lambda e: e.minute)

        return MatchResult(
            match_id=match_id,
            home_team=home_team,
            away_team=away_team,
            home_score=home_score,
            away_score=away_score,
            total_goals=total_goals,
            outcome_1x2=outcome_1x2,
            outcome_ou_25=outcome_ou,
            outcome_btts=outcome_btts,
            lambda_home=lh,
            lambda_away=la,
            events=events
        )

    @classmethod
    def run_monte_carlo(
        cls,
        lambda_home: float,
        lambda_away: float,
        iterations: int = 10000,
        seed: Optional[int] = 42
    ) -> MonteCarloDistribution:
        """Runs N Poisson Monte Carlo simulations to calculate empirical probabilities and vig-free fair odds."""
        rng = random.Random(seed)
        home_wins = 0
        draws = 0
        away_wins = 0
        over_25 = 0
        btts = 0

        for _ in range(iterations):
            gh = cls.sample_poisson(lambda_home, rng)
            ga = cls.sample_poisson(lambda_away, rng)
            if gh > ga:
                home_wins += 1
            elif gh < ga:
                away_wins += 1
            else:
                draws += 1

            if (gh + ga) > 2:
                over_25 += 1
            if gh > 0 and ga > 0:
                btts += 1

        p_h = home_wins / iterations
        p_d = draws / iterations
        p_a = away_wins / iterations
        p_over = over_25 / iterations
        p_under = 1.0 - p_over

        return MonteCarloDistribution(
            iterations=iterations,
            home_win_pct=round(p_h * 100.0, 2),
            draw_pct=round(p_d * 100.0, 2),
            away_win_pct=round(p_a * 100.0, 2),
            over_25_pct=round(p_over * 100.0, 2),
            under_25_pct=round(p_under * 100.0, 2),
            btts_pct=round((btts / iterations) * 100.0, 2),
            fair_odds_1x2={
                "HOME": round(1.0 / p_h, 2) if p_h > 0 else 999.0,
                "DRAW": round(1.0 / p_d, 2) if p_d > 0 else 999.0,
                "AWAY": round(1.0 / p_a, 2) if p_a > 0 else 999.0
            },
            fair_odds_ou_25={
                "OVER_2.5": round(1.0 / p_over, 2) if p_over > 0 else 999.0,
                "UNDER_2.5": round(1.0 / p_under, 2) if p_under > 0 else 999.0
            }
        )
