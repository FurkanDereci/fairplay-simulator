from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class NormalizedMarket:
    market_type: str  # '1X2', 'OVER_UNDER_2.5', etc.
    outcomes: Dict[str, float]  # e.g. {"HOME": 1.90, "DRAW": 3.60, "AWAY": 4.20}
    implied_probabilities: Dict[str, float]
    overround: float  # Excess over 1.0 (e.g. 0.0422 for 4.22% vig)
    bookmaker_margin_pct: float  # Margin %
    fair_odds: Dict[str, float]  # Vig-free fair odds

class OddsNormalizer:
    @staticmethod
    def normalize_market(market_type: str, outcomes: Dict[str, float]) -> NormalizedMarket:
        """Normalizes decimal odds, computes implied probabilities, overround/vig, and fair odds."""
        implied = {k: 1.0 / v for k, v in outcomes.items() if v > 0}
        total_implied = sum(implied.values())
        overround = max(0.0, total_implied - 1.0)
        margin_pct = (overround / total_implied) * 100.0 if total_implied > 0 else 0.0
        
        fair_probs = {k: v / total_implied for k, v in implied.items()}
        fair_odds = {k: round(1.0 / fp, 2) for k, fp in fair_probs.items()}
        
        return NormalizedMarket(
            market_type=market_type,
            outcomes=outcomes,
            implied_probabilities={k: round(v, 4) for k, v in implied.items()},
            overround=round(overround, 4),
            bookmaker_margin_pct=round(margin_pct, 2),
            fair_odds=fair_odds
        )
