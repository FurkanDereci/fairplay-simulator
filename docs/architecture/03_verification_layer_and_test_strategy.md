# Architecture Document: Verification Layer & Automated Test Strategy

## 1. Verification Layer Invariants

To guarantee platform integrity and prevent financial or state bugs, the system enforces four core invariant suites:

### Invariant Suite 1: Cooldown Lockout Verification
- **Rule**: If `status == 'COOLDOWN_LOCKED'` or `NOW() < cooldown_expires_at`, bet creation MUST be rejected with HTTP 423.
- **Test Condition**: Simulate bankruptcy -> attempt bet -> assert rejection. Advance time past `cooldown_expires_at` -> assert bet creation allowed.

### Invariant Suite 2: NAV & Balance Conservation
- **Rule**: For all users, $NAV_t \times U_t = \text{Cash}_t + \text{Exposure}_t$.
- **Test Condition**: Run multi-user deposit, bet placement, settlement, and refill sequences. Assert total value balance conservation at every step.

### Invariant Suite 3: Odds Sanitation & Vig Extraction
- **Rule**: Implied probabilities $\sum (1/o_i)$ must strictly exceed $1.00$ (overround $O > 0$).
- **Test Condition**: Validate incoming odds JSON feeds. Reject negative vig or corrupted odds arrays.

### Invariant Suite 4: Bet Settlement Idempotency
- **Rule**: Processing a match finalization event multiple times MUST result in exactly 1 payout transaction.
- **Test Condition**: Send duplicate settlement payloads for the same bet leg. Assert transaction log has exactly 1 entry.

---

## 2. Automated Test Suite Scripts

The platform ships an automated test suite run with Python's built-in `unittest` (no extra
runner required):

```bash
python -m unittest discover tests
```

| Test file | Covers |
| --------- | ------ |
| `tests/test_backend_core.py` | NAV engine (refill invariance, cross-series TWR, bankruptcy) and cooldown invariants (backoff, tier decay) |
| `tests/test_data_ingestion.py` | Odds normalization and vig extraction (`OddsNormalizer`, `MockDataGenerator`) |
| `tests/test_database_models.py` | SQLAlchemy models, relations and cascade deletes |
| `tests/test_match_engine.py` | Poisson lambda derivation, deterministic simulation, Monte Carlo, settle flow |
| `tests/test_benchmark_engine.py` | Benchmark bot strategies and NAV evolution |
| `tests/test_risk_engine.py` | Sharpe, Sortino, MDD, beta/alpha, trade analytics |
| `tests/test_agent_router.py` | Multi-agent routing, gatekeeper loop, deadlock breaker |
| `tests/test_api_endpoints.py` | API surface, auth guards, energy depletion gate |
| `tests/test_full_architecture.py` | End-to-end register/login/wager/settle/bankruptcy flow |
| `tests/verify_simulator_math.py` | Standalone math checks (backoff curve, overround) |

This table is the authoritative list. Earlier revisions referenced `tests/test_nav_engine.py`,
`tests/test_cooldown_engine.py` and `tests/test_odds_vig.py` — those files were never created;
their coverage lives in the files above.
