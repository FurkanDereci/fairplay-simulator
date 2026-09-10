from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Any

@dataclass
class TransactionRecord:
    timestamp: str
    tx_type: str  # 'INITIAL_DEPOSIT', 'REFILL_DEPOSIT', 'BET_STAKE', 'BET_PAYOUT'
    amount: float
    cash_after: float
    nav_after: float
    units_after: float

class NAVPortfolioEngine:
    """GIPS-compliant Unit NAV Fund Accounting Engine for Virtual Betting Portfolios."""
    
    def __init__(self, initial_balance: float = 1000.0, base_nav: float = 100.0):
        self.base_nav: float = base_nav
        self.cash_balance: float = initial_balance
        self.locked_stakes: float = 0.0
        self.nav: float = base_nav
        self.total_units: float = initial_balance / base_nav if base_nav > 0 else 0.0
        self.series_id: int = 1
        # Completed series' growth factors, multiplied together (GIPS cross-series TWR).
        self.series_growth: float = 1.0
        self._series_closed: bool = False
        self.transactions: List[TransactionRecord] = []
        self.nav_history: List[Dict[str, Any]] = []
        
        self._record_transaction("INITIAL_DEPOSIT", initial_balance)

    @property
    def total_portfolio_value(self) -> float:
        return self.cash_balance + self.locked_stakes

    def _update_nav(self):
        if self.total_units > 0:
            self.nav = self.total_portfolio_value / self.total_units
        else:
            self.nav = 0.0
        
        self.nav_history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "nav": round(self.nav, 4),
            "cash": round(self.cash_balance, 2),
            "locked_stakes": round(self.locked_stakes, 2),
            "total_value": round(self.total_portfolio_value, 2),
            "units": round(self.total_units, 4)
        })

    def _record_transaction(self, tx_type: str, amount: float):
        self._update_nav()
        self.transactions.append(TransactionRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            tx_type=tx_type,
            amount=amount,
            cash_after=round(self.cash_balance, 2),
            nav_after=round(self.nav, 4),
            units_after=round(self.total_units, 4)
        ))

    def _close_series(self) -> None:
        """Records the current series' final growth factor when the fund is wiped out."""
        if self._series_closed:
            return
        factor = (self.nav / self.base_nav) if self.base_nav > 0 else 0.0
        self.series_growth *= factor
        self._series_closed = True

    def deposit_refill(self, amount: float) -> bool:
        """Processes virtual balance refill without altering current NAV performance."""
        if amount <= 0:
            return False
        if self.total_portfolio_value <= 0 or self.total_units <= 0:
            # Re-unitization after complete bankruptcy
            self._close_series()
            self.series_id += 1
            self.cash_balance = amount
            self.locked_stakes = 0.0
            self.nav = self.base_nav
            self.total_units = amount / self.base_nav
            self._series_closed = False
        else:
            # Issue new units at current NAV
            new_units = amount / self.nav
            self.total_units += new_units
            self.cash_balance += amount
            
        self._record_transaction("REFILL_DEPOSIT", amount)
        return True

    def place_wager(self, stake: float) -> bool:
        if stake > self.cash_balance or stake <= 0:
            return False
        self.cash_balance -= stake
        self.locked_stakes += stake
        self._record_transaction("BET_STAKE", -stake)
        return True

    def settle_wager(self, stake: float, payout: float) -> bool:
        if stake <= 0 or payout < 0 or stake > self.locked_stakes:
            return False
        self.locked_stakes -= stake
        self.cash_balance += payout
        self._record_transaction("BET_PAYOUT", payout - stake)
        if self.total_portfolio_value <= 0:
            self._close_series()
        return True

    def calculate_twr(self) -> float:
        """Time-Weighted Return %, compounded across series (GIPS).

        A wiped-out series is closed at its final growth factor, so a bankruptcy stays on the
        record instead of being reset by the next refill's re-unitization.
        """
        if self.base_nav <= 0:
            return 0.0
        growth = self.series_growth * (self.nav / self.base_nav)
        return round((growth - 1.0) * 100.0, 2)
