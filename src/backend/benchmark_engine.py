import random
from typing import Dict, Any, List, Optional, Tuple
from src.backend.nav_engine import NAVPortfolioEngine

class BenchmarkBot:
    """Simulates an automated trading/betting bot executing a specific systematic strategy."""

    def __init__(self, name: str, strategy_type: str, initial_balance: float = 1000.0, base_nav: float = 100.0):
        self.name = name
        self.strategy_type = strategy_type  # 'RANDOM', 'FAVORITE', 'HOME_BIAS'
        self.portfolio = NAVPortfolioEngine(initial_balance=initial_balance, base_nav=base_nav)
        self.active_wagers: Dict[str, Tuple[str, float, float]] = {}  # match_id -> (selection, stake, odds)

    def pick_selection(self, market_1x2: Dict[str, float], seed: Optional[int] = None) -> Tuple[str, float]:
        """Picks an outcome and returns (selection, odds) based on strategy."""
        o_h = market_1x2.get("HOME", 2.0)
        o_d = market_1x2.get("DRAW", 3.2)
        o_a = market_1x2.get("AWAY", 3.5)

        if self.strategy_type == "HOME_BIAS":
            return "HOME", o_h
        elif self.strategy_type == "FAVORITE":
            # Pick lowest odds (strongest favorite)
            odds_map = {"HOME": o_h, "DRAW": o_d, "AWAY": o_a}
            fav_selection = min(odds_map, key=odds_map.get)
            return fav_selection, odds_map[fav_selection]
        else:
            # RANDOM
            rng = random.Random(seed) if seed is not None else random.Random()
            sel = rng.choice(["HOME", "DRAW", "AWAY"])
            return sel, market_1x2.get(sel, 2.0)

    def place_match_wager(self, match_id: str, market_1x2: Dict[str, float], stake_fraction: float = 0.05, seed: Optional[int] = None) -> bool:
        """Places a wager of fixed percentage of available cash."""
        if match_id in self.active_wagers:
            return False
        
        stake = round(max(10.0, self.portfolio.cash_balance * stake_fraction), 2)
        if stake > self.portfolio.cash_balance:
            if self.portfolio.cash_balance >= 10.0:
                stake = self.portfolio.cash_balance
            else:
                # Bot went bankrupt, refill
                self.portfolio.deposit_refill(1000.0)
                stake = round(self.portfolio.cash_balance * stake_fraction, 2)

        selection, odds = self.pick_selection(market_1x2, seed)
        placed = self.portfolio.place_wager(stake)
        if placed:
            self.active_wagers[match_id] = (selection, stake, odds)
        return placed

    def settle_match(self, match_id: str, outcome_1x2: str):
        """Settles match outcome and updates bot NAV."""
        if match_id not in self.active_wagers:
            return
        
        selection, stake, odds = self.active_wagers.pop(match_id)
        if selection == outcome_1x2:
            payout = round(stake * odds, 2)
        else:
            payout = 0.0
        
        self.portfolio.settle_wager(stake=stake, payout=payout)

class BenchmarkManager:
    """Manages the 3 systematic baseline strategies (Random Walk, Favorite Heavy, Home Bias)."""

    def __init__(self):
        self.random_bot = BenchmarkBot(name="Random Walk Index", strategy_type="RANDOM")
        self.favorite_bot = BenchmarkBot(name="Favorite-Heavy Index", strategy_type="FAVORITE")
        self.home_bot = BenchmarkBot(name="Home-Advantage Index", strategy_type="HOME_BIAS")
        self.history: List[Dict[str, Any]] = [
            {
                "step": 0,
                "random_walk": 100.0,
                "favorite_heavy": 100.0,
                "home_advantage": 100.0
            }
        ]

    def on_match_scheduled(self, match_id: str, market_1x2: Dict[str, float], seed: Optional[int] = None):
        """Bots place wagers when a match is scheduled or simulated."""
        self.random_bot.place_match_wager(match_id, market_1x2, seed=seed)
        self.favorite_bot.place_match_wager(match_id, market_1x2, seed=seed)
        self.home_bot.place_match_wager(match_id, market_1x2, seed=seed)

    def on_match_settled(self, match_id: str, outcome_1x2: str):
        """Bots settle wagers and update their NAV curves."""
        self.random_bot.settle_match(match_id, outcome_1x2)
        self.favorite_bot.settle_match(match_id, outcome_1x2)
        self.home_bot.settle_match(match_id, outcome_1x2)

        self.history.append({
            "step": len(self.history),
            "match_id": match_id,
            "random_walk": round(self.random_bot.portfolio.nav, 2),
            "favorite_heavy": round(self.favorite_bot.portfolio.nav, 2),
            "home_advantage": round(self.home_bot.portfolio.nav, 2)
        })

    def process_match(self, match_id: str, market_1x2: Dict[str, float], outcome_1x2: str, seed: Optional[int] = None, db = None):
        """Simulates full bot lifecycle (placement + settlement) on a completed match."""
        self.on_match_scheduled(match_id, market_1x2, seed=seed)
        self.on_match_settled(match_id, outcome_1x2)

        if db is not None:
            try:
                from src.backend.models.database import BenchmarkNAVHistoryModel
                rec = BenchmarkNAVHistoryModel(
                    match_id=match_id,
                    random_walk_nav=self.random_bot.portfolio.nav,
                    favorite_heavy_nav=self.favorite_bot.portfolio.nav,
                    home_advantage_nav=self.home_bot.portfolio.nav,
                    step_index=len(self.history) - 1
                )
                db.add(rec)
            except Exception as e:
                pass

    def get_benchmarks_summary(self, player_nav: float) -> Dict[str, Any]:
        """Returns actual live bot NAVs compared to the player."""
        return {
            "player_nav": round(player_nav, 2),
            "random_walk_index": round(self.random_bot.portfolio.nav, 2),
            "favorite_heavy_index": round(self.favorite_bot.portfolio.nav, 2),
            "home_advantage_index": round(self.home_bot.portfolio.nav, 2),
            "history": self.history[-50:],
            "twr": {
                "player": round(((player_nav / 100.0) - 1.0) * 100.0, 2),
                "random_walk": self.random_bot.portfolio.calculate_twr(),
                "favorite_heavy": self.favorite_bot.portfolio.calculate_twr(),
                "home_advantage": self.home_bot.portfolio.calculate_twr()
            }
        }
