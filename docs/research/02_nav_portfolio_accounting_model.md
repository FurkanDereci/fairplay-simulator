# Mathematical and Algorithmic Specification: Betting Portfolio NAV & Performance Accounting

## 1. Problem Statement & Need for Unitization
In a gamified virtual betting platform where bankrupt users receive balance recharges/refills, simply tracking the raw bankroll balance creates severe mathematical distortions:
- **Refill Distortion**: A user who loses 1,000 TL, gets a 1,000 TL refill, and wins 100 TL shows a cash balance of 1,100 TL (+10% naive return), despite having lost 900 TL of net virtual capital.
- **Scale Asymmetry**: Recharges distort total return metrics, making unskilled players who bankrupt frequently look artificially profitable.

To evaluate genuine betting skill independently of capital additions/refills, the platform applies **GIPS-compliant Mutual Fund Unitized Accounting (Unit NAV)**.

---

## 2. Mathematical Formulation of Unitized Betting Accounting

### 2.1 Core State Variables
At any timestamp $t$:
- $C_t$: Cash Balance (available virtual capital for betting).
- $E_t$: Market Exposure Value (current value or stake of active unsettled bets).
- $V_t$: Total Portfolio Value ($V_t = C_t + E_t$).
- $U_t$: Total Outstanding Units.
- $\text{NAV}_t$: Net Asset Value per unit ($\text{NAV}_t = V_t / U_t$).

Initially, at $t = 0$:
- Initial Cash Deposit $D_0 = 1000.00$ TL.
- Initial NAV $\text{NAV}_0 = 100.00$.
- Initial Units $U_0 = D_0 / \text{NAV}_0 = 10.0000$ units.

### 2.2 Processing Cash Inflows (Refills/Top-Ups)
When a user receives a refill or top-up of amount $D_t$ at timestamp $t$:
1. Value before inflow: $V_{t^-} = C_{t^-} + E_{t^-}$.
2. NAV before inflow: $\text{NAV}_{t^-} = V_{t^-} / U_{t^-}$.
3. New Units Issued: $\Delta U_t = D_t / \text{NAV}_{t^-}$.
4. Updated Total Units: $U_t = U_{t^-} + \Delta U_t$.
5. Updated Cash Balance: $C_t = C_{t^-} + D_t$.
6. Updated Portfolio Value: $V_t = V_{t^-} + D_t$.
7. **Crucial Invariant**: $\text{NAV}_t = \frac{V_t}{U_t} = \frac{V_{t^-} + D_t}{U_{t^-} + (D_t / \text{NAV}_{t^-})} = \text{NAV}_{t^-}$.
   - Capital inflows change the unit count $U_t$, but **leave $\text{NAV}_t$ completely unchanged**.

### 2.3 Handling Bankruptcy ($V_t = 0$) and Series Re-unitization
When $V_t = 0$ (complete insolvency):
- $\text{NAV}_t$ drops to $0.00$.
- When a new refill $D_{\text{refill}}$ is issued, a new unit series is initiated to avoid division-by-zero:
  - Reset Base NAV: $\text{NAV}_{\text{new\_series}} = 100.00$.
  - New Units Issued: $U_{\text{new\_series}} = D_{\text{refill}} / 100.00$.
  - Cumulative Time-Weighted Return (TWR) compounds across series intervals:
    $$\text{TWR}_{\text{total}} = \left( \prod_{s=1}^{S} (1 + R_s) \right) - 1$$

---

## 3. Performance Metrics Suite

### 3.1 Time-Weighted Return (TWR)
TWR measures the compound rate of growth in a portfolio, eliminating the distorting effects of cash inflows/refills:
$$\text{TWR}_T = \frac{\text{NAV}_T}{\text{NAV}_0} - 1$$

### 3.2 Maximum Drawdown (MDD)
Tracks peak-to-trough decline in unit NAV:
$$\text{MDD} = \max_{\tau \le t} \left( \frac{\text{NAV}_{\text{peak}, \tau} - \text{NAV}_t}{\text{NAV}_{\text{peak}, \tau}} \right)$$

### 3.3 Yield / ROI per Market Type
For any market type $m$ (e.g., 1X2, Over/Under):
$$\text{Yield}_m = \frac{\sum \text{Payout}_m - \sum \text{Stake}_m}{\sum \text{Stake}_m} \times 100\%$$

### 3.4 Sharpe & Sortino Ratios for Betting
$$\text{Sharpe} = \frac{\bar{R}_{\text{bet}} - R_f}{\sigma_{\text{bet}}}, \quad \text{Sortino} = \frac{\bar{R}_{\text{bet}} - R_f}{\sigma_{\text{downside}}}$$

---

## 4. Python NAV Engine Implementation

```python
from dataclasses import dataclass, field
from typing import List
import datetime

@dataclass
class Transaction:
    timestamp: datetime.datetime
    tx_type: str # 'DEPOSIT', 'WITHDRAWAL', 'BET_STAKE', 'BET_PAYOUT'
    amount: float
    nav_after: float
    units_after: float

class UnitizedBettingPortfolio:
    def __init__(self, initial_deposit: float = 1000.0, initial_nav: float = 100.0):
        self.cash: float = initial_deposit
        self.locked_exposure: float = 0.0
        self.nav: float = initial_nav
        self.units: float = initial_deposit / initial_nav
        self.series_id: int = 1
        self.transactions: List[Transaction] = []
        
        self._record_tx('INITIAL_DEPOSIT', initial_deposit)

    @property
    def total_value(self) -> float:
        return self.cash + self.locked_exposure

    def _update_nav(self):
        if self.units > 0:
            self.nav = self.total_value / self.units

    def _record_tx(self, tx_type: str, amount: float):
        self.transactions.append(
            Transaction(
                timestamp=datetime.datetime.now(datetime.timezone.utc),
                tx_type=tx_type,
                amount=amount,
                nav_after=self.nav,
                units_after=self.units
            )
        )

    def deposit_refill(self, amount: float):
        """Refills virtual balance without affecting NAV."""
        if self.total_value == 0:
            # Re-unitization after insolvency
            self.series_id += 1
            self.cash = amount
            self.nav = 100.0
            self.units = amount / 100.0
        else:
            new_units = amount / self.nav
            self.units += new_units
            self.cash += amount
        self._update_nav()
        self._record_tx('REFILL_DEPOSIT', amount)

    def place_bet(self, stake: float) -> bool:
        if stake > self.cash:
            return False
        self.cash -= stake
        self.locked_exposure += stake
        self._update_nav()
        self._record_tx('BET_STAKE', -stake)
        return True

    def settle_bet(self, stake: float, payout: float):
        self.locked_exposure -= stake
        self.cash += payout
        self._update_nav()
        self._record_tx('BET_SETTLEMENT', payout - stake)
