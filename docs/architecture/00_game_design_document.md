# Game Design Document (GDD): FairPlay - Gamified Football Simulation Platform

## 1. Executive Summary & Core Game Vision
- **Project Name**: FairPlay Simulator
- **Primary Game Mode (MVP)**: Single-Player Strategic Analytics & Solvency Survival
- **Core Vision**: Non-gambling, educational football simulation combining sports betting odds with mutual fund portfolio accounting (Unit NAV), risk management, and mathematical probability tools.

---

## 2. Core Game Loop & Single-Player Experience (MVP)

```
+-------------------------------------------------------------------+
|                     SINGLE-PLAYER CORE GAME LOOP                  |
+-------------------------------------------------------------------+
| 1. Explore Fixtures & Live Betting Markets                        |
| 2. Analyze Vig / Overround Gauge, Kelly Criterion & EV            |
| 3. Check Ruin Risk Warning if Stake > 15% Bankroll                |
| 4. Wager Execution -> Energy Depletion (10 Energy / Bet)          |
| 5. Match Settlement -> Unit NAV, CLV & Benchmark Index Comparison |
| 6. Performance Evaluation -> TWR, Drawdown & Discipline Badges    |
| 7. Solvency Sustained -> Tier Decay / Cooldown Discount Unlocks   |
|    OR Bankruptcy -> Exponential Backoff Cooldown Lockout          |
+-------------------------------------------------------------------+
```

---

## 3. Detailed Game Rules & Mechanics

### Rule 1: Kelly Criterion & Risk of Ruin Assistant
- **Formula**: Calculates optimal stake fraction $f^* = \frac{p \cdot o - 1}{o - 1}$.
- **Bankroll Safeguard**: Any single wager exceeding $15\%$ of total bankroll triggers a mandatory "High Ruin Risk Warning" modal explaining the probability of eventual insolvency under over-leveraged betting.

### Rule 2: Closing Line Value (CLV) Tracking
- **Market Beat Metric**: Measures placed odds ($o_{\text{placed}}$) vs final pre-kickoff closing odds ($o_{\text{closing}}$):
  $$\text{CLV}_{\text{pct}} = \left( \frac{o_{\text{placed}}}{o_{\text{closing}}} - 1 \right) \times 100\%$$
- **$+CLV$ Achievement**: A positive CLV indicates the user consistently identifies mispriced odds before the broader market adjusts, independent of match outcome variance.

### Rule 3: Single-Player Benchmarking vs Market Indices
The user's Unit NAV equity curve is continuously benchmarked against 3 automated baseline strategies:
1. **Random Walk Index**: Simulates equal-stake random selections across the same matches.
2. **Favorite-Heavy Index**: Simulates betting solely on match favorites ($o < 1.60$).
3. **Home-Advantage Index**: Simulates betting strictly on home win selections.
- Demonstrates whether the user's selection skill beats random guessing and bookmaker overround.

### Rule 4: Discipline Badges & Cooldown Cap Discounts
- Earned through financial discipline rather than short-term luck:
  - *"Positive EV Hunter"*: 10 wagers placed with $EV > 0$.
  - *"Bankroll Guardian"*: 14 consecutive solvent days with $RAS < 30$.
  - *"CLV Master"*: 15 wagers placed with $+CLV > 0\%$.
- **Mechanical Reward**: Earning discipline badges permanently reduces the maximum bankruptcy cooldown cap (e.g. 7-day cap reduced to 3 days) and accelerates tier decay speed.

### Rule 5 (Phase 2 - Deferred): Virtual Copy Fund / Social League
- **Status**: Architecture prepared; disabled in MVP single-player mode.
- **Future Mechanics**: Allows top-performing users ($NAV > 120.0$, $RAS < 25$) to publish their portfolio as a virtual fund for other players to track without real money.

---

## 4. Anti-Addiction & Cooldown Mechanics
- **Exponential Backoff**: $T(n) = \min\left(168, \; 1.0 \times 4^{n-1}\right)$ hours upon insolvency ($V_t < B_{\text{min}}$).
- **Tier Decay**: 3 active solvent days reduce effective bankruptcy tier by 1.
- **Overround Gauge**: Real-time display of bookmaker margin $M = \frac{O}{1+O} \times 100\%$.
