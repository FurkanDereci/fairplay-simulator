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

The platform includes Python automated test scripts (`tests/test_nav_engine.py`, `tests/test_cooldown_engine.py`, `tests/test_odds_vig.py`) to verify calculations automatically during CI/CD or agentic execution.
