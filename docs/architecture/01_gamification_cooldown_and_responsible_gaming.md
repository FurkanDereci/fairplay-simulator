# Architecture Document: Gamification, Cooldown & Mathematical Risk Features

## 1. Kelly Criterion & Risk of Ruin Mechanics

### 1.1 Kelly Criterion Optimal Stake Calculation
Given user-estimated or benchmark true probability $p \in (0, 1)$ and offered decimal odds $o > 1.0$:
$$f^* = \frac{p \cdot o - 1}{o - 1}$$
Where $f^*$ represents the optimal percentage of available cash balance to stake.

### 1.2 Risk of Ruin Threshold
If a user attempts to stake $W > 0.15 \times C_{\text{available}}$, the system calculates the Risk of Ruin $R_{\text{ruin}}$:
$$R_{\text{ruin}} = \left( \frac{1 - \text{Edge}}{1 + \text{Edge}} \right)^{\text{Units}}$$
Displays an explicit warning modal requiring user confirmation before proceeding.

---

## 2. Closing Line Value (CLV) Calculation
$$\text{CLV} = \left( \frac{o_{\text{placed}}}{o_{\text{closing}}} - 1 \right) \times 100\%$$
- Positive CLV ($> 0\%$) proves market-beating entry timing.

---

## 3. Cooldown & Tier Decay System
$$T(n) = \min\left(168, \; 1.0 \times 4^{n-1}\right) \text{ hours}$$
- Tier Decay: 3 active solvent days reduce effective tier $n$ by 1.
- Discipline Discount: Earning 3+ Discipline Badges reduces max $T(n)$ cap from 168 hours to 72 hours.
