# Research Report: Football Odds and Fixtures APIs for Virtual Betting Simulator

## 1. Executive Summary & Architectural Requirements
Building a realistic, non-gambling football betting simulator requires two core data engines:
1. **Fixture & Telemetry Engine**: Schedules, team info, live match status, live scores, and settlement events (goals, red cards, final whistle).
2. **Market & Odds Engine**: Pre-match and live odds across key markets (1X2 / Match Winner, Over/Under, Both Teams to Score, Asian Handicap).

To avoid single-point-of-failure and rate-limit constraints, a decoupled dual-provider architecture or a unified sports API is required.

---

## 2. API Provider Evaluation

### 2.1 The Odds API (odds-api.com)
- **Primary Strength**: Dedicated betting odds aggregation across 30+ global bookmakers (Pinnacle, Bet365, Unibet, 1xBet, etc.).
- **Free Tier Quota**: 500 requests / month.
- **Leagues Covered**: All major European leagues (Premier League, La Liga, Serie A, Bundesliga, Ligue 1, UEFA Champions League, Turkish Süper Lig).
- **Markets Supported**:
  - `h2h` (Match Winner 1X2)
  - `spreads` (Asian Handicap / Point Spreads)
  - `totals` (Over/Under Goals)
  - `btts` (Both Teams to Score)
  - `draw_no_bet` & `double_chance`
- **Odds Update Frequency**: Pre-match refreshed every 5-15 mins; live odds stream available.
- **Pros**: Cleanest normalized odds schema; easy calculation of bookmaker vig/overround.
- **Cons**: Strict request quota on free tier (requires smart caching).

### 2.2 API-Football / API-Sports (api-sports.io)
- **Primary Strength**: Complete all-in-one football telemetry and odds feed.
- **Free Tier Quota**: 100 requests / day (3,000 / month).
- **Leagues Covered**: 1,000+ leagues globally including lower divisions and cups.
- **Markets Supported**: Pre-match odds (`/odds`), live odds (`/odds/live`), fixture status, match statistics, lineups.
- **Pros**: Single SDK for both match fixtures/scores and betting odds; no need for cross-provider entity matching.
- **Cons**: Free plan excludes live odds endpoint (pre-match odds available). Entry plan ($19/mo) grants 7,500 req/day.

### 2.3 Football-Data.org
- **Primary Strength**: Generous free tier for fixture schedules, standings, and results.
- **Free Tier Quota**: 10 requests / minute (no monthly cap).
- **Leagues Covered**: 12 top competitions (PL, La Liga, Serie A, Bundesliga, Ligue 1, Eredivisie, Primeira Liga, Champions League, World Cup, Euros).
- **Pros**: High rate-limit per minute; ideal for baseline match schedule polling.
- **Cons**: Very limited odds coverage on free tier.

---

## 3. Comparison Matrix

| Provider | Free Quota | Fixture Data | Odds Data | Live Scores | Verdict for Simulator |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **The Odds API** | 500 req/mo | Basic | **Excellent** | No | Best dedicated odds feed |
| **API-Football** | 100 req/day | **Excellent** | **Good** | **Excellent** | Best unified all-in-one feed |
| **Football-Data.org** | 10 req/min | **Good** | Minimal | Basic | Best free fixture scheduler |

---

## 4. Recommended Ingestion Strategy

```
+-------------------------------------------------------------------+
|                     DATA INGESTION LAYER                          |
+---------------------------------+---------------------------------+
                                  |
    [Football-Data.org API]       |       [The Odds API]
    (Fixtures, Standings, Scores) |       (1X2, O/U, BTTS Odds)
                  |               |                 |
                  +-------+-------+                 |
                          |                         |
                          v                         v
           +-----------------------------------------------+
           |   Redis Odds & Fixtures Cache (TTL: 5-15m)   |
           +----------------------+------------------------+
                                  |
                                  v
           +-----------------------------------------------+
           |   TimescaleDB Time-Series Storage             |
           +-----------------------------------------------+
```

1. **Bootstrapped / Zero-Cost Stack**:
   - Use **Football-Data.org** (10 req/min) for match fixture calendars and results.
   - Use **The Odds API** (500 req/mo) for odds snapshots cached in Redis with dynamic TTLs (15 min for matchday -3, 5 min for matchday -1, 1 min near kickoff).
2. **Production Unified Stack**:
   - Upgrade to **API-Football** ($19/mo) for single-source live score updates, match events, and pre-match odds without complex ID mapping between separate providers.
