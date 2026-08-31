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
        self.cash_balance: float = initial_balance
        self.locked_stakes: float = 0.0
        self.nav: float = base_nav
        self.total_units: float = initial_balance / base_nav
        self.series_id: int = 1
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

    def deposit_refill(self, amount: float):
        """Processes virtual balance refill without altering current NAV performance."""
        if self.total_portfolio_value <= 0:
            # Re-unitization after complete bankruptcy
            self.series_id += 1
            self.cash_balance = amount
            self.locked_stakes = 0.0
            self.nav = 100.0
            self.total_units = amount / 100.0
        else:
            # Issue new units at current NAV
            new_units = amount / self.nav
            self.total_units += new_units
            self.cash_balance += amount
            
        self._record_transaction("REFILL_DEPOSIT", amount)

    def place_wager(self, stake: float) -> bool:
        if stake > self.cash_balance or stake <= 0:
            return False
        self.cash_balance -= stake
        self.locked_stakes += stake
        self._record_transaction("BET_STAKE", -stake)
        return True

    def settle_wager(self, stake: float, payout: float):
        self.locked_stakes -= stake
        self.cash_balance += payout
        self._record_transaction("BET_PAYOUT", payout - stake)

    def calculate_twr() -> float:
        """Time-Weighted Return % relative to baseline NAV 100.0."""
        return round(((self.nav / 100.0) - 1.0) * 100.0, 2)
