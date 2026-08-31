# Architecture Document: System Architecture & Database Schema

## 1. System Topology & Microservices

```
                       +------------------------+
                       |   Client Layer (Web)   |
                       +-----------+------------+
                                   | REST / WSS
                                   v
                       +------------------------+
                       |   FastAPI Gateway      |
                       +----+--------------+----+
                            |              |
           +----------------+              +----------------+
           |                                                |
           v                                                v
+-----------------------+                        +-----------------------+
| Core Application      |                        | Real-Time Odds        |
| Microservices         |                        | Broadcaster (Pub/Sub) |
+-----------+-----------+                        +-----------+-----------+
            |                                                |
            v                                                v
+------------------------------------------------------------------------+
| Data Storage Tier                                                      |
| - PostgreSQL 16 + TimescaleDB (Users, Bets, Matches, NAV, Snapshots)   |
| - Redis Cluster (Odds Cache, Sessions, Rate Limits, Pub/Sub)           |
+------------------------------------------------------------------------+
```

---

## 2. Relational Database DDL Schema (PostgreSQL 16)

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TYPE user_status_enum AS ENUM ('ACTIVE', 'COOLDOWN_LOCKED', 'SUSPENDED');
CREATE TYPE bet_status_enum AS ENUM ('PENDING', 'WON', 'LOST', 'VOID', 'CANCELLED');
CREATE TYPE match_status_enum AS ENUM ('SCHEDULED', 'IN_PLAY', 'FINISHED', 'POSTPONED', 'CANCELLED');

-- 1. Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    status user_status_enum NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. User Balances
CREATE TABLE user_balances (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    available_balance NUMERIC(12, 4) NOT NULL DEFAULT 1000.0000 CHECK (available_balance >= 0),
    locked_balance NUMERIC(12, 4) NOT NULL DEFAULT 0.0000 CHECK (locked_balance >= 0),
    simulation_energy INT NOT NULL DEFAULT 100 CHECK (simulation_energy BETWEEN 0 AND 100),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Cooldown States
CREATE TABLE cooldown_states (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    current_tier INT NOT NULL DEFAULT 0 CHECK (current_tier >= 0),
    consecutive_solvent_days INT NOT NULL DEFAULT 0 CHECK (consecutive_solvent_days >= 0),
    cooldown_expires_at TIMESTAMP WITH TIME ZONE
);

-- 4. Matches & Odds Snapshots
CREATE TABLE matches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_provider_id VARCHAR(100) UNIQUE NOT NULL,
    home_team VARCHAR(100) NOT NULL,
    away_team VARCHAR(100) NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    status match_status_enum NOT NULL DEFAULT 'SCHEDULED'
);

CREATE TABLE odds_snapshots (
    id BIGSERIAL PRIMARY KEY,
    match_id UUID NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    market_type VARCHAR(50) NOT NULL,
    odds_data JSONB NOT NULL,
    overround NUMERIC(6, 4) NOT NULL,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Bets & Bet Legs
CREATE TABLE bets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    stake NUMERIC(12, 4) NOT NULL CHECK (stake > 0),
    total_odds NUMERIC(8, 4) NOT NULL CHECK (total_odds >= 1.0),
    potential_payout NUMERIC(12, 4) NOT NULL,
    status bet_status_enum NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. NAV History
CREATE TABLE nav_history (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    net_asset_value NUMERIC(12, 4) NOT NULL,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```
